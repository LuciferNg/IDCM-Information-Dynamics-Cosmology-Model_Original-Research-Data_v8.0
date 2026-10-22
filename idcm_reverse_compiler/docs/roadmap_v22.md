# v22 Roadmap — Compiler Cosmology Execution Layer

## Status
v21: 結構驗證完成 ✅
- 11 structural formulas, 4 fitting, 0 false positives
- 5-core ISA proven (LOAD, STORE, POW, DIV, SQRT)
- 2+1=3 operation dimension confirmed
- Corpus cleaning pipeline operational
- Paper `compiler_cosmology_paper.md` written

## v22 Targets

### Priority 1: IR Execution Engine (Inline)
- **What:** Embed the Minimal VM (Appendix G) directly into the compiler
- **Why:** Paper has the VM as a Python script; v22 should validate IR internally
- **Deliverable:** `compiler.eval_ir(ir, mem) → float` returning numerical result
- **Verification:** All 11 structural formulas produce correct numerical values

### Priority 2: Automated Verification Suite
- **What:** Compare each structural formula's VM output against PDG/known values
- **Why:** Currently manual; should be `pytest verify_formulas.py`
- **Boundary:** Must distinguish "structural error" from "input conversion error"
- **Deliverable:** `verify_all/verify_structural.py` — regression test for all 11 formulas

### Priority 3: Dependency Graph Export
- **What:** Auto-generate the adjacency matrix and closure chain
- **Why:** Paper has hand-written matrix; should be auto-generated
- **Deliverable:** `compiler.export_dependency_graph() → JSON/CSV/ASCII`
- **Schema:** `{"phi": {"eps":1, "beta":1, ...}, ...}`

### Priority 4: CKM Unified Derivation
- **What:** Add MERA correction to V_us (currently 4.9% error, pure geometric)
- **Why:** V_us = φ⁻³ is correct structural core; error shows need for ε-correction
- **Hypothesis:** V_us = φ⁻³ + ε² · f(φ) ≈ 0.2248 (closing the gap)
- **Verification:** Error must drop from 4.9% to < 0.5%

### Priority 5: LaTeX Registry Corpus Cleaner
- **What:** Extend `sanitize()` to handle `\varphi`, `\varepsilon`, `\beta`, `\Omega` etc.
- **Why:** registry.json (39 formulas) fails at 38/39 unknown due to LaTeX tokens
- **Deliverable:** `registry_to_corpus()` converting LaTeX → plain-text φ, ε, β, Ω

### Priority 6: Absolute Mass Scale (Exploratory)
- **What:** V_EW = M_P / φ^80 ± correction
- **Status:** 🔬 Exploratory — needs derivation
- **Method:** Use v22's VM to test candidate formulas against known values
- **Constraint:** No free parameters; only N_d, L, k_u/k_d/k_l, φ, ε, β, κ allowed

## Dependencies

```
v22 = v21
    + VM engine (P1)
    + Automated verification (P2)
    + Dependency graph (P3)
    + CKM correction (P4)
    + LaTeX handling (P5)
    + [Explore P6 if time permits]
```

## Verification Criteria
- All 11 structural formulas: Forest=1, Confidence=1.00
- All IR sequences: numerical accuracy within v21 error bounds
- Regression test: v22 ≥ v21 on all metrics
- CKM: V_us error < 0.5% (target)