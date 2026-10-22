#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IDCM 逆向編譯器 v2

升級目標：
- 加入 grammar / bigram 約束
- 加入上下文轉移矩陣
- 加入括號深度 / 分段評分
- 加入 corpus 載入
- 保留窮究式搜尋，但避免 token 過度自由解讀

定位：
- 這仍然係 research harness，不係最終答案
- 先找「最少假設 + 最大一致性」的 decoder 候選
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
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


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

ROLE_CANDIDATES = [
    "opcode",
    "operand",
    "delimiter",
    "state_marker",
    "literal",
    "address",
    "length_field",
    "control_flag",
    "binding_symbol",
    "unknown",
]

KINDS = ["number", "symbol", "operator", "group", "separator", "binding", "other"]


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
class DecodeResult:
    hypotheses: List[DecodeHypothesis]
    token_stats: Dict[str, Dict[str, int]]
    token_roles: Dict[str, str]
    kind_transition_stats: Dict[str, Dict[str, int]]
    role_transition_stats: Dict[str, Dict[str, int]]
    parse_summaries: Dict[str, List[str]]


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

    def build_role_transition_stats(self, hyp: DecodeHypothesis) -> Dict[str, Dict[str, int]]:
        stats: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for rec in self.records:
            roles = [hyp.assignment.role_of(t.text) for t in rec.tokens]
            for a, b in zip(roles, roles[1:]):
                stats[a][b] += 1
        return {k: dict(v) for k, v in stats.items()}

    @staticmethod
    def classify_token_candidates(token: str) -> List[str]:
        if re.fullmatch(r"\d+\.\d+|\d+", token):
            return ["operand", "literal", "length_field", "address"]
        if re.fullmatch(r"[A-Za-zα-ωΑ-Ω]+", token):
            return ["opcode", "state_marker", "binding_symbol", "unknown"]
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

    def enumerate_hypotheses(self, max_hypotheses: int = 512) -> List[DecodeHypothesis]:
        unique_tokens = sorted({t.text for rec in self.records for t in rec.tokens})
        candidate_lists = [self.classify_token_candidates(tok) for tok in unique_tokens]

        # 窮究式但受控：如果笛卡爾積太大，先用 token kind 簡化
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
            hypotheses.append(
                DecodeHypothesis(
                    name=f"H{idx:04d}",
                    assignment=RoleAssignment(mapping=mapping),
                )
            )
        return hypotheses

    @staticmethod
    def prune_candidates(token: str, cands: List[str]) -> List[str]:
        # 先做一層保守收斂，避免太自由
        if re.fullmatch(r"\d+\.\d+|\d+", token):
            return [c for c in cands if c in {"operand", "literal", "length_field"}]
        if token in {"=", "->", "=>", ":", "::"}:
            return [c for c in cands if c in {"delimiter", "binding_symbol"}]
        if token in {"(", ")", "[", "]", "{", "}"}:
            return ["delimiter"]
        if token in {"^", "_"}:
            return ["binding_symbol"]
        if token in {",", ";"}:
            return ["delimiter"]
        if token in {"+", "-", "*", "/", "**", "//"}:
            return [c for c in cands if c in {"opcode", "delimiter"}]
        return cands

    @staticmethod
    def token_kind_compatibility(token: str, kind: str, role: str, prev_kind: Optional[str], next_kind: Optional[str]) -> float:
        score = 0.0

        # 基本角色兼容性
        if kind == "number":
            if role in {"operand", "literal", "length_field", "address"}:
                score += 3.0
            else:
                score -= 2.0
        elif kind == "symbol":
            if role in {"opcode", "state_marker", "binding_symbol"}:
                score += 2.0
            else:
                score -= 0.2
        elif kind in {"group", "separator"}:
            if role == "delimiter":
                score += 3.0
            else:
                score -= 1.5
        elif kind == "binding":
            if role == "binding_symbol":
                score += 3.0
            else:
                score -= 1.0
        elif kind == "operator":
            if token in {"=", "->", "=>", ":", "::", "+", "-", "*", "/", "**", "//", "<=", ">=", "!=", "=="}:
                if role in {"delimiter", "opcode", "control_flag"}:
                    score += 2.0
                else:
                    score -= 0.5

        # 字面 token 的先驗偏好
        if token in {"=", "->", "=>"} and role == "delimiter":
            score += 2.5
        if token in {"^", "_"} and role == "binding_symbol":
            score += 2.5
        if token in {"(", ")", "[", "]", "{", "}"} and role == "delimiter":
            score += 2.5

        # 鄰接關係：數字通常唔應該直接夾住兩個符號，除非係 operand/literal
        if kind == "number":
            if prev_kind in {"symbol", "number"} and next_kind in {"symbol", "number"}:
                if role in {"operand", "literal", "address"}:
                    score += 1.0
                else:
                    score -= 1.0

        return score

    def score_hypothesis(self, hyp: DecodeHypothesis) -> Tuple[float, List[str]]:
        score = 0.0
        notes: List[str] = []
        unique_tokens = sorted(hyp.assignment.mapping.keys())
        role_counter = Counter(hyp.assignment.mapping.values())

        # 1) token-level compatibility
        for rec in self.records:
            tokens = rec.tokens
            for i, t in enumerate(tokens):
                role = hyp.assignment.role_of(t.text)
                prev_kind = tokens[i - 1].kind if i > 0 else None
                next_kind = tokens[i + 1].kind if i + 1 < len(tokens) else None
                score += self.token_kind_compatibility(t.text, t.kind, role, prev_kind, next_kind)

        # 2) kind transition coherence
        for rec in self.records:
            kinds = [t.kind for t in rec.tokens]
            roles = [hyp.assignment.role_of(t.text) for t in rec.tokens]
            for (k1, k2), (r1, r2) in zip(zip(kinds, kinds[1:]), zip(roles, roles[1:])):
                # delimiter 後接 symbol/number 是合理的
                if k1 in {"operator", "separator", "group", "binding"} and r1 in {"delimiter", "binding_symbol"}:
                    if k2 in {"symbol", "number", "group"} and r2 in {"opcode", "operand", "state_marker", "literal", "binding_symbol", "delimiter"}:
                        score += 0.5
                # binding 之後常見係 symbol/number
                if k1 == "binding" and r1 == "binding_symbol" and k2 in {"symbol", "number"}:
                    score += 1.0
                # 兩個 number 連住通常像 packed literal / width specification
                if k1 == "number" and k2 == "number":
                    if r1 in {"operand", "literal", "length_field", "address"} and r2 in {"operand", "literal", "length_field", "address"}:
                        score += 0.5
                    else:
                        score -= 0.5

        # 3) bracket depth / structure stability
        for rec in self.records:
            depth = 0
            max_depth = 0
            balance_ok = True
            for t in rec.tokens:
                if t.text in {"(", "[", "{"}:
                    depth += 1
                    max_depth = max(max_depth, depth)
                elif t.text in {")", "]", "}"}:
                    depth -= 1
                    if depth < 0:
                        balance_ok = False
                elif t.text == "=" and depth == 0:
                    # 定義/closure 覺得較像分界
                    score += 0.5
            if depth != 0:
                balance_ok = False
            if balance_ok:
                score += 1.5
            score += min(1.5, max_depth * 0.25)

        # 4) role entropy penalty：角色太碎會變成任意投射
        distinct_roles = len([r for r, c in role_counter.items() if c > 0 and r != "unknown"])
        score += max(0.0, 8.0 - distinct_roles)
        score -= 1.25 * role_counter.get("unknown", 0)

        # 5) 具體偏好：如果等號、箭頭、括號都係 delimiter/binding，通常更像 grammar
        for tok in {"=", "->", "=>", "(", ")", "[", "]", "{", "}"}:
            role = hyp.assignment.role_of(tok)
            if tok in {"=", "->", "=>", "(", ")", "[", "]", "{", "}"} and role == "delimiter":
                score += 2.5
            elif tok in {"(", ")", "[", "]", "{", "}"} and role != "delimiter":
                score -= 1.0

        if hyp.assignment.role_of("^") == "binding_symbol":
            score += 1.0
        if hyp.assignment.role_of("_") == "binding_symbol":
            score += 1.0

        # note：top hypothesis 如果把大量 symbol 都塞成 opcode，通常太自由，扣一點
        opcode_like = sum(1 for tok in unique_tokens if hyp.assignment.role_of(tok) == "opcode")
        if opcode_like > max(2, len(unique_tokens) // 2):
            score -= (opcode_like - max(2, len(unique_tokens) // 2)) * 0.75

        return score, notes

    def parse_summary_for_record(self, rec: FormulaRecord, hyp: DecodeHypothesis) -> str:
        chunks: List[str] = []
        current: List[str] = []
        for t in rec.tokens:
            role = hyp.assignment.role_of(t.text)
            if role in {"delimiter", "binding_symbol"}:
                if current:
                    chunks.append(" ".join(current))
                    current = []
                chunks.append(f"[{t.text}:{role}]")
            else:
                current.append(f"{t.text}:{role}")
        if current:
            chunks.append(" ".join(current))
        return " | ".join(chunks)

    def search_decoder(self, max_hypotheses: int = 512, top_k: int = 10) -> DecodeResult:
        token_stats = self.build_token_stats()
        kind_transition_stats = self.build_kind_transition_stats()
        hypotheses = self.enumerate_hypotheses(max_hypotheses=max_hypotheses)
        scored: List[DecodeHypothesis] = []
        for hyp in hypotheses:
            hyp.score, hyp.notes = self.score_hypothesis(hyp)
            scored.append(hyp)
        scored.sort(key=lambda h: h.score, reverse=True)
        best = scored[:top_k]

        top_mapping: Dict[str, str] = {}
        if best:
            top_mapping = dict(best[0].assignment.mapping)

        top_hyp = best[0] if best else DecodeHypothesis(name="NONE", assignment=RoleAssignment(mapping={}))
        role_transition_stats = self.build_role_transition_stats(top_hyp)
        parse_summaries = {
            rec.raw: [self.parse_summary_for_record(rec, top_hyp)] if best else []
            for rec in self.records
        }

        return DecodeResult(
            hypotheses=best,
            token_stats=token_stats,
            token_roles=top_mapping,
            kind_transition_stats=kind_transition_stats,
            role_transition_stats=role_transition_stats,
            parse_summaries=parse_summaries,
        )

    def emit_report(self, result: DecodeResult) -> str:
        lines: List[str] = []
        lines.append("=== IDCM Reverse Compiler Report v2 ===")
        lines.append(f"formula_count: {len(self.records)}")
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

        lines.append("-- Top decoder hypotheses --")
        for hyp in result.hypotheses:
            lines.append(f"{hyp.name}  score={hyp.score:.3f}")
            items = sorted(hyp.assignment.mapping.items(), key=lambda kv: kv[0])
            preview = ", ".join(f"{k}:{v}" for k, v in items[:16])
            lines.append(f"    mapping: {preview}")
        lines.append("")

        lines.append("-- Top token role stats (best hypothesis) --")
        for tok, role in sorted(result.token_roles.items(), key=lambda kv: kv[0]):
            lines.append(f"{tok!r}: {role}")
        lines.append("")

        lines.append("-- Token kind frequency --")
        for tok, kinds in sorted(result.token_stats.items(), key=lambda kv: kv[0]):
            kinds_s = ", ".join(f"{k}={v}" for k, v in sorted(kinds.items()))
            lines.append(f"{tok!r}: {kinds_s}")
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

        lines.append("-- Interpretation --")
        lines.append("1. 這版加入咗 bigram / bracket depth / role transition 評分，所以會比上一版更不容易把所有 symbol 當成 opcode。")
        lines.append("2. 如果 top hypothesis 仍然太自由，下一步應該把 grammar 寫成顯式 state machine，而唔係只靠分數。")
        lines.append("3. 如果 top hypothesis 對多條公式都維持同一 token 角色，呢就係 candidate decoder 的強信號。")
        lines.append("4. 若某些 token（例如 phi / eps / kappa）一直被判成同一層 role，可能代表它哋係 grammar marker，而唔係數值本身。")
        return "\n".join(lines)


def load_formulas_from_source(path: Optional[str]) -> List[str]:
    if not path:
        return []
    p = path.strip()
    if not p:
        return []
    with open(p, "r", encoding="utf-8") as f:
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
    ]


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="IDCM reverse compiler research harness")
    parser.add_argument("--input", "-i", help="JSON file or newline text file containing formulas")
    parser.add_argument("--max-hypotheses", type=int, default=2048, help="Max hypotheses to enumerate")
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
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(rc.emit_report(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
