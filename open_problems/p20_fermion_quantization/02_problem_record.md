# SP2: Yukawa Coupling from W-field/Higgs Overlap — Problem Record

**Date:** 2026-08-01
**Parent:** P20 — Fermion Quantization
**Status:** 🔴 Open

---

## 1. Problem Statement

The Dirac structure has been derived from K_chain (SP1, 9/9 ✅). The mass operator gives:

$$m_f = \varphi^{-k_f} \cdot m_{\text{3rd-gen}}$$

But the **Yukawa coupling** — the interaction between the Higgs boson and fermions — has not been derived from the W-field.

The Higgs is the **radial mode** of the W-field:

$$\Phi = (v + H) / \sqrt{2}, \quad m_H = 2\sqrt{\kappa} \cdot V_{EW}$$

The Yukawa coupling must come from the **overlap integral** between:
- The W-field radial excitation (Higgs)
- The W-field spinor excitation (fermion)

**Gap:** No structural derivation of $y_f$ from W-field first principles.

---

## 2. Known Starting Points

### 2.1 Higgs Sector
- $V_{EW} = 246.22$ GeV (structural from $M_P$ and $V_{EW}/M_P = \varphi^{-(N_d + h^{11} - 4\varepsilon^2)}$)
- $m_H = 2\sqrt{\kappa} \times V_{EW} = 123.11$ GeV (1.59% from RG running)
- $\lambda = 2\kappa = 0.125$ at GUT scale, $\lambda(M_Z) \approx 0.129$ after RG

### 2.2 Fermion Masses
- $m_f = \varphi^{-k_f} \cdot m_{\text{3rd-gen}}$ (K_tree eigenvalue)
- All 6 charged fermion masses verified (SP1, 9/9 ✅)

### 2.3 Dirac Structure
- $\gamma^\mu$ matrices derived from $\sigma \otimes \sigma$ tensor products (SP1)
- Chiral projectors $P_L, P_R$ from $Z_2$ grading (SP1)
- Dirac operator: $i\gamma^\mu\partial_\mu - m_f$

---

## 3. What Must Be Derived

| # | Item | Input | Target |
|:-:|:-----|:------|:-------|
| 1 | Yukawa coupling $y_f$ from W-field overlap | W-field radial mode × spinor mode | $y_f = \sqrt{2} \cdot m_f / V_{EW}$ |
| 2 | Structural formula for $y_f$ | $k_f, \varphi, V_{EW}$ | $y_f = \varphi^{-k_f} \cdot m_{\text{3rd-gen}} \cdot \sqrt{2} / V_{EW}$ |
| 3 | Overlap integral mechanism | K_matrix mode structure | $\langle W_H | W_\psi | W_H \rangle$ |
| 4 | Top Yukawa $y_t \approx 1$ | Reference | $\sqrt{2} \cdot 172.76 / 246.22 = 0.992$ |
| 5 | Electron Yukawa $y_e \approx 2.9\times10^{-6}$ | Deeply suppressed | $\sqrt{2} \cdot 0.000511 / 246.22 = 2.94\times10^{-6}$ |
| 6 | Yukawa RG running | GUT to weak scale | Match SM RGE structure |

---

## 4. Success Criteria

| Criterion | Threshold | Method |
|:----------|:---------:|:-------|
| $y_t$ accuracy | $< 2\%$ | $\sqrt{2}m_t/V_{EW}$ vs PDG |
| $y_b$ accuracy | $< 5\%$ | $\sqrt{2}m_b/V_{EW}$ vs PDG |
| All charged fermions | $< 10\%$ | Compare with PDG Yukawa couplings |
| Structural origin | No free param | $y_f$ from $\varphi, k_f, V_{EW}$ only |
| Overlap mechanism | Algebraic | $y_f = \langle \Phi | \psi \psi | \Phi \rangle$ |

---

## 5. Key Physical Insight

The Yukawa coupling in IDCM is **not tuned**. It is the **overlap integral** of the W-field radial mode (Higgs) with the W-field spinor mode (fermion) on the K_chain ⊗ K_tree graph:

$$y_f = \underbrace{\frac{\sqrt{2} \cdot m_{\text{3rd-gen}}}{V_{EW}}}_{\text{reference}} \times \underbrace{\varphi^{-k_f}}_{\text{K_tree depth}}$$

Where:
- $\sqrt{2} \cdot m_{\text{3rd-gen}} / V_{EW}$ is the **reference coupling** at the top of the tree
- $\varphi^{-k_f}$ is the **K_tree eigenvalue** suppressing the coupling for lower generations
- $k_f \in \{k_u, k_d, k_l\}$ are the tree depths for up/down/lepton sectors

The mechanism:
$$\mathcal{L}_{\text{Yukawa}} = -y_f \cdot \bar{\psi}_L \Phi \psi_R + \text{h.c.}$$

After SSB ($\Phi \to (v+H)/\sqrt{2}$):
$$m_f = y_f \cdot \frac{v}{\sqrt{2}}$$

This gives the **structural Yukawa formula**:
$$y_f = \frac{\sqrt{2} \cdot \varphi^{-k_f} \cdot m_{\text{3rd-gen}}}{V_{EW}}$$

---

## 6. Verification Plan

1. Compute $y_f$ for all 9 charged fermions from structural formula
2. Compare with SM Yukawa couplings $y_f^{\text{SM}} = \sqrt{2} m_f^{\text{PDG}} / v$
3. Check $y_t \approx 1$, $y_e \approx 3 \times 10^{-6}$
4. Verify RG running effect: $\lambda$ and $y_t$ co-evolution
5. Cross-validate with SM RGE structure