#!/usr/bin/env python3
"""IDCM: Find exact φ-power formulas for 2nd gen particles using ε³ corrections."""
import math

# === CONSTANTS ===
phi = (1 + math.sqrt(5)) / 2
phi_inv = phi - 1
beta = phi_inv / 2
eps = phi_inv / 4
eps3 = eps ** 3
eps6 = eps ** 6
kappa = 1/16

print("=" * 72)
print("IDCM CONSTANTS")
print("=" * 72)
print(f"  φ       = {phi:.15f}")
print(f"  φ⁻¹     = {phi_inv:.15f}")
print(f"  β       = {beta:.15f}")
print(f"  ε       = {eps:.15f}")
print(f"  ε²      = {eps**2:.15f}")
print(f"  ε³      = {eps3:.15f}")
print(f"  ε⁴      = {eps**4:.15f}")
print(f"  ε⁶      = {eps6:.15f}")

# === k-VALUES ===
k_u = 33 * beta
k_d = 26 * beta - phi_inv**4
k_l = 19 * beta

print(f"\n  k_u = 33β = {k_u:.15f}")
print(f"  k_d = 26β - φ⁻⁴ = {k_d:.15f}")
print(f"  k_l = 19β = {k_l:.15f}")

# === CURRENT φ-POWER PREDICTIONS ===
m_c_mt_pred = phi ** (-k_u)
m_s_mb_pred = phi ** (-k_d)
m_mu_mtau_pred = phi ** (-k_l)

print(f"\n{'=' * 72}")
print("CURRENT φ-POWER PREDICTIONS (2nd gen)")
print("=" * 72)
print(f"  m_c/m_t = φ^(-{k_u:.6f}) = {m_c_mt_pred:.10f}")
print(f"  m_s/m_b = φ^(-{k_d:.6f}) = {m_s_mb_pred:.10f}")
print(f"  m_μ/m_τ = φ^(-{k_l:.6f}) = {m_mu_mtau_pred:.10f}")

# === OBSERVED VALUES ===
CY3 = 134
m_c_pdg = 1.27
m_t_pdg = 172.76
m_s_pdg = 0.0934
m_b_pdg = 4.18
m_mu_pdg = 0.105658
m_tau_pdg = 1.77686

m_c_mt_obs = 1/CY3  # 0.007462687
m_c_mt_pdg = m_c_pdg / m_t_pdg
m_s_mb_obs = m_s_pdg / m_b_pdg
m_mu_mtau_obs = m_mu_pdg / m_tau_pdg

print(f"\n{'=' * 72}")
print("OBSERVED VALUES")
print("=" * 72)
print(f"  m_c/m_t (1/CY₃=1/134) = {m_c_mt_obs:.10f}")
print(f"  m_c/m_t (PDG)         = {m_c_mt_pdg:.10f}")
print(f"  m_s/m_b (PDG)         = {m_s_mb_obs:.10f}")
print(f"  m_μ/m_τ (PDG)         = {m_mu_mtau_obs:.10f}")

# Also compute absolute masses
m_c_pred = phi ** (-k_u) * m_t_pdg
m_s_pred = phi ** (-k_d) * m_b_pdg
m_mu_pred = phi ** (-k_l) * m_tau_pdg

print(f"\n  Predicted m_c = {m_c_pred:.4f} GeV (PDG: {m_c_pdg} GeV)")
print(f"  Predicted m_s = {m_s_pred:.6f} GeV (PDG: {m_s_pdg} GeV)")
print(f"  Predicted m_μ = {m_mu_pred:.6f} GeV (PDG: {m_mu_pdg} GeV)")

# === ERRORS ===
print(f"\n{'=' * 72}")
print("CURRENT ERRORS vs 1/CY₃")
print("=" * 72)
err_c = abs(m_c_mt_pred - m_c_mt_obs) / m_c_mt_obs * 100
err_s = abs(m_s_mb_pred - m_s_mb_obs) / m_s_mb_obs * 100
err_mu = abs(m_mu_mtau_pred - m_mu_mtau_obs) / m_mu_mtau_obs * 100
print(f"  m_c/m_t: error = {err_c:.4f}%")
print(f"  m_s/m_b: error = {err_s:.4f}%")
print(f"  m_μ/m_τ: error = {err_mu:.4f}%")

# === FIND EXACT CORRECTION ===
print(f"\n{'=' * 72}")
print("FINDING EXACT ε³ CORRECTIONS")
print("=" * 72)

for name, pred, obs, k_val in [("Charm (c)", m_c_mt_pred, m_c_mt_obs, k_u),
                                 ("Strange (s)", m_s_mb_pred, m_s_mb_obs, k_d),
                                 ("Muon (μ)", m_mu_mtau_pred, m_mu_mtau_obs, k_l)]:
    corr = obs / pred
    delta_k = math.log(corr) / math.log(phi)
    n_eps3 = delta_k / eps3
    
    print(f"\n  {name}:")
    print(f"    φ-pred  = {pred:.10f}")
    print(f"    exact   = {obs:.10f}")
    print(f"    factor  = {corr:.10f}")
    print(f"    Δk      = {delta_k:.10f}")
    print(f"    Δk/ε³   = {n_eps3:.10f}")
    print(f"    round   = {round(n_eps3)}")
    
    n = round(n_eps3)
    # Try φ^(-k + n*ε³) = φ^(-k) * φ^(-n*ε³)  ... wait, no. 
    # φ^(-k) * correction = φ^(-k) * (1 + n*ε³) for linear correction
    # Or φ^(-(k - n*ε³)) = φ^(-k) * φ^(n*ε³) for exponent correction
    
    # Try: m_c/m_t = φ^(-k_u + n*ε³) = φ^(-k_u) * φ^(n*ε³)
    # So correction factor = φ^(n*ε³) which means corr = exp(n*ε³*ln(φ))
    
    # Method 1: exponent correction: k' = k - n*ε³
    # So new formula: m = φ^(-(k - n*ε³)) = φ^(-k + n*ε³)
    k_new = k_val - n * eps3
    new_pred = phi ** (-k_new)
    err_new = abs(new_pred - obs) / obs * 100
    print(f"    k' = k - {n}ε³ = {k_val:.10f} - {n*eps3:.10f} = {k_new:.10f}")
    print(f"    φ^(-k') = {new_pred:.10f}  error = {err_new:.6e}%")
    
    # Method 2: multiplicative correction: factor = 1 + n*ε³
    # So m = φ^(-k) * (1 + n*ε³)
    mul_pred = pred * (1 + n * eps3)
    mul_err = abs(mul_pred - obs) / obs * 100
    print(f"    φ^(-k) × (1 + {n}ε³) = {mul_pred:.10f}  error = {mul_err:.6e}%")
    
    # Method 3: multiplicative correction with φ-factor: factor = φ^(-n*ε³)
    # So m = φ^(-k) * φ^(-n*ε³) = φ^(-(k + n*ε³))
    k_new2 = k_val + n * eps3
    new_pred2 = phi ** (-k_new2)
    err_new2 = abs(new_pred2 - obs) / obs * 100
    print(f"    φ^(-(k + {n}ε³)) = {new_pred2:.10f}  error = {err_new2:.6e}%")
    
    # Method 4: φ^(-k) * (1 + n*ε³ + m*ε⁶) — try to find m too
    # residual = obs / (pred * (1 + n*eps3)) - 1
    if n != 0:
        residual = obs / (pred * (1 + n * eps3)) - 1
        m = residual / eps6 if abs(eps6) > 1e-20 else 0
        print(f"    Residual after 1-term: {(obs/(pred*(1+n*eps3))-1)*100:.6f}%")
        print(f"    m = residual/ε⁶ = {m:.10f}, round = {round(m) if abs(m) < 100 else 'N/A'}")

# === Try to find patterns: what if k_u = 33β - n*ε³? ===
print(f"\n{'=' * 72}")
print("SYSTEMATIC SEARCH: k' = 33β + n·ε³")
print("=" * 72)
print("  Looking for n such that φ^(-(33β + n·ε³)) = 1/134 exactly")
target = 1/134
for n in range(-10, 11):
    k_test = k_u + n * eps3  # using +n*ε³ so φ^(-(k_u + n*ε³)) = φ^(-k_u)*φ^(-n*ε³)
    val = phi ** (-k_test)
    err = abs(val - target) / target * 100
    print(f"    n = {n:+3d}: φ^(-({k_u:.6f} + {n}ε³)) = {val:.10f}  error = {err:.6f}%")

# What about k' = 33β - n*ε³?
print(f"\n  Looking for n such that φ^(-(33β - n·ε³)) = 1/134")
for n in range(-10, 11):
    k_test = k_u - n * eps3
    val = phi ** (-k_test)
    err = abs(val - target) / target * 100
    print(f"    n = {n:+3d}: φ^(-({k_u:.6f} - {n}ε³)) = {val:.10f}  error = {err:.6f}%")

# === Now try: what is the EXACT exponent for each? ===
print(f"\n{'=' * 72}")
print("EXACT EXPONENTS REQUIRED")
print("=" * 72)

# If exact = φ^(-k_exact), then k_exact = -log(exact)/log(φ)
k_exact_c = -math.log(m_c_mt_obs) / math.log(phi)
k_exact_s = -math.log(m_s_mb_obs) / math.log(phi)
k_exact_mu = -math.log(m_mu_mtau_obs) / math.log(phi)

print(f"\n  Charm: k_exact = -ln(1/134)/ln(φ) = {k_exact_c:.10f}")
print(f"    k_u = {k_u:.10f}")
print(f"    Δk = {k_exact_c - k_u:.10f}")
print(f"    Δk/ε³ = {(k_exact_c - k_u)/eps3:.10f}")
print(f"    Δk/ε³ (round) = {round((k_exact_c - k_u)/eps3)}")

print(f"\n  Strange: k_exact = -ln(m_s/m_b)/ln(φ) = {k_exact_s:.10f}")
print(f"    k_d = {k_d:.10f}")
print(f"    Δk = {k_exact_s - k_d:.10f}")
print(f"    Δk/ε³ = {(k_exact_s - k_d)/eps3:.10f}")
print(f"    Δk/ε³ (round) = {round((k_exact_s - k_d)/eps3)}")

print(f"\n  Muon: k_exact = -ln(m_μ/m_τ)/ln(φ) = {k_exact_mu:.10f}")
print(f"    k_l = {k_l:.10f}")
print(f"    Δk = {k_exact_mu - k_l:.10f}")
print(f"    Δk/ε³ = {(k_exact_mu - k_l)/eps3:.10f}")
print(f"    Δk/ε³ (round) = {round((k_exact_mu - k_l)/eps3)}")

# === Try combinations with φ identities ===
print(f"\n{'=' * 72}")
print("COMBINATIONS WITH φ-IDENTITIES")
print("=" * 72)

# φ-identities: φ^n - φ^{-n} ∈ ℤ for odd n
# n=1: 1, n=3: 4, n=5: 11, n=7: 29, n=9: 76, n=11: 199
# Also: φ^5 = 11 - φ^{-5} ≈ 11.090
# φ^5 - φ^{-5} = 11

# Try: what if k_u = 33β - 2ε³? 
# 33β = 33 * φ⁻¹/2 = 33/2 * φ⁻¹
# 33 = h¹¹ - 3 = 36 - 3

# Try: k_u_exact = 33β - ? 
# We need Δk = k_exact - k_u
# Check if Δk relates to ε³, ε², φ^(-n), etc.

for name, k_exact, k_orig, label in [("Charm", k_exact_c, k_u, "k_u=33β"),
                                       ("Strange", k_exact_s, k_d, "k_d=26β-φ⁻⁴"),
                                       ("Muon", k_exact_mu, k_l, "k_l=19β")]:
    dk = k_exact - k_orig
    print(f"\n  {name} ({label}):")
    print(f"    Δk = {dk:.10f}")
    print(f"    Δk × 16 = {dk*16:.10f}")
    print(f"    Δk / φ     = {dk/phi:.10f}")
    print(f"    Δk / φ⁻¹   = {dk/phi_inv:.10f}")
    print(f"    Δk / ε     = {dk/eps:.10f}")
    print(f"    Δk / ε²    = {dk/eps**2:.10f}")
    print(f"    Δk / ε³    = {dk/eps3:.10f}")
    print(f"    Δk / κ     = {dk/kappa:.10f}")
    print(f"    Δk × N_d   = {dk*44:.10f}")

# === Now try to find EXACT closed forms ===
# What if the exact formula uses φ^(-(33β - ε³)) = φ^(-33β) * φ^(ε³)?
print(f"\n{'=' * 72}")
print("EXACT FORMULA CANDIDATES")
print("=" * 72)

# Charm: try k_u + correction
# The correction should be a simple function of ε³
# φ^(-k_u) = 0.007393
# 1/134 = 0.007463
# Need to increase by factor 1.0094
# So need φ^(-Δk) = 1.0094 → Δk = -ln(1.0094)/ln(φ) = -0.0094/0.4812 = -0.0195
# So k_exact = k_u - 0.0195... 

# Let's try: k_exact = 33β - ε³  (subtract ε³ → k smaller → ratio larger because φ^(-k) is decreasing in k)
# φ^(-(33β - ε³)) = φ^(-33β) * φ^(ε³)
# = 0.007393 * φ^(0.003689)
# = 0.007393 * 1.00598
# = 0.007437

# Try: k_exact = 33β - 5ε³
# φ^(-(33β - 5ε³)) = 0.007393 * φ^(5*0.003689)
# = 0.007393 * φ^(0.01845)
# = 0.007393 * 1.0302
# = 0.007617 — too big

# Try: k_exact = 33β - 2ε³  
# φ^(-(33β - 2ε³)) = 0.007393 * φ^(2*0.003689)
# = 0.007393 * φ^(0.007378)
# = 0.007393 * 1.01196
# = 0.007481 — very close to 0.007463!

# Let me compute that precisely
for name, k_orig, target, sign_choices in [("Charm", k_u, 1/134, [-1, 1]),
                                            ("Strange", k_d, m_s_mb_obs, [-1, 1]),
                                            ("Muon", k_l, m_mu_mtau_obs, [-1, 1])]:
    print(f"\n  {name}: target = {target:.10f}")
    for sign in sign_choices:
        for n in range(-10, 11):
            k_test = k_orig + sign * n * eps3
            val = phi ** (-k_test)
            err = abs(val - target) / target * 100
            if err < 0.05:
                print(f"    ✅ k = {k_orig:.6f} {sign:+d}·{n}ε³ = {k_test:.10f} → {val:.10f}  err={err:.6e}%")
            elif err < 0.5:
                print(f"    🟡 k = {k_orig:.6f} {sign:+d}·{n}ε³ = {k_test:.10f} → {val:.10f}  err={err:.6f}%")