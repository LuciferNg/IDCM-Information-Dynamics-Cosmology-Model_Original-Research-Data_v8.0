# IDCM Reverse Compiler Version Run Reports

## Overview
Each version has its own report under docs/run_reports/vX.md.

## Index
- v1: Initial reverse compiler skeleton; sample corpus tokenization and basic decoder hypothesis search. Baseline roles: delimiter/opcode/operand/state_marker/binding_symbol. Verified on sample corpus with exit code 0.
- v2: Added grammar / bigram constraints, context transition matrix, bracket-depth scoring, corpus loader, JSON output. Tested on 7-formula corpus successfully (7/7 PASS).
- v3: Preserved prior version as v3 and added explicit state machine parser, grammar tree extraction, position constraints, opcode family detection. Test run succeeded.
- v4: Added AST rewrite / reduction, collision analysis, grammar candidate export, and more conservative symbol classification. First run failed (exit 1), then repaired with backup + patch and re-run succeeded.
- v5: Added binary packet guesses, CFG output, cross-formula collision ranking, and prefix+numeric opcode hypothesis tests. Test run succeeded.
- v6: Added fixed-width binary encoding, CFG validation, collision coherence ranking, and stress corpus automation. Main corpus 7/7 PASS; stress corpus 5/5 PASS.
- v7: Added rewrite rules, token lattice, auto grammar induction, decoder exports, and stronger cross-validation. Test run succeeded.
- v8: Separated sqrt as function, added finer grammar hierarchy, operator/binding split, confidence scoring, and stability/ambiguity reports. Test run succeeded.
- v9: Added function call subtree parsing, strict 4-way split (opcode/state/function/binding), and stability-ranked grammar tree export.
- v10: Introduced action/state split, canonical grammar voting, parse forest export, and token/subtree consistency voting. SHL moved to action.
- v11: Expanded to 5-layer pipeline export (token/role/tree/forest/vote), layer consistency table, and human-readable pipeline explanation.
- v12: Added consensus-first summary, disagreement matrix, stage map, rule confidence, and explicit formula-level consistency reporting.
- v13: Added W-field coherence map with strength/tension/gradient and formula-level coherence score.
- v14: Added semantic layer map: shift_opcode, control_flow_operator, assignment_operator, index_symbol, function_call.
- v15: Added rejection gate, formula ranking, and global coherence summary. Pipeline `0010 -> SHL 1 -> 0100` passes at Forest=1.
- v16: **Dialect classification.** DialectRouter operational. 100% algebraic vs pipeline routing accuracy.
- v17: **Dialect-aware parsing.** Pipeline formulas parsed correctly at Forest=1. Cross-dialect interference eliminated.
- v18: **Rejection Gate + confidence.** 87/101 pass at confidence >= 0.90. Clean formulas: Forest=1.
- v19: **IR generation.** 8 opcodes (LOAD, STORE, POW, DIV, SQRT, ADD, SUB, MUL). All structural formulas generate valid RPN.
- v20: **Automatic classification.** 11 structural | 32 fitting | 55 input. Closure converges at 16 symbols.
- v21: **Corpus cleaning + final validation.** 24 Clean Corpus: 15 active + 9 dumps. All pass Forest=1, Confidence=1.00. ISA proven: 2+1=3.
