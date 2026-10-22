# SP1: Dirac Structure from K_chain — Problem Record

**Date:** 2026-08-01
**Parent:** P20 — Fermion Quantization
**Status:** 🔴 Open

---

## 1. Problem Statement

The gauge bosons of the Standard Model have been successfully quantized from the W-field (P18, 7/7 ✅). However, **fermions as W-field spinor excitations have not**.

The existing `07-dirac_from_kmatrix.md` provides a 1+1D structural sketch showing that:
- K_chain complementary pairing (γ_n + γ_{N_d-n} = 4) → 2-component spinor
- Shift operator → γ^1-like structure
- Chiral projectors from Z₂ grading

**But this sketch is incomplete:**
1. ❌ Only 1+1D — needs 3+1D extension
2. ❌ γ^μ matrices are "assumed, not derived from K-matrix" (per verify_sm_quantization.py)
3. ❌ γ^5 coupling is "assumed"
4. ❌ No numerical verification script exists
5. ❌ No cross-validation against PDG

---

## 2. Known Starting Points

### 2.1 K_chain Structure
- K_chain is a 44×44 path graph Laplacian
- γ_n = 4 sin²(πn/88), n = 0..43
- Complementary identity: γ_n + γ_{44-n} = 4 = B (MERA branching)

### 2.2 Z₂ Grading
- Binet parity assigns depth d = {3, 2, 0} to up/down/lepton sectors
- This is the chirality origin in the W-field

### 2.3 Shift Operator
- S acts as (Sφ)_n = φ_{n+1}
- (S − S†)/(2i) gives momentum eigenvalues sin(2πn/44)

### 2.4 Mass from K_tree
- m_f ∝ φ^{-k_f} where k_f comes from tree depth
- MASS instruction: m_X = V_EW × (F_n/CY₃^s) × φ^B × (1 + ε³·c'/F_n)

---

## 3. What Must Be Derived

| # | Item | Current Status | Target |
|:-:|:-----|:--------------|:-------|
| 1 | 2-component spinor from pairing | ✅ In 1+1D | Extend to 3+1D |
| 2 | γ^0, γ^1, γ^2, γ^3 from graph | ❌ Assumed | Derive from K_chain × K_tree × K_chain × K_chain |
| 3 | Clifford algebra {γ^μ,γ^ν}=2η^{μν} | ❌ Not verified | Verify numerically |
| 4 | Dirac equation iγ^μ∂_μψ = mψ | 🟡 Sketch | Full derivation with mass operator |
| 5 | Chiral projectors (V−A) | 🟡 From Z₂ | Verify from tree depth asymmetry |
| 6 | Continuum limit | ❌ Not done | Show → standard Dirac in N_d → ∞ |

---

## 4. Success Criteria

| Criterion | Threshold | Verification Method |
|:----------|:---------:|:-------------------|
| Clifford algebra | {γ^μ,γ^ν} = 2η^{μν} I_4 within 1/N_d² | Numerical check of all 10 anticommutators |
| Dirac dispersion | ω² = p² + m² in continuum limit | Compare with W-field dispersion |
| Mass operator | M_n ≈ m_f from MASS formula | All 6 charged fermions |
| Chirality | P_L² = P_L, P_R² = P_R, P_L P_R = 0 | Verify from Z₂ graded tree depths |
| External validation | Match PDG Dirac equation at 1-loop | Vertex structure reproduces SM γ^μ coupling |

---

## 5. Approach

The 3+1D Dirac structure will be constructed as:

```
γ^0 = σ_1 ⊗ I_2     (time = mixing of complementary modes)
γ^i = iσ_2 ⊗ σ_i    (space = shift on chain × shift on tree × shift on cross-chains)
γ^5 = σ_3 ⊗ I_2     (chirality = Z₂ grading)
```

Where:
- σ_1, σ_2, σ_3 act on the complementary mode pair (u, d)
- I_2, σ_i act on the spin-1/2 index from the tree structure

**Key claim:** These are NOT inserted by hand. The K_chain adjacency and K_tree depth produce exactly this tensor product structure.

---

## 6. Verification Method

1. Write Python script that constructs γ^μ from K_chain operators
2. Compute all 10 anticommutators — verify {γ^μ,γ^ν}=2η^{μν}I_4
3. Compute γ^5 = iγ^0γ^1γ^2γ^3 — verify (γ^5)² = I_4, {γ^5, γ^μ}=0
4. Build the Dirac operator D = iγ^μ∂_μ − M
5. Verify D² = □ + M² in the continuum limit
6. Display results as a clear matrix

---

## 7. External Cross-Validation

Compare against:
- Standard 3+1D Dirac equation (PDG kinematic tests)
- Free fermion propagator G(p) = i/(p̸ − m + iε)
- Chiral coupling structure of weak interactions