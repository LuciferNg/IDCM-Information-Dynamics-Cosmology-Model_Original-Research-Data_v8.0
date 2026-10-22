# P20: Fermion Quantization — Attack Plan

**Date:** 2026-08-01
**Status:** 🔴 THE Big Gap — 3 sub-problems

---

## Current State

| Sector | Status | What Exists |
|:-------|:------:|:------------|
| Gauge boson quantization | ✅ P18 7/7 | SU(3)×SU(2)×U(1) from CY₃(36,98) |
| Dirac structure from K_chain | 🟡 Draft | `07-dirac_from_kmatrix.md` — 1+1D sketch, γ^μ assumed |
| Yukawa coupling | 🔴 Missing | Nothing |
| Full SM Lagrangian | 🔴 Not assembled | Gauge + Higgs ✅, fermions missing |

---

## Sub-Problem Breakdown

### SP1: Dirac Structure from K_chain (Formal)

**Goal:** Derive 3+1D Dirac equation from W-field graph structure, with numerical verification.

**Steps:**
1. K_chain complementary pairing → 2-component spinor (already done)
2. Shift operator → γ^1 structure (extend to 3+1D)
3. Clifford algebra extraction from graph adjacency
4. Mass operator from K_tree eigenvalues
5. Chiral projectors from Z₂ grading
6. Verify: Dirac dispersion matches W-field dispersion
7. Cross-validate: free Dirac equation in continuum limit

### SP2: Yukawa Coupling from W-field/Higgs Overlap

**Goal:** Derive y_f from W-field radial mode (Higgs) overlap with fermion spinor modes.

**Steps:**
1. Higgs as radial mode of W-field (already shown: m_H = 2√κ × V_EW)
2. Overlap integral: ⟨W_radial | W_fermion | W_radial⟩
3. Structural form: y_f = φ^k_f × ε³ × F_n/CY₃^s
4. Verify: m_f = y_f × v/√2 for all 6 charged fermions
5. Cross-validate: top Yukawa ≈ 1, electron Yukawa ≈ 3×10⁻⁶

### SP3: Full SM Lagrangian Assembly

**Goal:** Assemble complete SM Lagrangian from W-field first principles.

**Steps:**
1. Gauge sector (reuse P18)
2. Fermion kinetic terms (from SP1)
3. Yukawa terms (from SP2)
4. Higgs sector (existing)
5. Verify: Lagrangian reproduces SM phenomenology

---

## Execution Order

```
SP1: Dirac Structure → SP2: Yukawa → SP3: Full Lagrangian
```

Each SP produces:
- `0N_problem_record.md` — Problem statement
- `0N_derivation.py` — Numerical derivation + verification
- `0N_derivation.md` — Full derivation document
- `0N_cross_validate.py` — External cross-validation