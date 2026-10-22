#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IDCM Reverse Compiler v1

Initial baseline:
- tokenize a small corpus
- assign coarse roles
- search simple decoder hypotheses
- report sample-corpus consistency

This is the earliest recovered baseline from session history.
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
    (?:\d+\.\d+|\d+)
    |(?:[A-Za-zα-ωΑ-Ω]+)
    |(?:<=|>=|!=|==|->|=>|::|\+\-|\*\*|//)
    |(?:[\^_\-+*/=(),\[\]{}:/])
    |(?:\S)
    """,
    re.VERBOSE,
)

ROLE_CANDIDATES = [
    "delimiter",
    "opcode",
    "operand",
    "state_marker",
    "binding_symbol",
    "function",
    "action",
    "unknown",
]


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


@dataclass
class DecodeResult:
    hypotheses: List[DecodeHypothesis]
    token_roles: Dict[str, str]
    token_stats: Dict[str, Dict[str, int]]
    role_transition_stats: Dict[str, Dict[str, int]]
    parse_summaries: Dict[str, str]
    consistency: Dict[str, str]


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

    @staticmethod
    def candidates_for(token_text: str) -> List[str]:
        if re.fullmatch(r"\d+\.\d+|\d+", token_text):
            return ["operand"]
        if token_text in {"=", "->", "=>", ":", "::", ",", ";", "(", ")", "[", "]", "{", "}"}:
            return ["delimiter"]
        if token_text in {"^", "_"}:
            return ["binding_symbol"]
        if token_text in {"sqrt", "sin", "cos", "tan", "log", "exp"}:
            return ["function"]
        if token_text in {"SHL", "MOV", "ADD", "SUB", "CMP", "JMP", "SYNC"}:
            return ["action"]
        if re.fullmatch(r"[A-Za-zα-ωΑ-Ω]+", token_text):
            if token_text in {"phi", "eps", "kappa", "beta", "N", "L", "d"}:
                return ["state_marker", "binding_symbol", "unknown"]
            return ["state_marker", "action", "opcode", "unknown"]
        if token_text in {"+", "-", "*", "/", "**", "//"}:
            return ["opcode"]
        return ["unknown"]

    def enumerate_hypotheses(self, max_hypotheses: int = 256) -> List[DecodeHypothesis]:
        unique_tokens = sorted({t.text for rec in self.records for t in rec.tokens})
        candidate_lists = [self.candidates_for(tok) for tok in unique_tokens]
        hypotheses: List[DecodeHypothesis] = []
        for idx, roles in enumerate(product(*candidate_lists)):
            if len(hypotheses) >= max_hypotheses:
                break
            hypotheses.append(DecodeHypothesis(name=f"H{idx:04d}", assignment=RoleAssignment(dict(zip(unique_tokens, roles)))))
        return hypotheses

    @staticmethod
    def score_token(token: Token, role: str) -> float:
        if token.kind == "number":
            return 3.0 if role == "operand" else -1.0
        if token.kind == "symbol":
            if role == "function":
                return 2.5
            if role == "action":
                return 2.0
            if role == "state_marker":
                return 1.5
            return -0.2
        if token.kind in {"group", "separator"}:
            return 2.0 if role == "delimiter" else -1.0
        if token.kind == "binding":
            return 2.5 if role == "binding_symbol" else -1.0
        if token.kind == "operator":
            return 1.5 if role in {"delimiter", "opcode", "action"} else -0.5
        return 0.0

    def score_hypothesis(self, hyp: DecodeHypothesis) -> float:
        total = 0.0
        for rec in self.records:
            for token in rec.tokens:
                total += self.score_token(token, hyp.assignment.role_of(token.text))
            roles = [hyp.assignment.role_of(t.text) for t in rec.tokens]
            total += sum(1 for a, b in zip(roles, roles[1:]) if a == b)
        return total

    def build_token_stats(self) -> Dict[str, Dict[str, int]]:
        stats: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for rec in self.records:
            for t in rec.tokens:
                stats[t.text][t.kind] += 1
        return {k: dict(v) for k, v in stats.items()}

    def build_role_transition_stats(self, hyp: DecodeHypothesis) -> Dict[str, Dict[str, int]]:
        stats: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        for rec in self.records:
            roles = [hyp.assignment.role_of(t.text) for t in rec.tokens]
            for a, b in zip(roles, roles[1:]):
                stats[a][b] += 1
        return {k: dict(v) for k, v in stats.items()}

    def parse_summary(self, rec: FormulaRecord, hyp: DecodeHypothesis) -> str:
        return " ".join(f"{t.text}:{hyp.assignment.role_of(t.text)}/{t.kind}" for t in rec.tokens)

    def consistency_report(self, hyp: DecodeHypothesis) -> Dict[str, str]:
        report: Dict[str, str] = {}
        for tok in sorted(hyp.assignment.mapping):
            role = hyp.assignment.role_of(tok)
            if tok in {"phi", "eps", "kappa", "beta", "N", "L", "d"} and role in {"state_marker", "action"}:
                report[tok] = "MATCH"
            elif tok in {"sqrt"} and role == "function":
                report[tok] = "MATCH"
            elif tok in {"SHL"} and role in {"action", "opcode"}:
                report[tok] = "MATCH"
            elif tok in {"^", "_"} and role == "binding_symbol":
                report[tok] = "MATCH"
            elif tok in {"=", "->"} and role == "delimiter":
                report[tok] = "MATCH"
            elif re.fullmatch(r"\d+\.\d+|\d+", tok) and role == "operand":
                report[tok] = "MATCH"
            else:
                report[tok] = "CHECK"
        return report

    def search_decoder(self, max_hypotheses: int = 256, top_k: int = 5) -> DecodeResult:
        token_stats = self.build_token_stats()
        hypotheses = self.enumerate_hypotheses(max_hypotheses=max_hypotheses)
        scored = []
        for hyp in hypotheses:
            hyp.score = self.score_hypothesis(hyp)
            scored.append(hyp)
        scored.sort(key=lambda h: h.score, reverse=True)
        best = scored[:top_k]
        top = best[0] if best else DecodeHypothesis(name="NONE", assignment=RoleAssignment({}))
        token_roles = dict(top.assignment.mapping)
        role_transition_stats = self.build_role_transition_stats(top)
        parse_summaries = {rec.raw: self.parse_summary(rec, top) for rec in self.records}
        consistency = self.consistency_report(top)
        return DecodeResult(
            hypotheses=best,
            token_roles=token_roles,
            token_stats=token_stats,
            role_transition_stats=role_transition_stats,
            parse_summaries=parse_summaries,
            consistency=consistency,
        )

    def emit_report(self, result: DecodeResult) -> str:
        lines: List[str] = []
        lines.append("=== IDCM Reverse Compiler Report v1 ===")
        lines.append(f"formula_count: {len(self.records)}")
        lines.append("")
        lines.append("-- Top hypotheses --")
        for hyp in result.hypotheses:
            lines.append(f"{hyp.name} score={hyp.score:.3f}")
            preview = ", ".join(f"{k}:{v}" for k, v in sorted(hyp.assignment.mapping.items()))
            lines.append(f"    mapping: {preview}")
        lines.append("")
        lines.append("-- Token role summary --")
        for tok, role in sorted(result.token_roles.items()):
            lines.append(f"{tok!r}: {role}")
        lines.append("")
        lines.append("-- Token stats --")
        for tok, stats in sorted(result.token_stats.items()):
            lines.append(f"{tok!r}: {stats}")
        lines.append("")
        lines.append("-- Role transition matrix --")
        for a, row in sorted(result.role_transition_stats.items()):
            row_s = ", ".join(f"{b}={n}" for b, n in sorted(row.items()))
            lines.append(f"{a} -> {row_s}")
        lines.append("")
        lines.append("-- Parse summaries --")
        for raw, summary in result.parse_summaries.items():
            lines.append(raw)
            lines.append(f"    {summary}")
        lines.append("")
        lines.append("-- Consistency report --")
        for tok, verdict in sorted(result.consistency.items()):
            lines.append(f"{tok!r}: {verdict}")
        lines.append("")
        lines.append("-- Interpretation --")
        lines.append("1. v1 is the earliest baseline: tokenization + coarse roles + hypothesis scoring.")
        lines.append("2. The goal is the simplest decoder that keeps the sample corpus consistent.")
        lines.append("3. Later versions add grammar, trees, forests, votes, W-field, and semantic layers.")
        return "\n".join(lines)


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


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="IDCM reverse compiler research harness v1")
    parser.add_argument("--input", "-i", help="JSON file or newline text file containing formulas")
    parser.add_argument("--max-hypotheses", type=int, default=256)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--output-json", action="store_true")
    return parser


def main(argv: Sequence[str]) -> int:
    args = build_arg_parser().parse_args(argv[1:])
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
        print(json.dumps({
            "formula_count": len(formulas),
            "top_hypotheses": [
                {"name": h.name, "score": h.score, "mapping": h.assignment.mapping}
                for h in result.hypotheses
            ],
            "token_roles": result.token_roles,
            "token_stats": result.token_stats,
            "role_transition_stats": result.role_transition_stats,
            "parse_summaries": result.parse_summaries,
            "consistency": result.consistency,
        }, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(rc.emit_report(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
