#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IDCM 逆向編譯器 v9

新增：
- function call subtree parsing
- stricter 4-way split: opcode / state / function / binding
- stability-ranked grammar tree export
- decoder hypothesis ranking by structural consistency
- more explicit candidate grammar tree

定位：
- 進一步逼近唯一 grammar
- 將函數呼叫從普通 segment 拆出
- 讓 parse tree 更像真正 compiler AST
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import product
from collections import Counter, defaultdict
import argparse
import json
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


class ReverseCompiler:
    def __init__(self, formulas: Sequence[str]):
        self.records = [FormulaRecord(raw=f, tokens=self.tokenize(f)) for f in formulas]

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

    def build_kind_transition_stats(self) -> Dict[str, Dict[str, int]]:
        stats: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for rec in self.records:
            kinds = [t.kind for t in rec.tokens]
            for a, b in zip(kinds, kinds[1:]):
                stats[a][b] += 1
        return {k: dict(v) for k, v in stats.items()}

    @staticmethod
    def classify_token_candidates(token: str) -> List[str]:
        if re.fullmatch(r"\d+\.\d+|\d+", token):
            return ["operand", "literal", "length_field", "address"]
        if re.fullmatch(r"[A-Za-zα-ωΑ-Ω]+", token):
            if token in {"sqrt", "sin", "cos", "tan", "log", "exp"}:
                return ["function", "opcode"]
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
            score += 2.1 if role == "function" else 1.8 if role in {"state_marker", "binding_symbol"} else 0.2 if role == "opcode" else -0.3
        elif token.kind in {"group", "separator"}:
            score += 3.0 if role == "delimiter" else -1.5
        elif token.kind == "binding":
            score += 3.0 if role == "binding_symbol" else -1.0
        elif token.kind == "operator":
            score += 2.0 if role in {"delimiter", "opcode", "control_flag"} else -0.5

        if token.text in {"=", "->", "=>"} and role == "delimiter":
            score += 2.5
        if token.text in {"^", "_"} and role == "binding_symbol":
            score += 2.5
        if token.text in {"(", ")", "[", "]", "{", "}"} and role == "delimiter":
            score += 2.5
        if token.text in {"sqrt", "sin", "cos", "tan", "log", "exp"} and role == "function":
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

        # function call split: function name followed by group becomes FUNCTION_CALL subtree
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
                # if previous token was function, reframe as function-call
                prev_tok = rec.tokens[i - 1] if i > 0 else None
                if prev_tok and hyp.assignment.role_of(prev_tok.text) == "function":
                    node = ParseNode(label="FUNCTION_CALL", token=prev_tok.text)
                    current.children.pop() if current.children else None
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
                if role in {"delimiter", "binding_symbol", "state_marker", "function"}:
                    counts[t.text] += 2
                elif fam in {"separator", "binding", "state", "function"}:
                    counts[t.text] += 1.5
                elif role in {"operand", "literal", "length_field", "address"}:
                    counts[t.text] += 1.0
        ranked = sorted(counts.items(), key=lambda kv: (kv[1], kv[0]), reverse=True)
        return [(k, float(v)) for k, v in ranked]

    def export_cfg_rules(self, top: DecodeHypothesis) -> Dict[str, List[str]]:
        cfg = {
            "FORMULA": ["LHS ASSIGN RHS", "PIPELINE"],
            "LHS": ["STATE_MARKER", "OPCODE", "BIND_CHAIN", "FUNCTION_CALL"],
            "RHS": ["SEGMENT", "PIPELINE", "EXPR"],
            "EXPR": ["OPERAND OPERATOR OPERAND", "STATE_MARKER BIND_CHAIN", "FUNCTION_CALL", "GROUP"],
            "PIPELINE": ["SEGMENT ARROW SEGMENT", "SEGMENT ARROW SEGMENT ARROW SEGMENT"],
            "BIND_CHAIN": ["STATE_MARKER BIND STATE_MARKER", "STATE_MARKER BIND OPERAND"],
            "FUNCTION_CALL": ["FUNCTION GROUP_START EXPR GROUP_END"],
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
            "SHL": "STATE_MARKER",
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
            if role == "state_marker" and tok in rules:
                normalized[tok] = rules[tok]
            elif role == "binding_symbol" and tok in rules:
                normalized[tok] = rules[tok]
            elif role == "delimiter" and tok in rules:
                normalized[tok] = rules[tok]
            elif role == "function" and tok in rules:
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
            if role in {"delimiter", "binding_symbol", "state_marker", "function"}:
                score += 2
            if kind in {"operator", "group"} and role == "delimiter":
                score += 1
            if role == "state_marker" and tok in {"phi", "eps", "kappa", "beta", "N", "L", "SHL"}:
                score += 2
            if role == "function" and tok in {"sqrt", "sin", "cos", "tan", "log", "exp"}:
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
        # ranked grammar-tree shapes from the top hypothesis and auto induction
        auto = self.auto_grammar_induction(top)
        trees: List[Tuple[str, float]] = []
        for lhs, rhs_list in auto.items():
            for rhs in rhs_list:
                shape = f"{lhs} -> {rhs}"
                score = 0.0
                if "FUNCTION" in rhs:
                    score += 3.0
                if "BINDING" in rhs or "BIND" in rhs:
                    score += 2.0
                if "STATE" in rhs:
                    score += 1.5
                if "SEPARATOR" in rhs:
                    score += 1.0
                trees.append((shape, score))
        trees.sort(key=lambda kv: (kv[1], kv[0]), reverse=True)
        return trees[:20]

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
        parse_summaries = {rec.raw: [self.parse_summary(rec, top)] for rec in self.records}
        parse_trees = {rec.raw: build_tree_dict(self.build_parse_tree(rec, top)) for rec in self.records}
        family_stats = self.build_family_stats(top)
        collision_report = self.collision_analysis()
        grammar_candidates = self.export_grammar_candidates(top)
        binary_packets = {rec.raw: self.build_binary_packet(rec, top) for rec in self.records}
        opcode_rankings = self.ranking(top)
        cfg_rules = self.export_cfg_rules(top)
        validation_report = {rec.raw: self.validate_against_cfg(rec, top) for rec in self.records}
        stress_report = {"summary": self.stress_eval(top)}
        rewrite_report = {tok: role for tok, role in self.rewrite_rules(top).items()}
        lattice_report = self.token_lattice(top)
        decoder_exports = self.decoder_exports(top)
        auto_grammar = self.auto_grammar_induction(top)
        cfg_rules.update({f"AUTO_{k}": v for k, v in auto_grammar.items()})
        stability_report = self.stability_summary(top)
        ambiguity_report = self.ambiguity_summary(top)
        ranked_grammar_trees = self.grammar_tree_candidates(top)
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
        )

    def export_grammar_candidates(self, hyp: DecodeHypothesis) -> Dict[str, List[str]]:
        grammar = {
            "START": ["SEGMENT", "ASSIGN", "ARROW", "GROUP"],
            "SEGMENT": ["OPCODE", "STATE_MARKER", "OPERAND", "DELIMITER", "BIND", "FUNCTION"],
            "OPCODE": ["OPCODE", "OPERAND", "DELIMITER", "BIND"],
            "OPERAND": ["DELIMITER", "OPCODE", "OPERAND"],
            "DELIMITER": ["SEGMENT", "OPCODE", "OPERAND", "GROUP", "BIND", "FUNCTION"],
            "BIND": ["OPCODE", "OPERAND", "STATE_MARKER"],
            "GROUP": ["SEGMENT", "GROUP_END"],
            "STATE_MARKER": ["DELIMITER", "OPCODE", "OPERAND", "FUNCTION"],
            "FUNCTION": ["GROUP_START", "EXPR"],
        }
        if not any(r == "binding_symbol" for r in hyp.assignment.mapping.values()):
            grammar["BIND"] = ["OPCODE", "OPERAND"]
        return grammar

    def emit_report(self, result: DecodeResult) -> str:
        lines: List[str] = []
        lines.append("=== IDCM Reverse Compiler Report v9 ===")
        lines.append(f"formula_count: {len(self.records)}")
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
        lines.append("1. v9 將 function call 從一般 segment 拆出，令 AST 更似真正 compiler。")
        lines.append("2. ranked grammar trees 提供結構候選優先序。")
        lines.append("3. 若 function / state / binding 的穩定度分離成功，decoder 會再收斂一層。")
        lines.append("4. 若 parse tree 同 lattice / rewrite / binary 出現一致，grammar 可能已接近封閉。")
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
    parser = argparse.ArgumentParser(description="IDCM reverse compiler research harness v9")
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
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(rc.emit_report(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
