# IDCM 完整公式目錄

## AXIOM（1）
| # | Name | Formula | Type | Pipeline Origin |
|:-:|:-----|:--------|:-----|:----------------|
| 1 | phi | x² + x - 1 = 0 | Axiom | Fibonacci scheduling fixed point |

## STRUCTURAL（12）
| # | Name | Formula | Pipeline Origin |
|:-:|:-----|:--------|:----------------|
| 2 | eps | ε = φ⁻¹/4 | gap / 4 MERA directions |
| 3 | beta | β = φ⁻¹/2 | half-gap (symmetric) |
| 4 | kappa | κ = 1/16 | MERA² = 4² |
| 5 | N_d | N_d = 44 | 4 MERA × 11 pipeline depth |
| 6 | L | L = 53/8 | (N_d + 3²)/2³ |
| 7 | k_u | k_u = 33β | 33 = 3 generations × 11 |
| 8 | k_l | k_l = 19β | 19 = 11 + 8 |
| 9 | k_d | k_d = 26β - φ⁻⁴ | 26 = 44 - 3×6 |
| 10 | V_cb | V_cb = φ²/64 | φ² / 4³ |
| 11 | V_us | V_us = φ⁻³ | pure φ-power, -3 = generations |
| 12 | Omega_Lambda | Ω_Λ = 4/(φ⁴-1) | heat dissipation / pipeline cost |
| 13 | V_EW/M_P | V_EW/M_P = φ^(4ε²-80) | VEV/Planck ratio, 80 = N_d+h¹¹ |

## FITTING（3）
| # | Name | Formula | Free Variable |
|:-:|:-----|:--------|:--------------|
| 14 | gamma_n | γ_n = 4sin²(πn/2N_d) | n |
| 15 | v_g | v_g = cos(πn/2N_d) | n |
| 16 | V_ub | V_ub = φ^-(M/5 + M/11 + 2) | M |

## REGISTRY FORMULAS（additional 23）
### Pure structural definitions
| # | Name | Formula | Note |
|:-:|:-----|:--------|:-----|
| 17 | κ | 1/B² | B = φ³-φ⁻³ = 4 |
| 18 | κ² | 1/B⁴ | κ squared |
| 19 | ε | φ⁻¹/4 | duplicates paper S1 |
| 20 | β | φ⁻¹/2 | duplicates paper S3 |
| 21 | 137 | 137 | EM coupling structural base |
| 22 | 137+δ_QED | 137+δ_QED | QED loop correction |

### Derived structural constants
| # | Name | Formula | Pipeline Origin |
|:-:|:-----|:--------|:----------------|
| 23 | Δx_min | κ·L_P | MUP direct derivation |
| 24 | Δp_max | ħ/(κ·L_P) | MUP direct derivation |
| 25 | γ_n+γ_{N_d-n} | 4 | dual pairing identity |
| 26 | ρ_bare | φ⁻⁴ | tree curvature (bare) |
| 27 | ρ_obs | φ⁻⁴·(1+ε/2) | RG running tree→EW scale |
| 28 | δ_e | 63φ⁻⁴/256 | vertex projection f_W |
| 29 | δ_u | 2γ₂ | chain Laplacian |
| 30 | β(g) | -εg/2 | MERA coarse-graining |
| 31 | β_MERA(y_f) | -lnφ/(2ln4)·y_f | tree depth RG running |
| 32 | η | 19φ/88 | k_l and N_d combination |
| 33 | δ_CP | arctan(19φ⁵/88) | k_l and N_d geometric ratio |
| 34 | J | A²λ⁶η | from Wolfenstein parameters |

### Fitting / input-dependent
| # | Name | Formula | Why fitting |
|:-:|:-----|:--------|:------------|
| 35 | ω²_n | 4sin²(πn/2N_d) | n = free variable |
| 36 | γ_n | 4sin²(πn/2N_d) | n = free variable |
| 37 | λ | φ⁻³-(γ₃-2γ₂+γ₁) | references γ_n |
| 38 | A | V_cb/λ² | references λ |
| 39 | E_cut | √2·M_P·c² | Planck scale definition |
| 40 | T_H_corr | T_H·(1+κ²M_P²/M²)⁻¹ | references M |
| 41 | S_inst | 2π/ε | instanton action |
| 42 | β₁_SU3 | N_d/2+B | references B |
| 43 | β₁_SU2 | N_d/8+N_f/9 | N_f = external input |
| 44 | β₁_U1 | N_d/4+1/18 | 1/18 = external? |
| 45 | β₁/β₀_U1 | φ | pure φ, but derived from SU3/SU2/U1 |
| 46 | V(r) | σr | MERA minimal cut |
| 47 | σ | (B/(B-1))²·ε·(N_d/π)·Λ_QCD² | references Λ_QCD |
| 48 | Λ_QCD | external input | cannot derive from K-matrix |