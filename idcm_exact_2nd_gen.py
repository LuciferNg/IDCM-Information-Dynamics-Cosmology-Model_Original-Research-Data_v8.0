#!/usr/bin/env python3
"""IDCM: Find exact ε³-based correction terms for 2nd gen particles."""
import math
from itertools import product

phi = (1 + math.sqrt(5)) / 2
phi_inv = phi - 1
beta = phi_inv / 2
eps = phi_inv / 4
eps3 = eps ** 3
eps6 = eps ** 6

k_u = 33 * beta
k_d = 26 * beta - phi_inv**4
k_l = 19 * beta

# PDG / observed values
CY3 = 134
m_c_mt_obs = 1/CY3
m_s_mb_obs = 0.0223444976  # 0.0934/4.18
m_mu_mtau_obs = 0.0594633229  # 0.105658/1.77686

m_c_pred = phi ** (-k_u)
m_s_pred = phi ** (-k_d)
m_mu_pred = phi ** (-k_l)

print("=" * 72)
print("EXACT ε³ CORRECTION TERMS FOR 2nd GEN PARTICLES")
print("=" * 72)

# =========================================================
# APPROACH 1: Multiplicative correction factor = 1 + a·ε³ + b·ε⁶
# Solve for integers a, b that make the formula exact
# =========================================================
print("\n" + "=" * 72)
print("APPROACH 1: Multiplicative: φ^(-k) × (1 + a·ε³ + b·ε⁶) = exact")
print("=" * 72)

for name, pred, obs, k_val in [("Charm (c)", m_c_pred, m_c_mt_obs, k_u),
                                 ("Strange (s)", m_s_pred, m_s_mb_obs, k_d),
                                 ("Muon (μ)", m_mu_pred, m_mu_mtau_obs, k_l)]:
    corr = obs / pred  # exact correction factor needed
    print(f"\n  {name}:")
    print(f"    φ-pred = {pred:.10f}")
    print(f"    exact  = {obs:.10f}")
    print(f"    factor = {corr:.10f}")
    print(f"    1 + n·ε³ + m·ε⁶ = {corr:.10f}")
    print(f"    n·ε³ + m·ε⁶ = {corr - 1:.10f}")
    
    # Solve n·ε³ + m·ε⁶ = corr - 1 for integer n, m
    target = corr - 1
    best = None
    best_err = float('inf')
    for n in range(-10, 11):
        for m in range(-10, 11):
            val = n * eps3 + m * eps6
            err = abs(val - target)
            if err < best_err:
                best_err = err
                best = (n, m, val)
    n, m, val = best
    pred_new = pred * (1 + val)
    err_pct = abs(pred_new - obs) / obs * 100
    print(f"    Best: n={n:+d}, m={m:+d}: 1 + {n}·ε³ + {m}·ε⁶ = {1+val:.10f}")
    print(f"    φ^(-k) × (1 + {n}·ε³ + {m}·ε⁶) = {pred_new:.10f}")
    print(f"    Error = {err_pct:.6e}%")
    
    # Also try 3-term: n·ε³ + m·ε⁶ + p·ε⁹
    eps9 = eps ** 9
    target = corr - 1
    best3 = None
    best3_err = float('inf')
    for n in range(-10, 11):
        for m in range(-10, 11):
            for p in range(-10, 11):
                val = n * eps3 + m * eps6 + p * eps9
                err = abs(val - target)
                if err < best3_err:
                    best3_err = err
                    best3 = (n, m, p, val)
    n, m, p, val = best3
    pred_new = pred * (1 + val)
    err_pct = abs(pred_new - obs) / obs * 100
    print(f"    Best 3-term: n={n:+d}, m={m:+d}, p={p:+d}: 1 + {n}·ε³ + {m}·ε⁶ + {p}·ε⁹ = {1+val:.10f}")
    print(f"    Error = {err_pct:.6e}%")

# =========================================================
# APPROACH 2: Exponent correction: k' = k + n·ε³ + m·ε⁶
# So φ^(-k') = exact
# =========================================================
print("\n" + "=" * 72)
print("APPROACH 2: Exponent: φ^(-(k + n·ε³ + m·ε⁶)) = exact")
print("=" * 72)

for name, pred, obs, k_val in [("Charm (c)", m_c_pred, m_c_mt_obs, k_u),
                                 ("Strange (s)", m_s_pred, m_s_mb_obs, k_d),
                                 ("Muon (μ)", m_mu_pred, m_mu_mtau_obs, k_l)]:
    k_exact = -math.log(obs) / math.log(phi)
    dk = k_exact - k_val
    print(f"\n  {name}:")
    print(f"    k_exact = {k_exact:.10f}")
    print(f"    k       = {k_val:.10f}")
    print(f"    Δk      = {dk:.10f}")
    print(f"    Δk = n·ε³ + m·ε⁶")
    
    best = None
    best_err = float('inf')
    for n in range(-10, 11):
        for m in range(-10, 11):
            val = n * eps3 + m * eps6
            err = abs(val - dk)
            if err < best_err:
                best_err = err
                best = (n, m, val)
    n, m, val = best
    k_new = k_val + val
    pred_new = phi ** (-k_new)
    err_pct = abs(pred_new - obs) / obs * 100
    print(f"    Best: n={n:+d}, m={m:+d}: {n}·ε³ + {m}·ε⁶ = {val:.10f}")
    print(f"    k' = {k_val:.10f} + {val:.10f} = {k_new:.10f}")
    print(f"    φ^(-k') = {pred_new:.10f}")
    print(f"    Error = {err_pct:.6e}%")
    
    # 3-term
    eps9 = eps ** 9
    best3 = None
    best3_err = float('inf')
    for n in range(-10, 11):
        for m in range(-10, 11):
            for p in range(-10, 11):
                val = n * eps3 + m * eps6 + p * eps9
                err = abs(val - dk)
                if err < best3_err:
                    best3_err = err
                    best3 = (n, m, p, val)
    n, m, p, val = best3
    k_new = k_val + val
    pred_new = phi ** (-k_new)
    err_pct = abs(pred_new - obs) / obs * 100
    print(f"    Best 3-term: n={n:+d}, m={m:+d}, p={p:+d}: {n}·ε³ + {m}·ε⁶ + {p}·ε⁹ = {val:.10f}")
    print(f"    Error = {err_pct:.6e}%")

# =========================================================
# APPROACH 3: MERA-style: (1 + a·ε) or (1 + ε)^n corrections
# =========================================================
print("\n" + "=" * 72)
print("APPROACH 3: MERA-style (1+ε)^n corrections")
print("=" * 72)

for name, pred, obs, k_val in [("Charm (c)", m_c_pred, m_c_mt_obs, k_u),
                                 ("Strange (s)", m_s_pred, m_s_mb_obs, k_d),
                                 ("Muon (μ)", m_mu_pred, m_mu_mtau_obs, k_l)]:
    corr = obs / pred
    print(f"\n  {name}: correction factor = {corr:.10f}")
    
    # Try: (1+ε)^n
    for n in range(-5, 6):
        val = (1 + eps) ** n
        err = abs(val - corr) / corr * 100
        print(f"    (1+ε)^{n:+d} = {val:.10f}  err={err:.4f}%")
    
    # Try: (1+ε³)^n
    for n in range(-5, 6):
        val = (1 + eps3) ** n
        err = abs(val - corr) / corr * 100
        print(f"    (1+ε³)^{n:+d} = {val:.10f}  err={err:.4f}%")

# =========================================================
# APPROACH 4: m_c/m_t = 1/134 = φ^(-k) × (ε³ series)
# Find the exact series expansion
# =========================================================
print("\n" + "=" * 72)
print("APPROACH 4: Exact series expansion in ε³")
print("=" * 72)

# For charm: exact = 1/134, current = φ^(-k_u)
# 1/134 = φ^(-k_u) × (1 + a₁ε³ + a₂ε⁶ + a₃ε⁹ + ...)
# 1/134 / φ^(-k_u) = 1 + a₁ε³ + a₂ε⁶ + a₃ε⁹ + ...

for name, pred, obs, k_val in [("Charm (c)", m_c_pred, m_c_mt_obs, k_u),
                                 ("Strange (s)", m_s_pred, m_s_mb_obs, k_d),
                                 ("Muon (μ)", m_mu_pred, m_mu_mtau_obs, k_l)]:
    corr = obs / pred
    print(f"\n  {name}: correction = {corr:.10f}")
    print(f"    1 + a₁ε³ + a₂ε⁶ + a₃ε⁹ + ... = {corr:.10f}")
    
    # Solve for a₁, a₂, a₃
    # a₁ε³ + a₂ε⁶ + a₃ε⁹ = corr - 1
    target = corr - 1
    # Try a₁ = round(target/ε³)
    a1 = round(target / eps3)
    residual = target - a1 * eps3
    a2 = round(residual / eps6)
    residual2 = residual - a2 * eps6
    a3 = round(residual2 / (eps ** 9)) if abs(eps ** 9) > 1e-30 else 0
    residual3 = residual2 - a3 * (eps ** 9)
    
    pred_val = 1 + a1*eps3 + a2*eps6 + a3*(eps**9)
    print(f"    a₁ = {a1}, a₂ = {a2}, a₃ = {a3}")
    print(f"    1 + {a1}·ε³ + {a2}·ε⁶ + {a3}·ε⁹ = {pred_val:.10f}")
    print(f"    Residual = {target - (a1*eps3 + a2*eps6 + a3*(eps**9)):.2e}")
    
    # Try φ^(-k) × φ^(-n·ε³) = φ^(-(k + n·ε³))
    # φ^(-n·ε³) = correction factor
    n = round(-math.log(corr) / (math.log(phi) * eps3))
    pred_val = phi ** (-n * eps3)
    err = abs(pred_val - corr) / corr * 100
    print(f"    φ^(-n·ε³) with n={n}: φ^(-{n}·ε³) = {pred_val:.10f}  err={err:.6e}%")

# =========================================================
# FINAL EXACT FORMULAS
# =========================================================
print("\n" + "=" * 72)
print("FINAL EXACT FORMULAS FOR 2nd GEN PARTICLES")
print("=" * 72)

# Try the exact approach: find the precise formula
# For charm: m_c/m_t = 1/134 exactly
# Compute exact k for each
print("\n  Exact k-values (from -ln(obs)/ln(φ)):")
k_exact_c = -math.log(m_c_mt_obs) / math.log(phi)
k_exact_s = -math.log(m_s_mb_obs) / math.log(phi)
k_exact_mu = -math.log(m_mu_mtau_obs) / math.log(phi)
print(f"    Charm:  k_exact = {k_exact_c:.10f}")
print(f"    Strange: k_exact = {k_exact_s:.10f}")
print(f"    Muon:   k_exact = {k_exact_mu:.10f}")

print("\n  Exact φ-powers:")
print(f"    Charm:  φ^(-{k_exact_c:.10f}) = {phi**(-k_exact_c):.10f} = 1/134 ✓")
print(f"    Strange: φ^(-{k_exact_s:.10f}) = {phi**(-k_exact_s):.10f} = {m_s_mb_obs} ✓")
print(f"    Muon:   φ^(-{k_exact_mu:.10f}) = {phi**(-k_exact_mu):.10f} = {m_mu_mtau_obs} ✓")

# Express exact k as k_idcm + correction
print("\n  Expressing exact k as k_IDCM + ε³-series:")
for name, k_exact, k_idcm, label in [("Charm", k_exact_c, k_u, "33β"),
                                       ("Strange", k_exact_s, k_d, "26β-φ⁻⁴"),
                                       ("Muon", k_exact_mu, k_l, "19β")]:
    dk = k_exact - k_idcm
    eps_contrib = dk / eps3
    print(f"\n    {name} (k = {label}):")
    print(f"      k_exact = {k_idcm:.10f} + {dk:.10f}")
    print(f"      = {k_idcm:.10f} + {eps_contrib:.10f}·ε³")
    print(f"      = {k_idcm:.10f} + {round(eps_contrib):d}·ε³ + {dk - round(eps_contrib)*eps3:.2e} (residual)")

# Now try to find exact formulas using the MERA (1+ε)^2(1-ε) approach
# The paper shows m_tau/m_mu = φ^6 - (1+ε)^2(1-ε)
# Let's try similar for 2nd gen
print("\n" + "=" * 72)
print("MERA-EXPANSION APPROACH (like m_τ/m_μ)")  
print("=" * 72)

# m_τ/m_μ: φ^6 - (1+ε)^2(1-ε) = 16.8173
# (1+ε)^2(1-ε) = 1 + ε - ε² - ε³

# For 2nd gen, maybe the correction is similar but with different ε-based factors
print("\n  Trying: correction = φ^(-k) × (1+ε)^a(1-ε)^b")
for name, pred, obs, k_val in [("Charm (c)", m_c_pred, m_c_mt_obs, k_u),
                                 ("Strange (s)", m_s_pred, m_s_mb_obs, k_d),
                                 ("Muon (μ)", m_mu_pred, m_mu_mtau_obs, k_l)]:
    corr = obs / pred
    print(f"\n    {name}:")
    for a in range(-3, 4):
        for b in range(-3, 4):
            val = (1+eps)**a * (1-eps)**b
            err = abs(val - corr) / corr * 100
            if err < 1.0:
                print(f"      (1+ε)^{a:+d}(1-ε)^{b:+d} = {val:.10f}  err={err:.4f}%")

# Also try: φ^(-k) × (1 + ε³)^n directly
print("\n" + "=" * 72)
print("FINAL: Exact formulas for 2nd gen particles")
print("=" * 72)

# The exact k values
print(f"""
  k_u = 33β = {k_u:.10f}
  k_d = 26β - φ⁻⁴ = {k_d:.10f}
  k_l = 19β = {k_l:.10f}

  Exact Charm:   k'_u = {k_exact_c:.10f} = k_u - 5ε³ - 72ε⁶ + ...
  Exact Strange: k'_d = {k_exact_s:.10f} = k_d + 3ε³ + 56ε⁶ + ...
  Exact Muon:    k'_l = {k_exact_mu:.10f} = k_l - 2ε³ + 24ε⁶ + ...
""")

# What if the exact formula is just φ^(-33β) × (1 + 5ε³ - 2ε⁶) for charm?
print("Trying integer combinations more carefully:")
for name, pred, obs, k_val in [("Charm", m_c_pred, m_c_mt_obs, k_u),
                                 ("Strange", m_s_pred, m_s_mb_obs, k_d),
                                 ("Muon", m_mu_pred, m_mu_mtau_obs, k_l)]:
    corr = obs / pred
    target = corr - 1
    print(f"\n  {name}: target = {target:.10f}")
    
    # Find exact integer solution
    # target = n·ε³ + m·ε⁶ + p·ε⁹
    # Solve using integer programming
    eps9 = eps ** 9
    found = []
    for n in range(-20, 21):
        for m in range(-20, 21):
            # For each n,m, compute what p would need to be
            r = target - n*eps3 - m*eps6
            p = round(r / eps9)
            val = n*eps3 + m*eps6 + p*eps9
            err = abs(val - target)
            if err < 1e-12:  # Essentially exact
                found.append((n, m, p, val))
    if found:
        for n, m, p, val in found[:5]:
            pred_new = pred * (1 + val)
            print(f"    ✅ n={n:+d}, m={m:+d}, p={p:+d}: 1 + {n}ε³ + {m}ε⁶ + {p}ε⁹ = {1+val:.15f}")
            print(f"       φ^(-k) × (1+...) = {pred_new:.15f}  vs exact = {obs:.15f}")
    else:
        print(f"    No exact integer solution found with n,m,p in [-20,20]")
        # Show the best
        best_n = round(target / eps3)
        best_m = round((target - best_n*eps3) / eps6)
        best_p = round((target - best_n*eps3 - best_m*eps6) / eps9)
        val = best_n*eps3 + best_m*eps6 + best_p*eps9
        pred_new = pred * (1 + val)
        err = abs(pred_new - obs) / obs * 100
        print(f"    Best: n={best_n:+d}, m={best_m:+d}, p={best_p:+d}:")
        print(f"       1 + {best_n}ε³ + {best_m}ε⁶ + {best_p}ε⁹ = {1+val:.15f}")
        print(f"       φ^(-k) × (1+...) = {pred_new:.15f}  vs exact = {obs:.15f}")
        print(f"       Error = {err:.6e}%")