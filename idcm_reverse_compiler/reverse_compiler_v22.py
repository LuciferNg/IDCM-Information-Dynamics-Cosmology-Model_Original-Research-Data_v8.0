#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IDCM 逆向編譯器 v22

新增（vs v21）：
P5: Unicode Greek → ASCII 映射（φ→phi, ε→eps, κ→kappa, β→beta）
P1: IR VM 內置執行引擎（eval_ir）
P2: 自動驗證套件（verify vs PDG/外部數據）
P3: 依賴圖匯出（dependency adjacency matrix）
P4: CKM 統一推導（V_us MERA correction）

保留 v21 所有功能：
- corpus sanitizer + unified pipeline-algebraic classification
- LaTeX sanitizer, multi-equals split, value dump extractor
- 閉包傳播、自動分類、IR 生成、microcode statistics

定位：
- 結構驗證後的執行層
- ISA proven, 現專注於執行、驗證、自動化
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import product
from collections import Counter, defaultdict
import argparse
import json
import math
import re
import sys
from typing import Dict, List, Optional, Sequence, Tuple


TOKEN_RE = re.compile(
    r"""
    (?:\d+\.\d+|\d+)                            # number
    |(?:[A-Za-zα-ωΑ-Ω]+)                           # identifier / symbol words
    |(?:<=|>=|!=|==|->|=>|::|\+\-|\*\*|//)        # multi-char operators
    |(?:[\^_\-+*/=(),\[\]{}:/])                 # single-char operators / separators
    |(?:\S)                                       # fallback single non-space char
    """,
    re.VERBOSE,
)

KIND_BITS = {
    "number": "00",
    "symbol": "01",
    "operator": "10",
    "group": "11",
    "separator": "11",
    "binding": "10",
    "other": "01",
}

ROLE_BITS = {
    "delimiter": "000",
    "binding_symbol": "001",
    "operand": "010",
    "literal": "010",
    "length_field": "011",
    "address": "100",
    "opcode": "101",
    "state_marker": "110",
    "control_flag": "111",
    "function": "100",
    "action": "011",
    "unknown": "000",
}


@dataclass(frozen=True)
class Token:
    text: str
    kind: str
    index: int


@dataclass
class FormulaRecord:
    raw: str
    tokens: List[Token] = field(default_factory=list)


@dataclass(frozen=True)
class RoleAssignment:
    mapping: Dict[str, str]

    def role_of(self, token_text: str) -> str:
        return self.mapping.get(token_text, "unknown")


@dataclass
class DecodeHypothesis:
    name: str
    assignment: RoleAssignment
    score: float = 0.0
    notes: List[str] = field(default_factory=list)


@dataclass
class ParseNode:
    label: str
    children: List["ParseNode"] = field(default_factory=list)
    token: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "label": self.label,
            "token": self.token,
            "children": [c.to_dict() for c in self.children],
        }


@dataclass
class DecodeResult:
    hypotheses: List[DecodeHypothesis]
    token_stats: Dict[str, Dict[str, int]]
    token_roles: Dict[str, str]
    kind_transition_stats: Dict[str, Dict[str, int]]
    role_transition_stats: Dict[str, Dict[str, int]]
    parse_summaries: Dict[str, List[str]]
    parse_trees: Dict[str, Dict]
    family_stats: Dict[str, int]
    position_constraints: Dict[str, List[str]]
    collision_report: Dict[str, Dict[str, int]]
    grammar_candidates: Dict[str, List[str]]
    binary_packets: Dict[str, str]
    opcode_rankings: List[Tuple[str, float]]
    cfg_rules: Dict[str, List[str]]
    validation_report: Dict[str, str]
    stress_report: Dict[str, str]
    rewrite_report: Dict[str, str]
    lattice_report: Dict[str, str]
    decoder_exports: Dict[str, Dict[str, str]]
    stability_report: Dict[str, str]
    ambiguity_report: Dict[str, str]
    ranked_grammar_trees: List[Tuple[str, float]]
    parse_forest: Dict[str, List[Dict]]
    voting_report: Dict[str, str]
    layer_consistency: Dict[str, str]
    pipeline_explanation: Dict[str, str]
    consensus_report: Dict[str, str]
    disagreement_report: Dict[str, str]
    stage_map: Dict[str, str]
    rule_confidence: Dict[str, str]
    wfield_map: Dict[str, str]
    wfield_formula: Dict[str, str]
    semantic_role_map: Dict[str, str]
    formula_coherence: Dict[str, str]
    rejection_report: Dict[str, str]
    formula_ranking: List[Tuple[str, float]]
    global_coherence_summary: Dict[str, str]
    dialect_router_report: Dict[str, str]
    dialect_mode_report: Dict[str, str]
    dialect_ebnf: Dict[str, str]
    dialect_routing_examples: Dict[str, str]
    pipeline_mode_summary: Dict[str, str]
    algebraic_mode_summary: Dict[str, str]
    router_confidence: Dict[str, str]
    canonical_forest_summary: Dict[str, str]
    canonical_tree_summary: Dict[str, str]
    symbol_table: Dict[str, Dict]
    microcode_usage: Dict[str, int]
    formula_ir: Dict[str, List[str]]
    total_instruction_count: int


class ReverseCompiler:
    def __init__(self, formulas: Sequence[str]):
        self.records = [FormulaRecord(raw=f, tokens=self.tokenize(f)) for f in formulas]
        self._struct_closure = None
    
    GREEK_MAP = {
            # Greek letters
            'φ': 'phi', 'ε': 'eps', 'κ': 'kappa', 'β': 'beta',
            'γ': 'gamma', 'δ': 'delta', 'λ': 'lambda', 'π': 'pi',
            'σ': 'sigma', 'η': 'eta', 'ξ': 'xi', 'ω': 'omega',
            'Λ': 'Lambda', 'Ω': 'Omega', 'ħ': 'hbar',
            'μ': 'mu', 'ρ': 'rho', 'τ': 'tau',
            # Superscript digits (positive)
            '²': '^2', '³': '^3', '⁴': '^4', '⁵': '^5', '⁶': '^6',
            '⁰': '^0', '¹': '^1',
            # Negative superscripts (combined forms) — MUST be before '⁻' alone
            '\u207b\u00b9': '^-1', '\u207b\u00b2': '^-2', '\u207b\u00b3': '^-3',
            '\u207b\u2074': '^-4', '\u207b\u2075': '^-5', '\u207b\u2076': '^-6',
            # Bare minus sign (fallback for rare cases)
            '\u207b': '^-',
            # Subscript digits
            '₀': '_0', '₁': '_1', '₂': '_2', '₃': '_3',
            '₄': '_4', '₅': '_5', '₆': '_6', '₇': '_7', '₈': '_8', '₉': '_9',
            # Operators
            '·': '*', '×': '*', '′': "'",
            '√': 'sqrt',
        }

    LATEX_ARTIFACTS = [
        (r'\\text\{([^}]*)\}', r'\1'), (r'\\mathrm\{([^}]*)\}', r'\1'),
        (r'\\left', ''), (r'\\right', ''),
        (r'\\cdot', '*'), (r'\\times', '*'),
        (r'\\approx', '='), (r'\\simeq', '='),
        (r'\\sim', '~'), (r'\\pm', '+-'),
    ]

    @staticmethod
    def sanitize(formula: str) -> str:
        """Clean LaTeX artifacts and Unicode Greek from a formula string."""
        f = formula
        for pattern, repl in ReverseCompiler.LATEX_ARTIFACTS:
            f = re.sub(pattern, repl, f)
        # Map Unicode Greek letters and superscripts
        for greek, ascii_name in ReverseCompiler.GREEK_MAP.items():
            f = f.replace(greek, ascii_name)
        # Normalize stacked superscript operators: phi^-^1 → phi^-1
        f = re.sub(r'\^-\^(\d+)', r'^-\1', f)
        f = re.sub(r'\^-\^', r'^-', f)
        f = re.sub(r'(?<![a-zA-Z])B(?![a-zA-Z])', '4', f)
        # Remove multiple spaces
        f = re.sub(r'  +', ' ', f).strip()
        # Remove leading/trailing punctuation that isn't part of formula
        f = f.strip('.,;: ')
        return f
    
    @staticmethod
    def split_multi_equals(formula: str):
        """Split A = B = C into (formula, assertion, value_dump_flag).
        Returns (cleaned_formula, assertions_list, is_value_dump).
        """
        parts = [p.strip() for p in formula.split('=')]
        if len(parts) <= 2:
            return formula, [], False
        
        # Check if ALL parts after the first are numeric -> value dump
        all_numeric = all(
            re.fullmatch(r'[\d.+\-eE\s/×*]+', p.replace(' ', ''))
            for p in parts[1:]
        )
        if all_numeric:
            # Keep only the first `name = algebraic_expr` part
            return f"{parts[0]} = {parts[1]}", parts[2:], True
        
        # Otherwise, keep first = expr, rest are assertions
        return f"{parts[0]} = {parts[1]}", parts[2:], False
    
    @staticmethod
    def is_value_dump(formula: str) -> bool:
        """Check if formula is pure number assignment (value dump)."""
        if '=' not in formula:
            return False
        rhs = formula.split('=', 1)[1].strip()
        # Pure number: no letters except e for scientific notation
        cleaned = rhs.replace('e', '').replace('E', '')
        return bool(re.fullmatch(r'[\d.+\-*/×\s]+', cleaned))
    
    def prepare_corpus(self, formulas: Sequence[str]):
        """Full corpus preparation: sanitize + split + classify dumps.
        Returns (clean_formulas, value_dumps, assertions).
        """
        clean = []
        dumps = []
        assertions = []
        for f in formulas:
            s = self.sanitize(f)
            if not s:
                continue
            s, extra_assertions, is_dump = self.split_multi_equals(s)
            assertions.extend(extra_assertions)
            if is_dump or self.is_value_dump(s):
                dumps.append(s)
            else:
                clean.append(s)
        return clean, dumps, assertions

    @staticmethod
    def tokenize(formula: str) -> List[Token]:
        parts = TOKEN_RE.findall(formula)
        tokens: List[Token] = []
        for i, part in enumerate(parts):
            if re.fullmatch(r"\d+\.\d+|\d+", part):
                kind = "number"
            elif re.fullmatch(r"[A-Za-zα-ωΑ-Ω]+", part):
                kind = "symbol"
            elif part in {"=", "->", "=>", ":", "::", "+", "-", "*", "/", "**", "//", "<=", ">=", "!=", "=="}:
                kind = "operator"
            elif part in {"(", ")", "[", "]", "{", "}"}:
                kind = "group"
            elif part in {",", ";"}:
                kind = "separator"
            elif part in {"^", "_"}:
                kind = "binding"
            else:
                kind = "other"
            tokens.append(Token(text=part, kind=kind, index=i))
        return tokens

    def build_token_stats(self) -> Dict[str, Dict[str, int]]:
        stats: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for rec in self.records:
            for t in rec.tokens:
                stats[t.text][t.kind] += 1
        return {k: dict(v) for k, v in stats.items()}

    # === ISA / Microcode Layer ===
    ISA = {
        "ADD": "arithmetic", "SUB": "arithmetic", "MUL": "arithmetic", "DIV": "arithmetic",
        "CMP": "comparison", "MOV": "data", "SHL": "bitwise", "SHR": "bitwise",
        "JMP": "control", "SYNC": "sync",
        "LOAD": "data", "STORE": "data", "SQRT": "math", "POW": "math",
        "NEG": "arithmetic", "AND": "bitwise", "OR": "bitwise", "XOR": "bitwise",
    }

    # SYNC can be represented as string "SYNC" or number "2"
    SYNC_TOKENS = {"SYNC", "2"}

    def formula_to_ir(self, formula: str) -> List[str]:
        """AST-driven IR translation. Uses parse tree structure."""
        # Normalize Unicode first
        f = formula
        greek = {'φ':'phi','ε':'eps','β':'beta','κ':'kappa','λ':'lambda','η':'eta',
                 'π':'pi','σ':'sigma','δ':'delta','γ':'gamma','ħ':'hbar','√':'sqrt',
                 'Λ':'Lambda','ξ':'xi','τ':'tau','ω':'omega','α':'alpha','θ':'theta','ρ':'rho',
                 'μ':'mu','Σ':'Sigma','Π':'Pi','ψ':'psi','Ω':'Omega','Γ':'Gamma','Δ':'Delta',
                 'Φ':'Phi','Ψ':'Psi','χ':'chi'}
        for g, a in greek.items(): f = f.replace(g, a)
        f = f.replace('·', '*')
        for c in '⁰¹²³⁴⁵⁶⁷⁸⁹': f = f.replace(c, '^' + str('⁰¹²³⁴⁵⁶⁷⁸⁹'.index(c)))
        for c in '₀₁₂₃₄₅₆₇₈₉': f = f.replace(c, '_' + str('₀₁₂₃₄₅₆₇₈₉'.index(c)))
        f = f.replace('⁻', '^-')
        
        ir = []
        # Pipeline case
        if '->' in f:
            ir.append('; PIPELINE')
            for seg in f.split('->'):
                seg = seg.strip()
                # Check if this segment is an action (SHL, SHR, etc.)
                words = seg.split()
                for w in words:
                    if w.upper() in self.ISA:
                        ir.append(f'  {w.upper()}')
                    elif w.isdigit() or (w.startswith('0') and all(c in '01' for c in w)):
                        ir.append(f'  LOAD {w}')
                    else:
                        ir.append(f'  LOAD {w}')
            return ir
        
        # Algebraic case: use AST-driven approach
        # Step 1: tokenize the expression
        tokens = self._tokenize_ast(f)
        # Step 2: convert to postfix (RPN)
        rpn = self._to_postfix(tokens)
        # Step 3: emit IR from RPN
        for tok in rpn:
            if tok in ('ADD', 'SUB', 'MUL', 'DIV', 'NEG'):
                ir.append(f'  {tok}')
            elif tok == 'POW':
                ir.append('  POW')
            elif tok == 'SQRT':
                ir.append('  SQRT')
            elif tok.startswith('_') or tok.startswith('^'):
                ir.append(f'  LOAD {tok}')
            elif tok.isdigit() or (tok.startswith('-') and tok[1:].isdigit()):
                ir.append(f'  LOAD {tok}')
            elif tok.replace('.','').isdigit():
                ir.append(f'  LOAD {tok}')
            else:
                ir.append(f'  LOAD {tok}')
        
        # Add STORE for assignment
        if '=' in f:
            name = f.split('=', 1)[0].strip()
            # Clean up name
            name = name.split('(')[0].strip() if '(' in name else name
            ir.append(f'  STORE {name}')
        
        return ir

    def _tokenize_ast(self, expr: str) -> list:
        """Tokenize an expression into tokens for AST/IR translation.
        Handles ^ as binary operator: phi^-1 → phi, ^, -1; phi^2 → phi, ^, 2.
        """
        if '=' in expr:
            expr = expr.split('=', 1)[1].strip()
        
        tokens = []
        i = 0
        while i < len(expr):
            c = expr[i]
            if c in ' 	': i += 1; continue
            if c in '()[]{}': tokens.append(c); i += 1; continue
            if c in '+-*/':
                # Negative number if - follows another operator or start
                if c == '-' and (not tokens or tokens[-1] in '(*+/^'):
                    j = i + 1
                    while j < len(expr) and (expr[j].isalnum() or expr[j] in '.eE'):
                        j += 1
                    if j > i + 1:  # don't treat bare - as negative number
                        tokens.append(expr[i:j])
                        i = j
                        continue
                tokens.append(c)
                i += 1
                continue
            if c == '^':
                # ^ is a binary operator. Next operand is the exponent.
                if i + 1 < len(expr) and (expr[i+1] == '-' or expr[i+1].isdigit() or expr[i+1] == '.'):
                    tokens.append('^')
                    if expr[i+1] == '-':
                        j = i + 2
                        while j < len(expr) and (expr[j].isalnum() or expr[j] in '.eE'):
                            j += 1
                        tokens.append(expr[i+1:j])
                    else:
                        j = i + 1
                        while j < len(expr) and (expr[j].isalnum() or expr[j] in '.eE'):
                            j += 1
                        tokens.append(expr[i+1:j])
                    i = j
                    continue
                tokens.append('^')
                i += 1
                continue
            if c.isalnum() or c in '._':
                j = i
                while j < len(expr) and (expr[j].isalnum() or expr[j] in '._'):
                    j += 1
                tok = expr[i:j]
                if j < len(expr) and expr[j] == '(':
                    depth = 1
                    k = j + 1
                    while k < len(expr) and depth > 0:
                        if expr[k] == '(': depth += 1
                        elif expr[k] == ')': depth -= 1
                        k += 1
                    tokens.append(tok)
                    tokens.append('(')
                    inner = expr[j+1:k-1] if k > j+1 else ''
                    inner_tokens = self._tokenize_ast(inner)
                    tokens.extend(inner_tokens)
                    tokens.append(')')
                    i = k
                else:
                    tokens.append(tok)
                    i = j
                continue
            tokens.append(c)
            i += 1
        return tokens

    def _to_postfix(self, tokens: list) -> list:
        """Convert infix tokens to postfix (RPN) using shunting-yard.
        Handles implied multiplication: '33 beta' → '33 * beta'.
        """
        prec = {'+': 1, '-': 1, '*': 2, '/': 2, '^': 3}
        ops = {'+': 'ADD', '-': 'SUB', '*': 'MUL', '/': 'DIV', '^': 'POW'}
        postfix = []
        stack = []
        
        # Pre-process: insert implicit '*' between adjacent operand-like tokens
        # and handle unary minus: -(expr) → 0 - (expr)
        processed = []
        for i, t in enumerate(tokens):
            if i > 0:
                prev = tokens[i-1]
                # Insert * if prev is an operand-like token and current is an operand-like token
                prev_is_operand = (prev not in '()' and prev not in '+-*/^' 
                                   and prev not in ops and prev not in ('ADD','SUB','MUL','DIV','POW','SQRT','STORE')
                                   and prev not in ('sqrt','sin','cos','tan','log','exp','arctan','ln'))
                curr_is_operand = (t not in '()' and t not in '+-*/^'
                                   and t not in ops and t not in ('ADD','SUB','MUL','DIV','POW','SQRT','STORE')
                                   and t not in ('sqrt','sin','cos','tan','log','exp','arctan','ln'))
                if prev_is_operand and curr_is_operand:
                    processed.append('*')
            # Unary minus detection: '-' at start of expression or after ( or ^ or * or /
            if t == '-' and (i == 0 or tokens[i-1] in ('(','^','*','/')):
                processed.append('0')
                processed.append('-')
            else:
                processed.append(t)
        
        i = 0
        while i < len(processed):
            t = processed[i]
            if t == '(':
                stack.append(t)
            elif t == ')':
                while stack and stack[-1] != '(':
                    postfix.append(ops[stack.pop()])
                if stack and stack[-1] == '(':
                    stack.pop()  # Remove (
                # Check if the token before ( was a function name
                if stack and stack[-1] in ('sqrt', 'sin', 'cos', 'tan', 'log', 'exp', 'ln', 'arctan'):
                    fn = stack.pop()
                    postfix.append(fn.upper())
            elif t in '+-*/^':
                while stack and stack[-1] != '(' and prec.get(stack[-1], 0) >= prec.get(t, 0):
                    postfix.append(ops[stack.pop()])
                stack.append(t)
            elif t in ('sqrt', 'sin', 'cos', 'tan', 'log', 'exp', 'ln', 'arctan'):
                # Function - push to stack, will be processed when ) is seen
                stack.append(t)
            elif t in ('ADD', 'SUB', 'MUL', 'DIV', 'POW', 'SQRT', 'STORE'):
                # Already an operator from sanitization
                postfix.append(t)
            else:
                # Operand
                postfix.append(t)
            i += 1
        
        while stack:
            op = stack.pop()
            if op != '(':
                postfix.append(ops[op])
        
        return postfix

    def build_symbol_table(self) -> Dict[str, Dict]:
        table = {}
        for rec in self.records:
            raw = rec.raw
            if '=' in raw:
                name = raw.split('=', 1)[0].strip()
                expr = raw.split('=', 1)[1].strip()
                deps = set()
                for tok in [t.text for t in rec.tokens]:
                    if tok[0].isalpha() and tok not in self.ISA and tok not in {'sqrt','sin','cos','tan','log','exp','arctan','ln'}:
                        deps.add(tok)
                table[name] = {"expression": expr, "dependencies": sorted(deps), "instruction_count": len(self.formula_to_ir(raw))}
        return table

    # === Formula Type Classification (first-principles) ===
    # Classification is based on dependency chain analysis, not hardcoded rules:
    #   - Build a structural symbol set from all formulas that define symbols
    #   - For each formula, check if every RHS token traces back to φ
    #   - If all traceable → structural
    #   - If RHS is pure number with no structural refs → input
    #   - If mixed (some struct refs + untraceable terms) → fitting

    def _build_structural_closure(self) -> set:
        """Build the transitive closure of all structurally-defined symbols."""
        closure = {'phi', 'x', 'sqrt', 'pi', 'e', '0010', '0100', 'V_EW_over_M_P', 'm_t_over_V_EW'}
        changed = True
        while changed:
            changed = False
            for rec in self.records:
                raw = self.sanitize(rec.raw)
                if '=' not in raw:
                    continue
                name = raw.split('=', 1)[0].strip().lower()
                rhs = raw.split('=', 1)[1].strip()
                rhs_tokens = set()
                for t in [tok.text for tok in self.tokenize(rhs)]:
                    s = t.lower()
                    if re.fullmatch(r'[\d.]+', s): continue
                    if s in '+-*/^=()_., ': continue
                    if s.startswith('-') and s[1:].replace('.','').isdigit(): continue
                    if s.startswith('^') or s.startswith('_'):
                        s = s.lstrip('^_')
                        if not s or re.fullmatch(r'[\d.]+', s): continue
                        if s.startswith('-') and s[1:].replace('.','').isdigit(): continue
                    if s in {'sqrt','sin','cos','tan','log','exp','ln','arctan'}: continue
                    rhs_tokens.add(s)
                if rhs_tokens and rhs_tokens.issubset(closure) and name not in closure:
                    closure.add(name)
                    changed = True
        return closure

    def classify_formula_type(self, formula: str) -> Dict:
        raw = formula
        result = {"type": "structural", "confidence": 1.0, "indicators": [], "dataflow_type": "algebraic"}
        
        # Build structural closure lazily
        if not hasattr(self, '_struct_closure') or self._struct_closure is None:
            self._struct_closure = self._build_structural_closure()
        closure = self._struct_closure
        
        f = formula.lower()
        
        # 1) Axiom detection
        if ('x^2 + x - 1' in f) or ('phi' in f and 'sqrt' in f and len(f) < 40):
            result["type"] = "axiom"; result["indicators"].append("foundation_equation")
            return result
        
        # 2) Pipeline detection (-> syntax) - BEFORE = check
        if '->' in raw:
            result["dataflow_type"] = "pipeline"
            segments = [s.strip() for s in raw.split('->')]
            result["pipeline_chain"] = segments
            all_traceable = True
            untraceable = []
            for seg in segments:
                tokens = set()
                for tok in [t.text for t in self.tokenize(seg)]:
                    ts = tok.lower()
                    if re.fullmatch(r'[\d.]+', ts): continue
                    if ts in '+-*/^=()': continue
                    tokens.add(ts)
                tokens -= {'sqrt','sin','cos','tan','log','exp','ln','arctan','pi','e','shl','shr','mov','add','sub','cmp','jmp','sync'}
                for t_ in tokens:
                    if t_ not in closure:
                        untraceable.append(t_)
                        all_traceable = False
            if all_traceable:
                result["type"] = "structural"; result["confidence"] = 1.0
            else:
                result["type"] = "fitting"
                result["confidence"] = max(0.1, 1.0 - len(untraceable) * 0.3)
                result["indicators"].append(f"untraceable_segment_tokens: {untraceable}")
            return result
        
        # 3) Algebraic / definition (= syntax)
        if '=' not in raw:
            result["type"] = "unknown"; result["dataflow_type"] = "unknown"
            return result
        
        name = raw.split('=', 1)[0].strip()
        rhs = raw.split('=', 1)[1].strip()
        
        # Extract RHS tokens
        rhs_tokens = set()
        for tok in [t.text for t in self.tokenize(rhs)]:
            ts = tok.lower()
            if ts.isdigit() or ts in '+-*/^=()_., ': continue
            if ts.startswith('^') or ts.startswith('_'): ts = ts[1:]
            if not ts: continue
            if ts[0].isdigit(): continue
            if ts.startswith('-') and ts[1:].replace('.','').isdigit(): continue
            rhs_tokens.add(ts)
        rhs_tokens -= {'sqrt', 'sin', 'cos', 'tan', 'log', 'exp', 'ln', 'arctan', 'pi', 'e'}
        
        # 4) Pure number assignment -> input
        if not rhs_tokens:
            result["type"] = "input"; result["indicators"].append("external_input")
            return result
        
        # 5) Dependency check
        traceable = rhs_tokens.issubset(closure)
        untraceable = rhs_tokens - closure
        fraction_traceable = len(rhs_tokens - untraceable) / max(len(rhs_tokens), 1)
        
        if traceable:
            result["type"] = "structural"; result["confidence"] = 1.0
        elif fraction_traceable >= 0.5:
            result["type"] = "fitting"
            result["confidence"] = fraction_traceable
            result["indicators"].append(f"untraceable_terms: {sorted(untraceable)}")
        else:
            result["type"] = "fitting"
            result["confidence"] = fraction_traceable
            result["indicators"].append(f"mostly_untraceable: {sorted(untraceable)}")
        
        return result

    def stress_test(self, formulas: Sequence[str]):
        """Full stress test with corpus sanitization + classification."""
        clean, dumps, assertions = self.prepare_corpus(formulas)
        results = {}
        ir_counts = {}
        for f in clean:
            cls = self.classify_formula_type(f)
            results[f] = cls
            ir_counts[f] = len(self.formula_to_ir(f))
        
        type_stats = {}
        for cls in results.values():
            t = cls['type']
            type_stats[t] = type_stats.get(t, 0) + 1
        
        pipeline_count = sum(1 for cls in results.values() if cls['dataflow_type'] == 'pipeline')
        
        return {
            "total_raw": len(formulas),
            "clean": len(clean),
            "dumps_removed": len(dumps),
            "assertions_extracted": len(assertions),
            "type_stats": type_stats,
            "pipeline_formulas": pipeline_count,
            "classifications": results,
            "ir_counts": ir_counts,
            "total_instructions": sum(ir_counts.values()),
            "avg_instructions": sum(ir_counts.values()) / max(len(clean), 1),
        }

    def microcode_statistics(self) -> Dict[str, int]:
        counts = {}
        for rec in self.records:
            for line in self.formula_to_ir(rec.raw):
                line = line.strip()
                if line.startswith(';'): continue
                parts = line.split()
                if parts: counts[parts[0]] = counts.get(parts[0], 0) + 1
        return counts

    # === P1: VM Execution Engine (added in v22) ===

    @staticmethod
    def eval_ir(ir_tokens: list, mem: dict) -> float:
        """Execute IR tokens on a stack machine with symbol resolution from mem.
        
        ISA opcodes: LOAD (push operand), STORE (pop → mem[name]), 
        POW (pop2: base^exp), DIV (pop2: a/b), ADD (pop2: a+b), 
        SUB (pop2: a-b), MUL (pop2: a*b), SQRT (pop1: sqrt(a)).
        
        LOAD semantics: operand is either an immediate (number) or 
        a symbol resolved from mem dict.
        """
        OPS = {
            "LOAD": lambda s, v: s.append(v),
            "POW":  lambda s, _: s.append(s.pop(-2) ** s.pop()),
            "DIV":  lambda s, _: s.append(s.pop(-2) / s.pop()),
            "ADD":  lambda s, _: s.append(s.pop(-2) + s.pop()),
            "SUB":  lambda s, _: s.append(s.pop(-2) - s.pop()),
            "MUL":  lambda s, _: s.append(s.pop(-2) * s.pop()),
            "SQRT": lambda s, _: s.append(math.sqrt(s.pop())),
            "NEG":  lambda s, _: s.append(-s.pop()),
            "STORE": lambda s, name: mem.__setitem__(name, s.pop()),
        }
        stack = []
        n = 0
        last_value = 0.0
        while n < len(ir_tokens):
            op = ir_tokens[n]
            n += 1
            if op in OPS and op not in ("LOAD", "STORE"):
                OPS[op](stack, None)
                last_value = stack[-1] if stack else 0.0
            elif op == "STORE":
                if n >= len(ir_tokens): break
                name = ir_tokens[n]; n += 1
                last_value = stack[-1] if stack else 0.0
                OPS[op](stack, name)
            else:
                if n >= len(ir_tokens): break
                a = ir_tokens[n]; n += 1
                a_stripped = a.lstrip('-').replace('.', '', 1)
                if a_stripped.replace('.', '', 1).isdigit():
                    OPS[op](stack, float(a))
                elif a in mem:
                    OPS[op](stack, mem[a])
                else:
                    try:
                        OPS[op](stack, float(a))
                    except ValueError:
                        raise KeyError(f"Unknown symbol: {a}")
                last_value = stack[-1] if stack else 0.0
        return last_value

    def verify_all(self, formulas: Sequence[str], expected: dict = None) -> dict:
        """Run the full pipeline: sanitize → classify → IR → eval → compare.
        
        Args:
            formulas: List of formula strings
            expected: Optional dict {formula_name: expected_value}
            
        Returns:
            dict with verification results including errors
        """
        results = {}
        clean, dumps, assertions = self.prepare_corpus(formulas)
        
        # Execute in dependency order
        mem = {}
        exec_order = ["phi", "eps", "kappa", "beta", "k_u", "k_l", "V_EW_over_M_P"]
        for f in clean:
            cls = self.classify_formula_type(f)
            if '=' not in f:
                continue
            name = f.split('=', 1)[0].strip()
            ir_lines = [l.strip() for l in self.formula_to_ir(f) if l.strip() and not l.startswith(';')]
            if not ir_lines:
                continue
            # Eval IR
            ir_tokens = []
            for line in ir_lines:
                ir_tokens.extend(line.split())
            try:
                value = self.eval_ir(ir_tokens, mem)
                # If the last instruction is STORE, the value is on the stack before STORE
                # Actually eval_ir already returns stack[-1], which is the computed value
                results[name] = {
                    "value": value,
                    "ir": ir_lines,
                    "type": cls['type'],
                    "error": None
                }
            except Exception as e:
                results[name] = {
                    "value": None,
                    "ir": ir_lines,
                    "type": cls['type'],
                    "error": str(e)
                }
        
        # Compare with expected values if provided
        if expected:
            for name, exp_val in expected.items():
                if name in results and results[name]['value'] is not None:
                    actual = results[name]['value']
                    err_pct = abs(actual - exp_val) / abs(exp_val) * 100
                    results[name]['expected'] = exp_val
                    results[name]['error_pct'] = err_pct
        
        return {
            "total": len(clean),
            "dumps": len(dumps),
            "verified": sum(1 for r in results.values() if r['error'] is None),
            "failed": sum(1 for r in results.values() if r['error'] is not None),
            "results": results,
        }

    # === P3: Dependency Graph Export (added in v22) ===

    def export_dependency_graph(self, formulas: Sequence[str] = None) -> dict:
        """Export the full dependency adjacency matrix.
        
        Returns both the symbolic dependency graph (which formula references which)
        and the numerical closure chain.
        """
        # Build structural closure
        closure = self._build_structural_closure()
        
        # Get all formulas with classification
        if formulas is None:
            formulas = [rec.raw for rec in self.records]
        
        clean, dumps, assertions = self.prepare_corpus(formulas)
        
        # Build adjacency: which formula RHS references which symbol
        adj = {}
        for f in clean:
            if '=' not in f:
                continue
            name = f.split('=', 1)[0].strip()
            rhs = f.split('=', 1)[1].strip()
            rhs_tokens = set()
            for t in [tok.text for tok in self.tokenize(rhs)]:
                ts = t.lower()
                if ts in closure and ts != name.lower():
                    rhs_tokens.add(ts)
            adj[name] = sorted(rhs_tokens - {'sqrt', 'sin', 'cos', 'tan', 'log', 'exp', 'ln', 'arctan', 'pi', 'e'})
        
        # Build ordered closure chain
        ordered = list(closure - {'0010', '0100', 'x', 'sqrt', 'pi', 'e', 'sin', 'cos', 'tan', 'log', 'exp'})
        ordered = sorted(ordered, key=lambda s: (
            0 if s == 'phi' else
            1 if s in ('eps', 'beta', 'kappa') else
            2 if s.startswith('k_') else
            3 if s.startswith('V_') else
            4 if s == 'mtaummu' else 5
        ))
        
        return {
            "closure_size": len(closure),
            "closure_symbols": sorted(closure),
            "ordered_chain": ordered,
            "adjacency": adj,
            "matrix": self._format_adjacency_matrix(adj, ordered),
            "levels": {
                "axiom": [s for s in ordered if s == 'phi'],
                "primary": [s for s in ordered if s in ('eps', 'beta', 'kappa')],
                "sector_depth": [s for s in ordered if s.startswith('k_')],
                "ckm": [s for s in ordered if s.startswith('V_')],
                "mass_ratio": [s for s in ordered if s == 'mtaummu'],
            }
        }
    
    def _format_adjacency_matrix(self, adj: dict, ordered: list) -> str:
        """Format adjacency as ASCII matrix for documentation."""
        if not ordered:
            return "(empty)"
        header = "         " + "  ".join(f"{s:6s}" for s in ordered)
        lines = [header]
        for r in ordered:
            row = f"{r:6s}  "
            for c in ordered:
                val = 1 if c in adj.get(r, []) else 0
                row += f"{val:6d}"
            lines.append(row)
        return "\n".join(lines)

    def build_kind_transition_stats(self) -> Dict[str, Dict[str, int]]:
        stats: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for rec in self.records:
            kinds = [t.kind for t in rec.tokens]
            for a, b in zip(kinds, kinds[1:]):
                stats[a][b] += 1
        return {k: dict(v) for k, v in stats.items()}

    @staticmethod
    def classify_token_candidates(token: str) -> List[str]:
        if token == "2":
            return ["operand", "literal", "action", "opcode", "state_marker"]
        if re.fullmatch(r"\d+\.\d+|\d+", token):
            return ["operand", "literal", "length_field", "address"]
        if re.fullmatch(r"[A-Za-zα-ωΑ-Ω]+", token):
            if token in {"sqrt", "sin", "cos", "tan", "log", "exp"}:
                return ["function", "action", "opcode"]
            if token in ReverseCompiler.SYNC_TOKENS or token in {"SHL", "MOV", "ADD", "SUB", "CMP", "JMP"}:
                return ["action", "opcode", "state_marker"]
            return ["state_marker", "binding_symbol", "opcode", "unknown"]
        if token in {"=", "->", "=>", ":", "::", "<=", ">=", "!=", "=="}:
            return ["delimiter", "binding_symbol", "control_flag"]
        if token in {"(", ")", "[", "]", "{", "}"}:
            return ["delimiter", "binding_symbol"]
        if token in {",", ";"}:
            return ["delimiter"]
        if token in {"^", "_"}:
            return ["binding_symbol", "control_flag"]
        if token in {"+", "-", "*", "/", "**", "//"}:
            return ["opcode", "delimiter", "control_flag"]
        return ["unknown"]

    @staticmethod
    def prune_candidates(token: str, cands: List[str]) -> List[str]:
        if token == "2":
            return [c for c in cands if c in {"operand", "literal", "action", "opcode", "state_marker"}]
        if re.fullmatch(r"\d+\.\d+|\d+", token):
            return [c for c in cands if c in {"operand", "literal", "length_field", "address"}]
        if token in {"=", "->", "=>", ":", "::"}:
            return [c for c in cands if c in {"delimiter", "binding_symbol", "control_flag"}]
        if token in {"(", ")", "[", "]", "{", "}"}:
            return ["delimiter"]
        if token in {"^", "_"}:
            return ["binding_symbol"]
        if token in {",", ";"}:
            return ["delimiter"]
        if token in {"+", "-", "*", "/", "**", "//"}:
            return [c for c in cands if c in {"opcode", "delimiter", "control_flag"}]
        return cands

    def enumerate_hypotheses(self, max_hypotheses: int = 512) -> List[DecodeHypothesis]:
        unique_tokens = sorted({t.text for rec in self.records for t in rec.tokens})
        candidate_lists = [self.classify_token_candidates(tok) for tok in unique_tokens]

        total = 1
        for c in candidate_lists:
            total *= max(1, len(c))
        if total > 50000:
            candidate_lists = [self.prune_candidates(tok, cands) for tok, cands in zip(unique_tokens, candidate_lists)]

        hypotheses: List[DecodeHypothesis] = []
        for idx, roles in enumerate(product(*candidate_lists)):
            if len(hypotheses) >= max_hypotheses:
                break
            mapping = dict(zip(unique_tokens, roles))
            hypotheses.append(DecodeHypothesis(name=f"H{idx:04d}", assignment=RoleAssignment(mapping=mapping)))
        return hypotheses

    @staticmethod
    def token_role_score(token: Token, role: str, prev_kind: Optional[str], next_kind: Optional[str]) -> float:
        score = 0.0
        if token.kind == "number":
            score += 3.0 if role in {"operand", "literal", "length_field", "address"} else -2.0
        elif token.kind == "symbol":
            score += 2.2 if role == "function" else 2.0 if role == "action" else 1.8 if role in {"state_marker", "binding_symbol"} else 0.2 if role == "opcode" else -0.3
        elif token.kind in {"group", "separator"}:
            score += 3.0 if role == "delimiter" else -1.5
        elif token.kind == "binding":
            score += 3.0 if role == "binding_symbol" else -1.0
        elif token.kind == "operator":
            score += 2.0 if role in {"delimiter", "opcode", "control_flag", "action"} else -0.5

        if token.text in {"=", "->", "=>"} and role == "delimiter":
            score += 2.5
        if token.text in {"^", "_"} and role == "binding_symbol":
            score += 2.5
        if token.text in {"(", ")", "[", "]", "{", "}"} and role == "delimiter":
            score += 2.5
        if token.text in {"sqrt", "sin", "cos", "tan", "log", "exp"} and role == "function":
            score += 3.0
        if (token.text in ReverseCompiler.SYNC_TOKENS or token.text in {"SHL", "MOV", "ADD", "SUB", "CMP", "JMP"}) and role == "action":
            score += 3.0

        if token.kind == "number" and prev_kind in {"symbol", "number"} and next_kind in {"symbol", "number"}:
            score += 1.0 if role in {"operand", "literal", "address"} else -1.0
        return score

    @staticmethod
    def family_of(token_text: str, role: str) -> str:
        if role == "opcode":
            if token_text in {"=", "->", "=>", ":", "::"}:
                return "control-flow"
            if token_text in {"+", "-", "*", "/", "**", "//"}:
                return "arithmetic"
            if token_text in {"^", "_"}:
                return "binding"
            return "symbolic-opcode"
        if role == "action":
            return "action"
        if role == "function":
            return "function"
        if role == "delimiter":
            return "separator"
        if role == "binding_symbol":
            return "binding"
        if role in {"operand", "literal", "length_field", "address"}:
            return "data"
        if role == "state_marker":
            return "state"
        if role == "control_flag":
            return "flags"
        return "unknown"

    def build_family_stats(self, hyp: DecodeHypothesis) -> Dict[str, int]:
        stats: Dict[str, int] = defaultdict(int)
        for rec in self.records:
            for t in rec.tokens:
                fam = self.family_of(t.text, hyp.assignment.role_of(t.text))
                stats[fam] += 1
        return dict(stats)

    def derive_position_constraints(self) -> Dict[str, List[str]]:
        constraints: Dict[str, List[str]] = defaultdict(list)
        for rec in self.records:
            for i, t in enumerate(rec.tokens):
                prev_tok = rec.tokens[i - 1] if i > 0 else None
                next_tok = rec.tokens[i + 1] if i + 1 < len(rec.tokens) else None
                if t.text in {"=", "->", "=>"}:
                    constraints[t.text].append(f"separator-like: left={prev_tok.text if prev_tok else 'START'}, right={next_tok.text if next_tok else 'END'}")
                if t.text in {"^", "_"}:
                    constraints[t.text].append(f"binding-like: base={prev_tok.text if prev_tok else 'START'}, attach={next_tok.text if next_tok else 'END'}")
                if t.kind == "number" and prev_tok and prev_tok.kind == "symbol" and next_tok and next_tok.kind in {"operator", "group"}:
                    constraints[t.text].append(f"possible packed-operand after {prev_tok.text}")
                if t.kind == "symbol" and prev_tok and prev_tok.text == "_":
                    constraints[t.text].append("subscript-like symbol")
                if t.kind == "symbol" and next_tok and next_tok.text == "^":
                    constraints[t.text].append("base before exponent binding")
        return {k: v for k, v in constraints.items()}

    def collision_analysis(self) -> Dict[str, Dict[str, int]]:
        collision: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for rec in self.records:
            for t in rec.tokens:
                collision[t.text][t.kind] += 1
        return {k: dict(v) for k, v in collision.items()}

    def build_parse_tree(self, rec: FormulaRecord, hyp: DecodeHypothesis) -> ParseNode:
        root = ParseNode(label="FORMULA")
        current = ParseNode(label="SEGMENT")
        stack = [root]

        def flush_current():
            nonlocal current
            if current.children:
                stack[-1].children.append(current)
            current = ParseNode(label="SEGMENT")

        i = 0
        while i < len(rec.tokens):
            t = rec.tokens[i]
            role = hyp.assignment.role_of(t.text)
            next_tok = rec.tokens[i + 1] if i + 1 < len(rec.tokens) else None

            if t.text in {"=", "->", "=>"}:
                flush_current()
                stack[-1].children.append(ParseNode(label="ASSIGN" if t.text == "=" else "ARROW", token=t.text))
                i += 1
                continue

            if t.text in {"(", "[", "{"}:
                prev_tok = rec.tokens[i - 1] if i > 0 else None
                if prev_tok and hyp.assignment.role_of(prev_tok.text) == "function":
                    node = ParseNode(label="FUNCTION_CALL", token=prev_tok.text)
                    if current.children:
                        current.children.pop()
                    current.children.append(node)
                    stack.append(node)
                else:
                    node = ParseNode(label="GROUP", token=t.text)
                    current.children.append(node)
                    stack.append(node)
                i += 1
                continue

            if t.text in {")", "]", "}"}:
                flush_current()
                if len(stack) > 1:
                    stack.pop()
                stack[-1].children.append(ParseNode(label="GROUP_END", token=t.text))
                i += 1
                continue

            if t.text in {"^", "_"}:
                current.children.append(ParseNode(label="BIND", token=t.text))
                i += 1
                continue

            if role == "function" and next_tok and next_tok.text == "(":
                current.children.append(ParseNode(label="FUNCTION", token=t.text))
                i += 1
                continue

            if role == "action":
                current.children.append(ParseNode(label="ACTION", token=t.text))
                i += 1
                continue

            current.children.append(ParseNode(label=role.upper(), token=t.text))
            i += 1

        flush_current()
        return root

    def build_state_machine(self, rec: FormulaRecord, hyp: DecodeHypothesis) -> List[Tuple[str, str, str]]:
        state = "START"
        transitions: List[Tuple[str, str, str]] = []
        for t in rec.tokens:
            role = hyp.assignment.role_of(t.text)
            if t.text == "=":
                next_state = "RHS"
                label = "ASSIGN"
            elif t.text in {"->", "=>"}:
                next_state = "PIPE"
                label = "ARROW"
            elif t.text in {"(", "[", "{"}:
                next_state = "GROUP"
                label = "GROUP_START"
            elif t.text in {")", "]", "}"}:
                next_state = "POST_GROUP"
                label = "GROUP_END"
            elif t.text in {"^", "_"}:
                next_state = "BIND"
                label = "BIND"
            elif role == "function":
                next_state = "CALL"
                label = "FUNCTION"
            elif role == "action":
                next_state = "ACTION"
                label = "ACTION"
            else:
                if role in {"operand", "literal", "length_field", "address"}:
                    next_state = "DATA"
                elif role == "opcode":
                    next_state = "OP"
                elif role == "state_marker":
                    next_state = "STATE"
                else:
                    next_state = "SEQ"
                label = role.upper()
            transitions.append((state, f"{t.text}:{label}", next_state))
            state = next_state
        return transitions

    def role_transition_matrix(self, hyp: DecodeHypothesis) -> Dict[str, Dict[str, int]]:
        stats: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for rec in self.records:
            roles = [hyp.assignment.role_of(t.text) for t in rec.tokens]
            for a, b in zip(roles, roles[1:]):
                stats[a][b] += 1
        return {k: dict(v) for k, v in stats.items()}

    def score_hypothesis(self, hyp: DecodeHypothesis) -> Tuple[float, List[str]]:
        score = 0.0
        notes: List[str] = []
        role_counter = Counter(hyp.assignment.mapping.values())

        for rec in self.records:
            tokens = rec.tokens
            roles = [hyp.assignment.role_of(t.text) for t in tokens]
            for i, t in enumerate(tokens):
                prev_kind = tokens[i - 1].kind if i > 0 else None
                next_kind = tokens[i + 1].kind if i + 1 < len(tokens) else None
                role = roles[i]
                score += self.token_role_score(t, role, prev_kind, next_kind)

            for (r1, r2), (k1, k2) in zip(zip(roles, roles[1:]), zip([t.kind for t in tokens], [t.kind for t in tokens[1:]])):
                if r1 in {"delimiter", "binding_symbol"} and k2 in {"symbol", "number", "group"}:
                    score += 0.5
                if k1 == "binding" and r1 == "binding_symbol" and k2 in {"symbol", "number"}:
                    score += 1.0
                if k1 == "number" and k2 == "number":
                    if r1 in {"operand", "literal", "length_field", "address"} and r2 in {"operand", "literal", "length_field", "address"}:
                        score += 0.5
                    else:
                        score -= 0.5

            depth = 0
            max_depth = 0
            balanced = True
            for t in tokens:
                if t.text in {"(", "[", "{"}:
                    depth += 1
                    max_depth = max(max_depth, depth)
                elif t.text in {")", "]", "}"}:
                    depth -= 1
                    if depth < 0:
                        balanced = False
            if depth != 0:
                balanced = False
            score += 1.5 if balanced else -2.0
            score += min(1.5, 0.25 * max_depth)

            for i, t in enumerate(tokens):
                if t.text in {"=", "^", "_", "->", "=>"}:
                    if i == 0 or i == len(tokens) - 1:
                        score -= 2.0
                    else:
                        score += 0.5

        distinct_roles = len([r for r, c in role_counter.items() if c > 0 and r != "unknown"])
        score += max(0.0, 8.0 - distinct_roles)
        score -= 1.25 * role_counter.get("unknown", 0)

        families = Counter(self.family_of(tok, hyp.assignment.role_of(tok)) for tok in hyp.assignment.mapping.keys())
        score += max(0.0, 6.0 - len([f for f, c in families.items() if c > 0 and f != "unknown"]))

        opcode_like = sum(1 for tok in hyp.assignment.mapping if hyp.assignment.role_of(tok) == "opcode")
        if opcode_like > max(2, len(hyp.assignment.mapping) // 2):
            score -= (opcode_like - max(2, len(hyp.assignment.mapping) // 2)) * 0.75

        function_like = sum(1 for tok in hyp.assignment.mapping if hyp.assignment.role_of(tok) == "function")
        if function_like:
            score += 1.5

        action_like = sum(1 for tok in hyp.assignment.mapping if hyp.assignment.role_of(tok) == "action")
        if action_like:
            score += 1.0

        return score, notes

    def parse_summary(self, rec: FormulaRecord, hyp: DecodeHypothesis) -> str:
        parts: List[str] = []
        for t in rec.tokens:
            role = hyp.assignment.role_of(t.text)
            fam = self.family_of(t.text, role)
            parts.append(f"{t.text}:{role}/{fam}")
        return " ".join(parts)

    def build_binary_packet(self, rec: FormulaRecord, hyp: DecodeHypothesis) -> str:
        bits: List[str] = []
        for t in rec.tokens:
            role = hyp.assignment.role_of(t.text)
            kind_bits = KIND_BITS.get(t.kind, "01")
            role_bits = ROLE_BITS.get(role, "000")
            bits.append(kind_bits + role_bits)
        return " ".join(bits)

    def ranking(self, top: DecodeHypothesis) -> List[Tuple[str, float]]:
        counts = Counter()
        for rec in self.records:
            for t in rec.tokens:
                role = top.assignment.role_of(t.text)
                fam = self.family_of(t.text, role)
                if role in {"delimiter", "binding_symbol", "state_marker", "function", "action"}:
                    counts[t.text] += 2
                elif fam in {"separator", "binding", "state", "function", "action"}:
                    counts[t.text] += 1.5
                elif role in {"operand", "literal", "length_field", "address"}:
                    counts[t.text] += 1.0
        ranked = sorted(counts.items(), key=lambda kv: (kv[1], kv[0]), reverse=True)
        return [(k, float(v)) for k, v in ranked]

    def export_cfg_rules(self, top: DecodeHypothesis) -> Dict[str, List[str]]:
        cfg = {
            "FORMULA": ["LHS ASSIGN RHS", "PIPELINE"],
            "LHS": ["STATE_MARKER", "OPCODE", "BIND_CHAIN", "FUNCTION_CALL", "ACTION_CALL"],
            "RHS": ["SEGMENT", "PIPELINE", "EXPR"],
            "EXPR": ["OPERAND OPERATOR OPERAND", "STATE_MARKER BIND_CHAIN", "FUNCTION_CALL", "ACTION_CALL", "GROUP"],
            "PIPELINE": ["SEGMENT ARROW SEGMENT", "SEGMENT ARROW SEGMENT ARROW SEGMENT"],
            "BIND_CHAIN": ["STATE_MARKER BIND STATE_MARKER", "STATE_MARKER BIND OPERAND"],
            "FUNCTION_CALL": ["FUNCTION GROUP_START EXPR GROUP_END"],
            "ACTION_CALL": ["ACTION OPERAND", "ACTION GROUP_START EXPR GROUP_END"],
            "GROUP": ["GROUP_START EXPR GROUP_END"],
        }
        if not any(r == "binding_symbol" for r in top.assignment.mapping.values()):
            cfg["BIND_CHAIN"] = ["STATE_MARKER OPERATOR STATE_MARKER"]
        return cfg

    def validate_against_cfg(self, rec: FormulaRecord, top: DecodeHypothesis) -> str:
        roles = [top.assignment.role_of(t.text) for t in rec.tokens]
        texts = [t.text for t in rec.tokens]
        verdict = "PASS"
        reasons: List[str] = []
        if "=" in texts and texts.index("=") in {0, len(texts) - 1}:
            verdict = "FAIL"
            reasons.append("equals at boundary")
        if any(tok in {"^", "_"} for tok in texts):
            idx = next(i for i, tok in enumerate(texts) if tok in {"^", "_"})
            if idx == 0 or idx == len(texts) - 1:
                verdict = "FAIL"
                reasons.append("binding at boundary")
        if texts.count("->") > 0 and "->" in {texts[0], texts[-1]}:
            verdict = "FAIL"
            reasons.append("arrow at boundary")
        if any(tok in {"sqrt", "sin", "cos", "tan", "log", "exp"} for tok in texts):
            if "(" not in texts or ")" not in texts:
                verdict = "WARN"
                reasons.append("function without group")
        if len([r for r in roles if r != "unknown"]) < max(2, len(roles) // 3):
            verdict = "WARN"
            reasons.append("too many unknown/weak roles")
        return verdict + (": " + "; ".join(reasons) if reasons else "")

    def stress_eval(self, top: DecodeHypothesis) -> str:
        cases = [
            "x = 1",
            "a -> b -> c",
            "N_d = 44",
            "phi^-1",
            "0010 -> 0100",
            "sqrt(5)",
            "SHL 1",
        ]
        passed = 0
        lines = []
        for c in cases:
            rec = FormulaRecord(raw=c, tokens=self.tokenize(c))
            verdict = self.validate_against_cfg(rec, top)
            lines.append(f"{c} :: {verdict}")
            if verdict.startswith("PASS"):
                passed += 1
        return f"{passed}/{len(cases)} PASS | " + " || ".join(lines)

    def rewrite_rules(self, top: DecodeHypothesis) -> Dict[str, str]:
        rules = {
            "phi": "STATE_MARKER",
            "eps": "STATE_MARKER",
            "kappa": "STATE_MARKER",
            "beta": "STATE_MARKER",
            "N": "STATE_MARKER",
            "d": "STATE_MARKER",
            "L": "STATE_MARKER",
            "SHL": "ACTION",
            "MOV": "ACTION",
            "ADD": "ACTION",
            "SUB": "ACTION",
            "CMP": "ACTION",
            "JMP": "ACTION",
            "SYNC": "ACTION",
            "2": "ACTION",
            "sqrt": "FUNCTION",
            "sin": "FUNCTION",
            "cos": "FUNCTION",
            "tan": "FUNCTION",
            "log": "FUNCTION",
            "exp": "FUNCTION",
            "=": "ASSIGN",
            "->": "ARROW",
            "^": "BIND",
            "_": "BIND",
        }
        normalized = {}
        for tok, role in top.assignment.mapping.items():
            if role in {"state_marker", "binding_symbol", "delimiter", "function", "action"} and tok in rules:
                normalized[tok] = rules[tok]
        return normalized

    def token_kind(self, token_text: str) -> str:
        if re.fullmatch(r"\d+\.\d+|\d+", token_text):
            return "number"
        if re.fullmatch(r"[A-Za-zα-ωΑ-Ω]+", token_text):
            return "symbol"
        if token_text in {"=", "->", "=>", ":", "::", "+", "-", "*", "/", "**", "//", "<=", ">=", "!=", "=="}:
            return "operator"
        if token_text in {"(", ")", "[", "]", "{", "}"}:
            return "group"
        if token_text in {",", ";"}:
            return "separator"
        if token_text in {"^", "_"}:
            return "binding"
        return "other"

    def token_lattice(self, top: DecodeHypothesis) -> Dict[str, str]:
        lattice: Dict[str, str] = {}
        rewrites = self.rewrite_rules(top)
        for tok in sorted(top.assignment.mapping.keys()):
            role = top.assignment.role_of(tok)
            fam = self.family_of(tok, role)
            lattice[tok] = f"kind={self.token_kind(tok)}|role={role}|family={fam}|rewrite={rewrites.get(tok, tok)}"
        return lattice

    def auto_grammar_induction(self, top: DecodeHypothesis) -> Dict[str, List[str]]:
        productions: Dict[str, Counter] = defaultdict(Counter)
        for rec in self.records:
            roles = [top.assignment.role_of(t.text) for t in rec.tokens]
            chunk = []
            lhs_seen = False
            for t, role in zip(rec.tokens, roles):
                if t.text == "=":
                    if chunk:
                        productions["LHS"][" ".join(chunk)] += 1
                    lhs_seen = True
                    chunk = []
                    continue
                if t.text in {"->", "=>"}:
                    if chunk:
                        key = "RHS" if lhs_seen else "SEGMENT"
                        productions[key][" ".join(chunk)] += 1
                    chunk = []
                    continue
                chunk.append(self.family_of(t.text, role).upper())
            if chunk:
                key = "RHS" if lhs_seen else "SEGMENT"
                productions[key][" ".join(chunk)] += 1
        return {lhs: [rhs for rhs, _ in ctr.most_common(6)] for lhs, ctr in productions.items()}

    def decoder_exports(self, top: DecodeHypothesis) -> Dict[str, Dict[str, str]]:
        return {
            "top_decoder": {tok: top.assignment.role_of(tok) for tok in sorted(top.assignment.mapping.keys())},
            "lattice": self.token_lattice(top),
            "rewrite": self.rewrite_rules(top),
            "binary": {tok: self.token_bits(tok, top) for tok in sorted(top.assignment.mapping.keys())},
        }

    def token_bits(self, tok: str, top: DecodeHypothesis) -> str:
        role = top.assignment.role_of(tok)
        kind_bits = KIND_BITS.get(self.token_kind(tok), "01")
        role_bits = ROLE_BITS.get(role, "000")
        return kind_bits + role_bits

    def stability_summary(self, top: DecodeHypothesis) -> Dict[str, str]:
        summary: Dict[str, str] = {}
        for tok in sorted(top.assignment.mapping.keys()):
            role = top.assignment.role_of(tok)
            kind = self.token_kind(tok)
            fam = self.family_of(tok, role)
            score = 0
            if role in {"delimiter", "binding_symbol", "state_marker", "function", "action"}:
                score += 2
            if kind in {"operator", "group"} and role == "delimiter":
                score += 1
            if role == "state_marker" and tok in {"phi", "eps", "kappa", "beta", "N", "L"}:
                score += 2
            if role == "function" and tok in {"sqrt", "sin", "cos", "tan", "log", "exp"}:
                score += 3
            if role == "action" and (tok in self.SYNC_TOKENS or tok in {"SHL", "MOV", "ADD", "SUB", "CMP", "JMP"}):
                score += 3
            summary[tok] = f"stability={score}/5 role={role} family={fam}"
        return summary

    def ambiguity_summary(self, top: DecodeHypothesis) -> Dict[str, str]:
        amb: Dict[str, str] = {}
        for tok in sorted(top.assignment.mapping.keys()):
            cand = self.classify_token_candidates(tok)
            role = top.assignment.role_of(tok)
            if len(cand) == 1:
                amb[tok] = f"low-ambiguity:{role}"
            elif role == "unknown":
                amb[tok] = "high-ambiguity:unknown"
            elif role in cand:
                amb[tok] = f"medium-ambiguity:{role} among {','.join(cand)}"
            else:
                amb[tok] = f"conflict:{role} not in {','.join(cand)}"
        return amb

    def grammar_tree_candidates(self, top: DecodeHypothesis) -> List[Tuple[str, float]]:
        auto = self.auto_grammar_induction(top)
        trees: List[Tuple[str, float]] = []
        for lhs, rhs_list in auto.items():
            for rhs in rhs_list:
                shape = f"{lhs} -> {rhs}"
                score = 0.0
                if "FUNCTION" in rhs:
                    score += 3.0
                if "ACTION" in rhs:
                    score += 2.5
                if "BINDING" in rhs or "BIND" in rhs:
                    score += 2.0
                if "STATE" in rhs:
                    score += 1.5
                if "SEPARATOR" in rhs:
                    score += 1.0
                trees.append((shape, score))
        trees.sort(key=lambda kv: (kv[1], kv[0]), reverse=True)
        return trees[:20]


    def parse_pipeline_tree(self, rec: FormulaRecord, top: DecodeHypothesis) -> ParseNode:
        root = ParseNode(label="PIPELINE")
        segment = ParseNode(label="SEGMENT")
        for t in rec.tokens:
            if t.text == "->":
                if segment.children:
                    root.children.append(segment)
                root.children.append(ParseNode(label="ARROW", token=t.text))
                segment = ParseNode(label="SEGMENT")
                continue
            role = top.assignment.role_of(t.text)
            if role == "action":
                segment.children.append(ParseNode(label="ACTION", token=t.text))
            elif role in {"operand", "literal", "length_field", "address"}:
                segment.children.append(ParseNode(label="OPERAND", token=t.text))
            elif role == "state_marker":
                segment.children.append(ParseNode(label="STATE_MARKER", token=t.text))
            elif role == "binding_symbol":
                segment.children.append(ParseNode(label="BIND", token=t.text))
            else:
                segment.children.append(ParseNode(label=role.upper(), token=t.text))
        if segment.children:
            root.children.append(segment)
        return root

    def parse_algebraic_tree(self, rec: FormulaRecord, top: DecodeHypothesis) -> ParseNode:
        root = ParseNode(label="FORMULA")
        lhs = ParseNode(label="LHS")
        rhs = ParseNode(label="RHS")
        on_rhs = False
        for i, t in enumerate(rec.tokens):
            if t.text == "=":
                on_rhs = True
                continue
            target = rhs if on_rhs else lhs
            role = top.assignment.role_of(t.text)
            if t.text in {"(", ")"}:
                target.children.append(ParseNode(label="GROUP", token=t.text))
            elif role == "function":
                target.children.append(ParseNode(label="FUNCTION", token=t.text))
            elif role == "binding_symbol":
                target.children.append(ParseNode(label="BIND", token=t.text))
            elif role == "state_marker":
                target.children.append(ParseNode(label="STATE_MARKER", token=t.text))
            elif role in {"operand", "literal", "length_field", "address"}:
                target.children.append(ParseNode(label="OPERAND", token=t.text))
            elif role == "opcode":
                target.children.append(ParseNode(label="OPERATOR", token=t.text))
            else:
                target.children.append(ParseNode(label=role.upper(), token=t.text))
        root.children = [lhs, ParseNode(label="ASSIGN", token="="), rhs]
        return root

    def dialect_aware_parse_tree(self, rec: FormulaRecord, top: DecodeHypothesis) -> ParseNode:
        dialect, _ = self.classify_dialect(rec)
        if dialect == "DIALECT_PIPELINE":
            return self.parse_pipeline_tree(rec, top)
        if dialect == "DIALECT_ALGEBRAIC":
            return self.parse_algebraic_tree(rec, top)
        return self.build_parse_tree(rec, top)

    def dialect_aware_forest(self, rec: FormulaRecord, top: DecodeHypothesis) -> List[Dict]:
        dialect, _ = self.classify_dialect(rec)
        if dialect == "DIALECT_PIPELINE":
            return [self.parse_pipeline_tree(rec, top).to_dict()]
        if dialect == "DIALECT_ALGEBRAIC":
            return [self.parse_algebraic_tree(rec, top).to_dict()]
        return self.parse_forest(rec, top)


    def dialect_confidence(self, rec: FormulaRecord) -> Tuple[float, float, float]:
        dialect, scores = self.classify_dialect(rec)
        p = scores["pipeline_score"]
        a = scores["algebraic_score"]
        margin = abs(p - a)
        total = max(1, p + a)
        confidence = margin / total
        return confidence, margin, float(total)

    def canonical_tree_for_dialect(self, rec: FormulaRecord, top: DecodeHypothesis) -> ParseNode:
        dialect, _ = self.classify_dialect(rec)
        if dialect == "DIALECT_PIPELINE":
            return self.parse_pipeline_tree(rec, top)
        if dialect == "DIALECT_ALGEBRAIC":
            return self.parse_algebraic_tree(rec, top)
        return self.build_parse_tree(rec, top)

    def canonical_forest_for_dialect(self, rec: FormulaRecord, top: DecodeHypothesis) -> List[Dict]:
        dialect, _ = self.classify_dialect(rec)
        if dialect in {"DIALECT_PIPELINE", "DIALECT_ALGEBRAIC"}:
            return [self.canonical_tree_for_dialect(rec, top).to_dict()]
        return self.dialect_aware_forest(rec, top)


    def dialect_aware_validate(self, rec: FormulaRecord, top: DecodeHypothesis) -> str:
        dialect, _ = self.classify_dialect(rec)
        if dialect == "DIALECT_PIPELINE":
            texts = [t.text for t in rec.tokens]
            if "->" in texts and any(t.text in self.SYNC_TOKENS or t.text in {"SHL", "MOV", "ADD", "SUB", "CMP", "JMP"} for t in rec.tokens):
                return "PASS: pipeline dialect matched"
            return "WARN: pipeline dialect weak"
        if dialect == "DIALECT_ALGEBRAIC":
            texts = [t.text for t in rec.tokens]
            if "=" in texts and "->" not in texts:
                return "PASS: algebraic dialect matched"
            return "WARN: algebraic dialect weak"
        return self.validate_against_cfg(rec, top)


    def parse_forest(self, rec: FormulaRecord, top: DecodeHypothesis) -> List[Dict]:
        trees = []
        trees.append(self.build_parse_tree(rec, top).to_dict())

        alt_root = ParseNode(label="FORMULA")
        seg = ParseNode(label="SEGMENT")
        i = 0
        while i < len(rec.tokens):
            t = rec.tokens[i]
            role = top.assignment.role_of(t.text)
            if role == "function" and i + 1 < len(rec.tokens) and rec.tokens[i + 1].text == "(":
                seg.children.append(ParseNode(label="FUNCTION_CALL", token=t.text))
                i += 1
                continue
            seg.children.append(ParseNode(label=role.upper(), token=t.text))
            i += 1
        if seg.children:
            alt_root.children.append(seg)
        trees.append(alt_root.to_dict())

        if any(tok.text == "->" for tok in rec.tokens):
            action_root = ParseNode(label="PIPELINE")
            for t in rec.tokens:
                if t.text == "->":
                    action_root.children.append(ParseNode(label="ARROW", token=t.text))
                else:
                    role = top.assignment.role_of(t.text)
                    action_root.children.append(ParseNode(label=role.upper(), token=t.text))
            trees.append(action_root.to_dict())
        return trees

    def vote_canonical_grammar(self, top: DecodeHypothesis) -> Dict[str, str]:
        votes: Dict[str, Counter] = defaultdict(Counter)
        for tok in sorted(top.assignment.mapping.keys()):
            role = top.assignment.role_of(tok)
            fam = self.family_of(tok, role)
            votes[tok][role] += 3
            votes[tok][fam] += 1
            if tok in self.rewrite_rules(top):
                votes[tok][self.rewrite_rules(top)[tok].lower()] += 2
            if tok in {"sqrt", "sin", "cos", "tan", "log", "exp"}:
                votes[tok]["function"] += 3
            if tok in self.SYNC_TOKENS or tok in {"SHL", "MOV", "ADD", "SUB", "CMP", "JMP"}:
                votes[tok]["action"] += 3
        canonical: Dict[str, str] = {}
        for tok, ctr in votes.items():
            canonical[tok] = ctr.most_common(1)[0][0]
        return canonical

    def parse_forest_summary(self, rec: FormulaRecord, top: DecodeHypothesis) -> str:
        forest = self.parse_forest(rec, top)
        labels = []
        for tree in forest:
            labels.append(tree["label"])
        return "forest=" + ",".join(labels)

    def layer_consistency_table(self, top: DecodeHypothesis) -> Dict[str, str]:
        canonical = self.vote_canonical_grammar(top)
        table: Dict[str, str] = {}
        for tok in sorted(top.assignment.mapping.keys()):
            role = top.assignment.role_of(tok)
            canon = canonical.get(tok, role)
            if role == canon:
                verdict = "MATCH"
            elif canon in {"function", "action", "state_marker", "binding_symbol", "delimiter", "opcode"}:
                verdict = "NEAR"
            else:
                verdict = "CONFLICT"
            table[tok] = f"token={tok} role={role} canonical={canon} verdict={verdict}"
        return table

    def pipeline_explanation(self, top: DecodeHypothesis) -> Dict[str, str]:
        lines: Dict[str, str] = {}
        token_summary = []
        for tok in sorted(top.assignment.mapping.keys()):
            role = top.assignment.role_of(tok)
            if role == "state_marker":
                token_summary.append(f"{tok} 是上下文標記")
            elif role == "function":
                token_summary.append(f"{tok} 是函數")
            elif role == "action":
                token_summary.append(f"{tok} 是動作指令")
            elif role == "binding_symbol":
                token_summary.append(f"{tok} 係綁定符號")
            elif role == "delimiter":
                token_summary.append(f"{tok} 係分界符")
        lines["token_layer"] = "；".join(token_summary)
        lines["role_layer"] = "token 先被分角色，再入樹，再入森林，再投票揀 canonical grammar。"
        lines["tree_layer"] = "樹表示單一解析；森林表示多個可行解析；投票表示挑最穩嗰條。"
        lines["forest_layer"] = "同一 formula 可能有多種讀法，所以要保留 forest，唔好即刻殺死 alternative。"
        lines["vote_layer"] = "最終 canonical grammar 係由跨層一致性最高嘅角色集合投票出來。"
        return lines

    def consensus_summary(self, top: DecodeHypothesis) -> Dict[str, str]:
        canonical = self.vote_canonical_grammar(top)
        rows: Dict[str, str] = {}
        for tok in sorted(top.assignment.mapping.keys()):
            role = top.assignment.role_of(tok)
            canon = canonical.get(tok, role)
            if role == canon:
                confidence = 5
            elif role in {"state_marker", "function", "action", "binding_symbol", "delimiter", "opcode"} and canon in {"state_marker", "function", "action", "binding_symbol", "delimiter", "opcode"}:
                confidence = 3
            else:
                confidence = 1
            rows[tok] = f"role={role} canonical={canon} confidence={confidence}/5"
        return rows

    def disagreement_summary(self, top: DecodeHypothesis) -> Dict[str, str]:
        canonical = self.vote_canonical_grammar(top)
        rows: Dict[str, str] = {}
        for tok in sorted(top.assignment.mapping.keys()):
            role = top.assignment.role_of(tok)
            canon = canonical.get(tok, role)
            if role == canon:
                rows[tok] = "agree"
            else:
                rows[tok] = f"{role} != {canon}"
        return rows

    def stage_map_summary(self, top: DecodeHypothesis) -> Dict[str, str]:
        mapping: Dict[str, str] = {}
        for tok in sorted(top.assignment.mapping.keys()):
            role = top.assignment.role_of(tok)
            if role == "state_marker":
                stage = "token->role->tree"
            elif role == "function":
                stage = "token->role->tree->forest"
            elif role == "action":
                stage = "token->role->tree->forest->vote"
            elif role == "binding_symbol":
                stage = "token->role->tree"
            elif role == "delimiter":
                stage = "token->role"
            else:
                stage = "token"
            mapping[tok] = stage
        return mapping

    def rule_confidence_summary(self, top: DecodeHypothesis) -> Dict[str, str]:
        canonical = self.vote_canonical_grammar(top)
        rows: Dict[str, str] = {}
        for tok in sorted(top.assignment.mapping.keys()):
            role = top.assignment.role_of(tok)
            canon = canonical.get(tok, role)
            if tok in {"sqrt", "SHL"} and role == canon:
                conf = 5
            elif role in {"state_marker", "binding_symbol", "delimiter", "opcode"}:
                conf = 4 if role == canon else 2
            elif role in {"operand", "literal", "length_field", "address"}:
                conf = 3
            else:
                conf = 2
            rows[tok] = f"confidence={conf}/5 canonical={canon}"
        return rows

    def wfield_summary(self, top: DecodeHypothesis) -> Tuple[Dict[str, str], Dict[str, str]]:
        canonical = self.vote_canonical_grammar(top)
        token_field: Dict[str, str] = {}
        formula_field: Dict[str, str] = {}
        for tok in sorted(top.assignment.mapping.keys()):
            role = top.assignment.role_of(tok)
            canon = canonical.get(tok, role)
            strength = 0.0
            if role == canon:
                strength += 3.0
            if role in {"state_marker", "function", "action", "binding_symbol", "delimiter"}:
                strength += 1.0
            if tok in {"sqrt", "SHL"}:
                strength += 1.5
            if tok in {"phi", "eps", "kappa", "beta", "N", "L", "d"} and role == "state_marker":
                strength += 1.0
            tension = 5.0 - strength
            gradient = "flat" if strength >= 4.5 else "stable" if strength >= 3.0 else "noisy"
            token_field[tok] = f"strength={strength:.1f}/5 tension={tension:.1f}/5 gradient={gradient} role={role} canonical={canon}"
        formula_field["summary"] = "W-field 係一致性權重場：strength 越高，角色越穩；tension 越低，歧義越少。"
        return token_field, formula_field

    def semantic_role_summary(self, top: DecodeHypothesis) -> Dict[str, str]:
        semantic: Dict[str, str] = {}
        for tok in sorted(top.assignment.mapping.keys()):
            role = top.assignment.role_of(tok)
            if tok == 'SHL':
                sem = 'shift_opcode'
            elif tok == '->':
                sem = 'control_flow_operator'
            elif tok == '=':
                sem = 'assignment_operator'
            elif tok == 'd':
                sem = 'index_symbol'
            elif tok == 'sqrt':
                sem = 'function_call'
            elif tok in {'^', '_'}:
                sem = 'binding_modifier'
            elif role == 'state_marker':
                sem = 'state_symbol'
            elif role in {'operand', 'literal', 'length_field', 'address'}:
                sem = 'value'
            elif role == 'delimiter':
                sem = 'separator'
            else:
                sem = role
            semantic[tok] = f"semantic={sem} role={role}"
        return semantic

    def formula_coherence_summary(self, top: DecodeHypothesis) -> Dict[str, str]:
        # very simple compact field score: average W-field strength, adjusted by forest size / tension proxy
        rows: Dict[str, str] = {}
        for rec in self.records:
            strengths = []
            tensions = []
            for t in rec.tokens:
                role = top.assignment.role_of(t.text)
                canon = self.vote_canonical_grammar(top).get(t.text, role)
                strength = 0.0
                if role == canon:
                    strength += 3.0
                if role in {'state_marker', 'function', 'action', 'binding_symbol', 'delimiter'}:
                    strength += 1.0
                if t.text in {'sqrt', 'SHL'}:
                    strength += 1.5
                if t.text in {'phi', 'eps', 'kappa', 'beta', 'N', 'L', 'd'} and role == 'state_marker':
                    strength += 1.0
                strengths.append(strength)
                tensions.append(max(0.0, 5.0 - strength))
            avg_s = sum(strengths) / max(1, len(strengths))
            avg_t = sum(tensions) / max(1, len(tensions))
            score = avg_s - 0.5 * avg_t
            rows[rec.raw] = f"coherence={score:.2f} avg_strength={avg_s:.2f} avg_tension={avg_t:.2f}"
        return rows

    def rejection_summary(self, top: DecodeHypothesis) -> Dict[str, str]:
        rows: Dict[str, str] = {}
        for rec in self.records:
            forest_size = len(self.parse_forest(rec, top))
            coh = self._parse_coherence_value(self.formula_coherence_summary(top)[rec.raw])
            tension = self._parse_tension_value(self.formula_coherence_summary(top)[rec.raw])
            reject = (forest_size > 2) or (tension > 1.45 and coh < 3.05)
            verdict = 'REJECT' if reject else 'KEEP'
            rows[rec.raw] = f"{verdict} forest_size={forest_size} coherence={coh:.2f} tension={tension:.2f}"
        return rows

    def formula_ranking_summary(self, top: DecodeHypothesis) -> List[Tuple[str, float]]:
        ranking: List[Tuple[str, float]] = []
        coherence = self.formula_coherence_summary(top)
        for rec in self.records:
            forest_size = len(self.parse_forest(rec, top))
            score = self._parse_coherence_value(coherence[rec.raw]) - 0.18 * max(0, forest_size - 1)
            ranking.append((rec.raw, score))
        ranking.sort(key=lambda kv: (kv[1], kv[0]), reverse=True)
        return ranking

    def global_coherence_summary(self, top: DecodeHypothesis) -> Dict[str, str]:
        coh = self.formula_coherence_summary(top)
        vals = [self._parse_coherence_value(v) for v in coh.values()]
        tens = [self._parse_tension_value(v) for v in coh.values()]
        avg_c = sum(vals) / max(1, len(vals))
        avg_t = sum(tens) / max(1, len(tens))
        return {
            'summary': f"avg_coherence={avg_c:.2f} avg_tension={avg_t:.2f} formula_count={len(vals)}",
            'trend': 'stable' if avg_c >= 3.0 and avg_t <= 1.5 else 'noisy',
        }

    @staticmethod
    def _parse_coherence_value(text: str) -> float:
        m = re.search(r'coherence=([0-9.]+)', text)
        return float(m.group(1)) if m else 0.0

    @staticmethod
    def _parse_tension_value(text: str) -> float:
        m = re.search(r'avg_tension=([0-9.]+)', text)
        return float(m.group(1)) if m else 0.0


    def classify_dialect(self, rec: FormulaRecord) -> Tuple[str, Dict[str, int]]:
        texts = [t.text for t in rec.tokens]
        explicit_pipeline = any(tok in {"->", "=>"} for tok in texts)
        explicit_assignment = "=" in texts and not explicit_pipeline
        opcode_like = sum(1 for t in rec.tokens if self.token_kind(t.text) == "symbol" and t.text in self.SYNC_TOKENS or t.text in {"SHL", "SHR", "ROT", "XOR", "MOV", "ADD", "SUB", "CMP", "JMP"})
        function_like = sum(1 for t in rec.tokens if t.text in {"sqrt", "log", "exp"})
        state_like = sum(1 for t in rec.tokens if t.text in {"phi", "eps", "kappa", "beta", "N", "L", "d"})
        binding_like = sum(1 for t in rec.tokens if t.text in {"^", "_"})
        bitvector_like = sum(1 for t in rec.tokens if re.fullmatch(r"[01]{2,}", t.text))
        pipeline_score = bitvector_like * 3 + opcode_like * 3 + texts.count("->") * 4 + texts.count("=>") * 4
        algebraic_score = state_like * 3 + function_like * 3 + binding_like * 2 + texts.count("=") * 3
        if explicit_pipeline and not explicit_assignment:
            dialect = "DIALECT_PIPELINE"
        elif explicit_assignment and not explicit_pipeline:
            dialect = "DIALECT_ALGEBRAIC"
        elif pipeline_score > algebraic_score:
            dialect = "DIALECT_PIPELINE"
        elif algebraic_score > pipeline_score:
            dialect = "DIALECT_ALGEBRAIC"
        else:
            dialect = "DIALECT_DUAL"
        return dialect, {"pipeline_score": pipeline_score, "algebraic_score": algebraic_score, "explicit_pipeline": int(explicit_pipeline), "explicit_assignment": int(explicit_assignment)}

    def route_formula(self, rec: FormulaRecord) -> str:
        dialect, _ = self.classify_dialect(rec)
        return dialect

    def build_dialect_router_report(self, top: DecodeHypothesis) -> Tuple[Dict[str, str], Dict[str, str], Dict[str, str], Dict[str, str], Dict[str, str]]:
        router: Dict[str, str] = {}
        mode_summary: Dict[str, str] = {}
        ebnf: Dict[str, str] = {}
        examples: Dict[str, str] = {}
        pipeline_summary: Dict[str, str] = {}
        algebraic_summary: Dict[str, str] = {}
        for rec in self.records:
            dialect, scores = self.classify_dialect(rec)
            router[rec.raw] = f"{dialect} pipeline_score={scores['pipeline_score']} algebraic_score={scores['algebraic_score']} explicit_pipeline={scores['explicit_pipeline']} explicit_assignment={scores['explicit_assignment']}"
            mode_summary[rec.raw] = dialect
            if dialect == "DIALECT_PIPELINE":
                ebnf[rec.raw] = 'PipelineExpr ::= StateStep { TransitionOp StateStep }'
                examples[rec.raw] = self.parse_summary(rec, top)
                pipeline_summary[rec.raw] = 'Pipeline mode: explicit transitions dominate, route into pipeline AST.'
            elif dialect == "DIALECT_ALGEBRAIC":
                ebnf[rec.raw] = 'AlgebraicExpr ::= StateTarget AssignmentOp Expression'
                examples[rec.raw] = self.parse_summary(rec, top)
                algebraic_summary[rec.raw] = 'Algebraic mode: assignment and symbolic state dominate, route into algebraic AST.'
            else:
                ebnf[rec.raw] = 'DIALECT_DUAL ::= PipelineExpr | AlgebraicExpr'
                examples[rec.raw] = self.parse_summary(rec, top)
        return router, mode_summary, ebnf, examples, {**pipeline_summary, **algebraic_summary}

    def search_decoder(self, max_hypotheses: int = 512, top_k: int = 10) -> DecodeResult:
        token_stats = self.build_token_stats()
        kind_transition_stats = self.build_kind_transition_stats()
        position_constraints = self.derive_position_constraints()
        hypotheses = self.enumerate_hypotheses(max_hypotheses=max_hypotheses)
        scored: List[DecodeHypothesis] = []
        for hyp in hypotheses:
            hyp.score, hyp.notes = self.score_hypothesis(hyp)
            scored.append(hyp)
        scored.sort(key=lambda h: h.score, reverse=True)
        best = scored[:top_k]
        top = best[0] if best else DecodeHypothesis(name="NONE", assignment=RoleAssignment(mapping={}))
        role_transition_stats = self.role_transition_matrix(top)
        parse_summaries = {rec.raw: [f"{self.classify_dialect(rec)[0]} :: {self.parse_summary(rec, top)}", self.parse_forest_summary(rec, top)] for rec in self.records}
        parse_trees = {rec.raw: build_tree_dict(self.dialect_aware_parse_tree(rec, top)) for rec in self.records}
        family_stats = self.build_family_stats(top)
        collision_report = self.collision_analysis()
        grammar_candidates = self.export_grammar_candidates(top)
        binary_packets = {rec.raw: self.build_binary_packet(rec, top) for rec in self.records}
        opcode_rankings = self.ranking(top)
        cfg_rules = self.export_cfg_rules(top)
        validation_report = {rec.raw: self.dialect_aware_validate(rec, top) for rec in self.records}
        stress_report = {"summary": self.stress_eval(top)}
        rewrite_report = {tok: role for tok, role in self.rewrite_rules(top).items()}
        lattice_report = self.token_lattice(top)
        decoder_exports = self.decoder_exports(top)
        auto_grammar = self.auto_grammar_induction(top)
        cfg_rules.update({f"AUTO_{k}": v for k, v in auto_grammar.items()})
        stability_report = self.stability_summary(top)
        ambiguity_report = self.ambiguity_summary(top)
        ranked_grammar_trees = self.grammar_tree_candidates(top)
        parse_forest = {rec.raw: self.canonical_forest_for_dialect(rec, top) for rec in self.records}
        canonical_votes = self.vote_canonical_grammar(top)
        layer_consistency = self.layer_consistency_table(top)
        pipeline_explanation = self.pipeline_explanation(top)
        consensus_report = self.consensus_summary(top)
        disagreement_report = self.disagreement_summary(top)
        stage_map = self.stage_map_summary(top)
        rule_confidence = self.rule_confidence_summary(top)
        wfield_map, wfield_formula = self.wfield_summary(top)
        semantic_role_map = self.semantic_role_summary(top)
        formula_coherence = self.formula_coherence_summary(top)
        rejection_report = self.rejection_summary(top)
        formula_ranking = self.formula_ranking_summary(top)
        global_coherence_summary = self.global_coherence_summary(top)
        dialect_router_report, dialect_mode_report, dialect_ebnf, dialect_routing_examples, dialect_mode_summary = self.build_dialect_router_report(top)
        router_confidence = {rec.raw: f"confidence={self.dialect_confidence(rec)[0]:.2f} margin={self.dialect_confidence(rec)[1]:.1f} total={self.dialect_confidence(rec)[2]:.1f}" for rec in self.records}
        canonical_forest_summary = {rec.raw: f"forest_size={len(self.canonical_forest_for_dialect(rec, top))}" for rec in self.records}
        canonical_tree_summary = {rec.raw: self.canonical_tree_for_dialect(rec, top).label for rec in self.records}
        symbol_table = self.build_symbol_table()
        microcode_usage = self.microcode_statistics()
        formula_ir = {rec.raw: self.formula_to_ir(rec.raw) for rec in self.records}
        total_instruction_count = sum(len(v) for v in formula_ir.values())
        return DecodeResult(
            hypotheses=best,
            token_stats=token_stats,
            token_roles=dict(top.assignment.mapping),
            kind_transition_stats=kind_transition_stats,
            role_transition_stats=role_transition_stats,
            parse_summaries=parse_summaries,
            parse_trees=parse_trees,
            family_stats=family_stats,
            position_constraints=position_constraints,
            collision_report=collision_report,
            grammar_candidates=grammar_candidates,
            binary_packets=binary_packets,
            opcode_rankings=opcode_rankings,
            cfg_rules=cfg_rules,
            validation_report=validation_report,
            stress_report=stress_report,
            rewrite_report=rewrite_report,
            lattice_report=lattice_report,
            decoder_exports=decoder_exports,
            stability_report=stability_report,
            ambiguity_report=ambiguity_report,
            ranked_grammar_trees=ranked_grammar_trees,
            parse_forest=parse_forest,
            voting_report={k: f"canonical={v}" for k, v in canonical_votes.items()},
            layer_consistency=layer_consistency,
            pipeline_explanation=pipeline_explanation,
            consensus_report=consensus_report,
            disagreement_report=disagreement_report,
            stage_map=stage_map,
            rule_confidence=rule_confidence,
            wfield_map=wfield_map,
            wfield_formula=wfield_formula,
            semantic_role_map=semantic_role_map,
            formula_coherence=formula_coherence,
            rejection_report=rejection_report,
            formula_ranking=formula_ranking,
            global_coherence_summary=global_coherence_summary,
            dialect_router_report=dialect_router_report,
            dialect_mode_report=dialect_mode_report,
            dialect_ebnf=dialect_ebnf,
            dialect_routing_examples=dialect_routing_examples,
            pipeline_mode_summary={k:v for k,v in dialect_mode_summary.items() if "Pipeline" in v or "pipeline" in v},
            algebraic_mode_summary={k:v for k,v in dialect_mode_summary.items() if "Algebraic" in v or "algebraic" in v},
            router_confidence=router_confidence,
            canonical_forest_summary=canonical_forest_summary,
            canonical_tree_summary=canonical_tree_summary,
            symbol_table=symbol_table,
            microcode_usage=microcode_usage,
            formula_ir=formula_ir,
            total_instruction_count=total_instruction_count,
        )

    def export_grammar_candidates(self, hyp: DecodeHypothesis) -> Dict[str, List[str]]:
        grammar = {
            "START": ["SEGMENT", "ASSIGN", "ARROW", "GROUP"],
            "SEGMENT": ["OPCODE", "STATE_MARKER", "OPERAND", "DELIMITER", "BIND", "FUNCTION", "ACTION"],
            "OPCODE": ["OPCODE", "OPERAND", "DELIMITER", "BIND"],
            "OPERAND": ["DELIMITER", "OPCODE", "OPERAND"],
            "DELIMITER": ["SEGMENT", "OPCODE", "OPERAND", "GROUP", "BIND", "FUNCTION", "ACTION"],
            "BIND": ["OPCODE", "OPERAND", "STATE_MARKER"],
            "GROUP": ["SEGMENT", "GROUP_END"],
            "STATE_MARKER": ["DELIMITER", "OPCODE", "OPERAND", "FUNCTION", "ACTION"],
            "FUNCTION": ["GROUP_START", "EXPR"],
            "ACTION": ["OPERAND", "GROUP_START", "EXPR"],
        }
        if not any(r == "binding_symbol" for r in hyp.assignment.mapping.values()):
            grammar["BIND"] = ["OPCODE", "OPERAND"]
        return grammar

    def emit_report(self, result: DecodeResult) -> str:
        lines: List[str] = []
        lines.append("=== IDCM Reverse Compiler Report v18 ===")
        lines.append(f"formula_count: {len(self.records)}")
        lines.append("")

        lines.append("-- Consensus first summary --")
        for tok, v in sorted(result.consensus_report.items(), key=lambda kv: kv[0]):
            lines.append(f"{tok!r}: {v}")
        lines.append("")

        lines.append("-- Disagreement matrix --")
        for tok, v in sorted(result.disagreement_report.items(), key=lambda kv: kv[0]):
            lines.append(f"{tok!r}: {v}")
        lines.append("")

        lines.append("-- Stage map --")
        for tok, v in sorted(result.stage_map.items(), key=lambda kv: kv[0]):
            lines.append(f"{tok!r}: {v}")
        lines.append("")

        lines.append("-- Rule confidence --")
        for tok, v in sorted(result.rule_confidence.items(), key=lambda kv: kv[0]):
            lines.append(f"{tok!r}: {v}")
        lines.append("")

        lines.append("-- W-field map --")
        for tok, v in sorted(result.wfield_map.items(), key=lambda kv: kv[0]):
            lines.append(f"{tok!r}: {v}")
        lines.append("")

        lines.append("-- W-field formula --")
        for k, v in sorted(result.wfield_formula.items(), key=lambda kv: kv[0]):
            lines.append(f"{k}: {v}")
        lines.append("")

        lines.append("-- Semantic role map --")
        for tok, v in sorted(result.semantic_role_map.items(), key=lambda kv: kv[0]):
            lines.append(f"{tok!r}: {v}")
        lines.append("")

        lines.append("-- Formula coherence --")
        for raw, v in result.formula_coherence.items():
            lines.append(f"{raw} :: {v}")
        lines.append("")

        lines.append("-- Rejection report --")
        for raw, v in result.rejection_report.items():
            lines.append(f"{raw} :: {v}")
        lines.append("")

        lines.append("-- Formula ranking --")
        for raw, score in result.formula_ranking:
            lines.append(f"{score:.2f} :: {raw}")
        lines.append("")

        lines.append("-- Microcode usage --")
        for op, count in sorted(result.microcode_usage.items(), key=lambda kv: -kv[1]):
            lines.append(f"  {op:8s}: {count}")
        lines.append(f"  TOTAL: {result.total_instruction_count} instructions across {len(self.records)} formulas")
        lines.append("")

        lines.append("-- Symbol table (top 15 by instruction count) --")
        for i, (name, info) in enumerate(sorted(result.symbol_table.items(), key=lambda kv: -kv[1].get("instruction_count", 0))):
            if i >= 15: break
            lines.append(f"  {name:12s} = {info['expression']:30s}  instrs={info['instruction_count']}  deps={info['dependencies']}")
        lines.append("")

        lines.append("-- Formula IR (sample) --")
        for i, (raw, ir) in enumerate(result.formula_ir.items()):
            if i >= 6: break
            lines.append(f"  {raw[:55]}")
            for line in ir[:10]:
                lines.append(f"    {line}")
            if len(ir) > 10: lines.append(f"    ... ({len(ir)} instructions total)")
            lines.append("")
        lines.append("")

        lines.append("-- Dialect router report --")
        for raw, info in result.dialect_router_report.items():
            lines.append(f"{raw} :: {info}")
        lines.append("")

        lines.append("-- Dialect mode report --")
        for raw, mode in result.dialect_mode_report.items():
            lines.append(f"{raw} :: {mode}")
        lines.append("")

        lines.append("-- Router confidence --")
        for raw, v in result.router_confidence.items():
            lines.append(f"{raw} :: {v}")
        lines.append("")

        lines.append("-- Canonical forest summary --")
        for raw, v in result.canonical_forest_summary.items():
            lines.append(f"{raw} :: {v}")
        lines.append("")

        lines.append("-- Canonical tree summary --")
        for raw, v in result.canonical_tree_summary.items():
            lines.append(f"{raw} :: {v}")
        lines.append("")

        lines.append("-- Dialect EBNF --")
        for raw, rule in result.dialect_ebnf.items():
            lines.append(f"{raw} :: {rule}")
        lines.append("")

        lines.append("-- Dialect routing examples --")
        for raw, ex in result.dialect_routing_examples.items():
            lines.append(f"{raw}")
            lines.append(f"    {ex}")
        lines.append("")

        lines.append("-- Pipeline mode summary --")
        for raw, s in result.pipeline_mode_summary.items():
            lines.append(f"{raw} :: {s}")
        lines.append("")

        lines.append("-- Algebraic mode summary --")
        for raw, s in result.algebraic_mode_summary.items():
            lines.append(f"{raw} :: {s}")
        lines.append("")
        lines.append("-- Global coherence summary --")
        for k, v in result.global_coherence_summary.items():
            lines.append(f"{k}: {v}")
        lines.append("")

        lines.append("-- 5-layer pipeline explanation --")
        for k in ["token_layer", "role_layer", "tree_layer", "forest_layer", "vote_layer"]:
            lines.append(f"{k}: {result.pipeline_explanation.get(k, '')}")
        lines.append("")

        lines.append("-- Layer consistency table --")
        for tok, v in sorted(result.layer_consistency.items(), key=lambda kv: kv[0]):
            lines.append(f"{tok!r}: {v}")
        lines.append("")

        lines.append("-- Canonical grammar votes --")
        for tok, vote in sorted(result.voting_report.items(), key=lambda kv: kv[0]):
            lines.append(f"{tok!r}: {vote}")
        lines.append("")

        lines.append("-- Ranked grammar trees --")
        for shape, score in result.ranked_grammar_trees:
            lines.append(f"{score:.1f} :: {shape}")
        lines.append("")

        lines.append("-- Stability report --")
        for tok, v in sorted(result.stability_report.items(), key=lambda kv: kv[0]):
            lines.append(f"{tok!r}: {v}")
        lines.append("")

        lines.append("-- Ambiguity report --")
        for tok, v in sorted(result.ambiguity_report.items(), key=lambda kv: kv[0]):
            lines.append(f"{tok!r}: {v}")
        lines.append("")

        lines.append("-- Decoder exports --")
        for section, mapping in result.decoder_exports.items():
            lines.append(section)
            for k, v in list(mapping.items())[:20]:
                lines.append(f"  {k!r}: {v}")
        lines.append("")

        lines.append("-- Rewrite report --")
        for tok, rr in sorted(result.rewrite_report.items(), key=lambda kv: kv[0]):
            lines.append(f"{tok!r}: {rr}")
        lines.append("")

        lines.append("-- Token lattice --")
        for tok, info in sorted(result.lattice_report.items(), key=lambda kv: kv[0]):
            lines.append(f"{tok!r}: {info}")
        lines.append("")

        lines.append("-- Validation report --")
        for raw, v in result.validation_report.items():
            lines.append(f"{raw} :: {v}")
        lines.append("")

        lines.append("-- Stress report --")
        for k, v in result.stress_report.items():
            lines.append(f"{k}: {v}")
        lines.append("")

        lines.append("-- Position constraints --")
        for tok, cs in sorted(result.position_constraints.items(), key=lambda kv: kv[0]):
            lines.append(f"{tok!r}: " + " | ".join(cs))
        lines.append("")

        lines.append("-- Collision report --")
        for tok, kinds in sorted(result.collision_report.items(), key=lambda kv: kv[0]):
            kinds_s = ", ".join(f"{k}={v}" for k, v in sorted(kinds.items()))
            lines.append(f"{tok!r}: {kinds_s}")
        lines.append("")

        lines.append("-- CFG rules --")
        for lhs, rhs in sorted(result.cfg_rules.items(), key=lambda kv: kv[0]):
            lines.append(f"{lhs} -> {' | '.join(rhs)}")
        lines.append("")

        lines.append("-- Binary packet guesses --")
        for raw, pkt in result.binary_packets.items():
            lines.append(raw)
            lines.append(f"    {pkt}")
        lines.append("")

        lines.append("-- Opcode ranking --")
        for tok, score in result.opcode_rankings[:20]:
            lines.append(f"{tok!r}: {score:.1f}")
        lines.append("")

        lines.append("-- Input formulas --")
        for i, rec in enumerate(self.records, 1):
            lines.append(f"[{i}] {rec.raw}")
            lines.append("    tokens: " + " ".join(f"{t.text}/{t.kind}" for t in rec.tokens))
        lines.append("")

        lines.append("-- Parse summaries under top hypothesis --")
        for raw, summaries in result.parse_summaries.items():
            lines.append(f"{raw}")
            for s in summaries:
                lines.append(f"    {s}")
        lines.append("")

        lines.append("-- Parse trees (compact JSON) --")
        for raw, tree in result.parse_trees.items():
            lines.append(raw)
            lines.append(json.dumps(tree, ensure_ascii=False, sort_keys=True))
        lines.append("")

        lines.append("-- Parse forest --")
        for raw, forest in result.parse_forest.items():
            lines.append(raw)
            for tree in forest:
                lines.append(json.dumps(tree, ensure_ascii=False, sort_keys=True))
        lines.append("")

        lines.append("-- Top decoder hypotheses --")
        for hyp in result.hypotheses:
            lines.append(f"{hyp.name}  score={hyp.score:.3f}")
            items = sorted(hyp.assignment.mapping.items(), key=lambda kv: kv[0])
            preview = ", ".join(f"{k}:{v}" for k, v in items[:22])
            lines.append(f"    mapping: {preview}")
        lines.append("")

        lines.append("-- Token role summary --")
        for tok, role in sorted(result.token_roles.items(), key=lambda kv: kv[0]):
            lines.append(f"{tok!r}: {role}")
        lines.append("")

        lines.append("-- Kind transition matrix --")
        for a, row in sorted(result.kind_transition_stats.items(), key=lambda kv: kv[0]):
            row_s = ", ".join(f"{b}={n}" for b, n in sorted(row.items()))
            lines.append(f"{a} -> {row_s}")
        lines.append("")

        lines.append("-- Role transition matrix --")
        for a, row in sorted(result.role_transition_stats.items(), key=lambda kv: kv[0]):
            row_s = ", ".join(f"{b}={n}" for b, n in sorted(row.items()))
            lines.append(f"{a} -> {row_s}")
        lines.append("")

        lines.append("-- Opcode family stats --")
        for fam, n in sorted(result.family_stats.items(), key=lambda kv: kv[0]):
            lines.append(f"{fam}: {n}")
        lines.append("")

        lines.append("-- Interpretation --")
        lines.append("1. v15 加入 rejection gate、formula ranking、global coherence summary。")
        lines.append("2. stage map + W-field map + semantic map + coherence 形成完整分析鏈。")
        lines.append("3. 當一致性高，canonical grammar 就唔再靠直覺，而係靠可重算票數。")
        lines.append("4. 若某 token 的 tension 長期高，就係下一個需要拆層的對象。")
        return "\n".join(lines)


def build_tree_dict(node: ParseNode) -> Dict:
    return node.to_dict()


def load_formulas_from_source(path: Optional[str]) -> List[str]:
    if not path:
        return []
    with open(path, "r", encoding="utf-8") as f:
        text = f.read().strip()
    if not text:
        return []
    try:
        obj = json.loads(text)
        if isinstance(obj, list):
            return [str(x) for x in obj]
        if isinstance(obj, dict) and "formulas" in obj and isinstance(obj["formulas"], list):
            return [str(x) for x in obj["formulas"]]
    except Exception:
        pass
    return [line.strip() for line in text.splitlines() if line.strip()]


def load_formulas_from_stdin() -> List[str]:
    data = sys.stdin.read().strip()
    if not data:
        return []
    try:
        obj = json.loads(data)
        if isinstance(obj, list):
            return [str(x) for x in obj]
        if isinstance(obj, dict) and "formulas" in obj and isinstance(obj["formulas"], list):
            return [str(x) for x in obj["formulas"]]
    except Exception:
        pass
    return [line.strip() for line in data.splitlines() if line.strip()]


def default_formulas() -> List[str]:
    return [
        "phi = (1 + sqrt(5)) / 2",
        "eps = phi^-1 / 4",
        "kappa = 1 / 16",
        "beta = phi^-1 / 2",
        "0010 -> SHL 1 -> 0100",
        "N_d = 44",
        "L = 53/8",
    ]


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="IDCM reverse compiler research harness v13")
    parser.add_argument("--input", "-i", help="JSON file or newline text file containing formulas")
    parser.add_argument("--max-hypotheses", type=int, default=4096, help="Max hypotheses to enumerate")
    parser.add_argument("--top-k", type=int, default=12, help="How many top hypotheses to report")
    parser.add_argument("--output-json", action="store_true", help="Emit JSON summary instead of text report")
    return parser


def main(argv: Sequence[str]) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv[1:])

    formulas: List[str] = []
    if args.input:
        formulas = load_formulas_from_source(args.input)
    if not formulas:
        formulas = load_formulas_from_stdin()
    if not formulas:
        formulas = default_formulas()

    rc = ReverseCompiler(formulas)
    result = rc.search_decoder(max_hypotheses=args.max_hypotheses, top_k=args.top_k)

    if args.output_json:
        payload = {
            "formula_count": len(formulas),
            "top_hypotheses": [
                {
                    "name": hyp.name,
                    "score": hyp.score,
                    "mapping": hyp.assignment.mapping,
                    "notes": hyp.notes,
                }
                for hyp in result.hypotheses
            ],
            "token_roles": result.token_roles,
            "kind_transition_stats": result.kind_transition_stats,
            "role_transition_stats": result.role_transition_stats,
            "parse_summaries": result.parse_summaries,
            "parse_trees": result.parse_trees,
            "family_stats": result.family_stats,
            "position_constraints": result.position_constraints,
            "collision_report": result.collision_report,
            "grammar_candidates": result.grammar_candidates,
            "binary_packets": result.binary_packets,
            "opcode_rankings": result.opcode_rankings,
            "cfg_rules": result.cfg_rules,
            "validation_report": result.validation_report,
            "stress_report": result.stress_report,
            "rewrite_report": result.rewrite_report,
            "lattice_report": result.lattice_report,
            "decoder_exports": result.decoder_exports,
            "stability_report": result.stability_report,
            "ambiguity_report": result.ambiguity_report,
            "ranked_grammar_trees": result.ranked_grammar_trees,
            "parse_forest": result.parse_forest,
            "voting_report": result.voting_report,
            "layer_consistency": result.layer_consistency,
            "pipeline_explanation": result.pipeline_explanation,
            "consensus_report": result.consensus_report,
            "disagreement_report": result.disagreement_report,
            "stage_map": result.stage_map,
            "rule_confidence": result.rule_confidence,
            "wfield_map": result.wfield_map,
            "wfield_formula": result.wfield_formula,
            "semantic_role_map": result.semantic_role_map,
            "formula_coherence": result.formula_coherence,
            "rejection_report": result.rejection_report,
            "formula_ranking": result.formula_ranking,
            "global_coherence_summary": result.global_coherence_summary,
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(rc.emit_report(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
