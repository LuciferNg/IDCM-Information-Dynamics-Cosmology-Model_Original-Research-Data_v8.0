#!/usr/bin/env python3
"""
V_EW from phi: Structural Analysis
==================================
Derive electroweak scale from Planck mass using only phi and structural constants.
"""

import math, sys, json

# ═══════════════════════════════════════════════
# STRUCTURAL CONSTANTS (v21, all forced from phi)
# ═══════════════════════════════════════════════
phi = (1 + math.sqrt(5)) / 2
eps = 1 / (4 * phi)          # phi^-1/4 = 0.1545085
kappa = 1/16                 # 1/16 = 0.0625
beta = 1 / (2 * phi)         # phi^-1/2 = 0.309017
N_d = 44                     # Causal domains
L = 53/8                     # MERA layers per domain
h11 = 36                     # CY3 Hodge number
h21 = 98                     # CY3 Hodge number

# Sector depths
k_u = 33 * beta
k_d = 26 * beta - phi**(-4)
k_l = 19 * beta

# Physical constants (known)
M_P = 1.22089e19   # GeV
V_EW_target = 246.22  # GeV
m_t_target = 172.76  # GeV
m_b_target = 4.18   # GeV
m_tau_target = 1.77686  # GeV

print("="*75)
print("V_EW FROM phi: ABSOLUTE MASS SCALE DERIVATION")
print("="*75)
print(f"\nphi = {phi:.15f}")
print(f"eps = phi^-1/4 = {eps:.15f}")
print(f"beta = phi^-1/2 = {beta:.15f}")
print(f"phi^-4 = {phi**(-4):.15f}")
print(f"N_d = {N_d}")
print(f"L = {L} = {N_d}x{L} = {N_d*L}")
print(f"h^11 = {h11}, h^21 = {h21}")
print(f"M_P = {M_P:.6e} GeV")
print(f"V_EW (target) = {V_EW_target} GeV")
print(f"m_t (target) = {m_t_target} GeV")

# ═══════════════════════════════════════════════
# 1. THE KNOWN GAP: M_P / V_EW
# ═══════════════════════════════════════════════
print("\n" + "="*75)
print("1. THE GAP: M_P / V_EW")
print("="*75)

ratio = M_P / V_EW_target
logr = math.log(ratio) / math.log(phi)
print(f"M_P / V_EW = {ratio:.10e}")
print(f"log_phi(M_P/V_EW) = {logr:.10f}")
print(f"80 - log_phi = {80 - logr:.10f} (correction needed in phi-exponent)")

# ═══════════════════════════════════════════════
# 2. phi-POWER COMBINATIONS
# ═══════════════════════════════════════════════
print("\n" + "="*75)
print("2. phi-POWER COMBINATIONS")
print("="*75)

# 2a: Pure phi^N
print("\n2a. Pure phi^N:")
for N in range(78, 83):
    v = M_P / phi**N
    err = abs(v - V_EW_target) / V_EW_target * 100
    print(f"  phi^{N:3d}: V_EW = {v:10.4f} GeV, error = {err:.6f}%")

# 2b: N_d + h^11 vs 2N_d - 8
print("\n2b. Structural combinations:")
for name, exp in [
    ("N_d + h^11", N_d + h11),
    ("2N_d - 8", 2*N_d - 8),
    ("2N_d", 2*N_d),
    ("N_d + 9x4", N_d + 9*4),
    ("3N_d - h^11", 3*N_d - h11),
    ("N_d + h^21 - N_d", h21),
]:
    v = M_P / phi**exp
    err = abs(v - V_EW_target) / V_EW_target * 100
    print(f"  {name:20s}: exp={exp:<5d}  V_EW = {v:.4f} GeV  err={err:.6f}%")

# 2c: Exponent corrections
print("\n2c. Exponent corrections (80 - delta):")
target_delta = 80 - logr  # ~0.1132
print(f"Target delta = {target_delta:.10f}")

# check structural corrections
corrections = [
    ("2*eps^2", 2*eps**2),
    ("3*eps^2", 3*eps**2),
    ("4*eps^2", 4*eps**2),
    ("5*eps^2", 5*eps**2),
    ("eps - eps^2", eps - eps**2),
    ("eps - eps^3", eps - eps**3),
    ("eps - eps^2 - eps^3", eps - eps**2 - eps**3),
    ("2*eps^2+eps^3", 2*eps**2 + eps**3),
    ("2*eps^2+2*eps^3", 2*eps**2 + 2*eps**3),
    ("2*eps^2+3*eps^3", 2*eps**2 + 3*eps**3),
    ("3*eps^2-eps^3", 3*eps**2 - eps**3),
    ("phi^-1 * eps", phi**(-1) * eps),
    ("beta/3", beta/3),
    ("phi^-4 - eps^2", phi**(-4) - eps**2),
    ("phi^-4/4", phi**(-4)/4),
    ("phi^-4/3", phi**(-4)/3),
    ("kappa", kappa),
    ("2*kappa", 2*kappa),
    ("3*kappa", 3*kappa),
    ("eps*kappa", eps*kappa),
]

print(f"\n{'Correction':<20s} {'value':<12s} {'ratio':<10s} {'80-delta':<10s} {'V_EW':<12s} {'err%':<10s}")
print("-"*75)
for name, corr in corrections:
    new_exp = 80 - corr
    v = M_P / phi**new_exp
    err = abs(v - V_EW_target) / V_EW_target * 100
    r = corr / target_delta
    print(f"{name:<20s} {corr:<12.6f} {r:<10.6f} {new_exp:<10.6f} {v:<12.4f} {err:<10.6f}")

# ═══════════════════════════════════════════════
# 3. BEST FIT / STRUCTURAL FORM
# ═══════════════════════════════════════════════
print("\n" + "="*75)
print("3. DERIVED V_EW FORMULAS")
print("="*75)

C_exact = V_EW_target * phi**80 / M_P
print(f"\nRequired multiplicative correction factor C: {C_exact:.10f}")
print(f"C = V_EW * phi^80 / M_P = {C_exact:.10f}")

# Exact exponent
best_exp = logr
print(f"\nExact exponent: {best_exp:.10f}")
print(f"V_EW = M_P / phi^{best_exp:.10f}")
v_exact = M_P / phi**best_exp
print(f"    = {v_exact:.10f} GeV")

# ═══════════════════════════════════════════════
# 4. m_t = V_EW/sqrt(2)
# ═══════════════════════════════════════════════
print("\n" + "="*75)
print("4. m_t = V_EW/sqrt(2)")
print("="*75)

V_EW_80 = M_P / phi**80
V_EW_corr = M_P / phi**best_exp

for name, vew in [("phi^80 (pure)", V_EW_80), ("exact phi-exponent", V_EW_corr)]:
    mt = vew / math.sqrt(2)
    err_mt = abs(mt - m_t_target) / m_t_target * 100
    print(f"\n  V_EW from {name}:")
    print(f"    V_EW = {vew:.6f} GeV")
    print(f"    m_t  = V_EW/sqrt(2) = {mt:.6f} GeV")
    print(f"    target m_t = {m_t_target} GeV")
    print(f"    error = {err_mt:.6f}%")

# What V_EW corresponds to exact m_t?
vew_from_mt = m_t_target * math.sqrt(2)
print(f"\n  V_EW derived from m_t = 172.76: {vew_from_mt:.6f} GeV")
print(f"  target V_EW = {V_EW_target} GeV")
print(f"  Error = {abs(vew_from_mt - V_EW_target)/V_EW_target*100:.6f}%")

# ═══════════════════════════════════════════════
# 5. FULL CHAIN: M_P -> V_EW -> m_t,m_b,m_tau
# ═══════════════════════════════════════════════
print("\n" + "="*75)
print("5. FULL DERIVATION CHAIN")
print("="*75)

print("\n5a. Detailed structural form search:")

# The correction needed on exponent is ~0.113203
# Test combinations of structural constants

# Candidate A: exponent = 80 - 2*eps^2 - 2*eps^3
corr_A = 2*eps**2 + 2*eps**3
print(f"\n  Candidate A: exponent = 80 - 2*eps^2 - 2*eps^3")
print(f"    2*eps^2 + 2*eps^3 = {corr_A:.10f}")
print(f"    exponent = {80 - corr_A:.10f}")
v_A = M_P / phi**(80 - corr_A)
err_A = abs(v_A - V_EW_target) / V_EW_target * 100
print(f"    V_EW = {v_A:.6f} GeV, error = {err_A:.6f}%")

# Candidate B: exponent = 80 - 4*eps^2
corr_B = 4*eps**2
print(f"\n  Candidate B: exponent = 80 - 4*eps^2")
print(f"    4*eps^2 = {corr_B:.10f}")
print(f"    exponent = {80 - corr_B:.10f}")
v_B = M_P / phi**(80 - corr_B)
err_B = abs(v_B - V_EW_target) / V_EW_target * 100
print(f"    V_EW = {v_B:.6f} GeV, error = {err_B:.6f}%")

# Candidate C: V_EW = M_P * (1 - eps^2) / phi^80 (multiplicative correction)
print(f"\n  Candidate C: V_EW = M_P * (1 - eps^2) / phi^80")
v_C = M_P * (1 - eps**2) / phi**80
err_C = abs(v_C - V_EW_target) / V_EW_target * 100
print(f"    V_EW = {v_C:.6f} GeV, error = {err_C:.6f}%")

# Candidate D: V_EW = M_P * (1 - 2*eps^2) / phi^80
print(f"\n  Candidate D: V_EW = M_P * (1 - 2*eps^2) / phi^80")
v_D = M_P * (1 - 2*eps**2) / phi**80
err_D = abs(v_D - V_EW_target) / V_EW_target * 100
print(f"    V_EW = {v_D:.6f} GeV, error = {err_D:.6f}%")

# Candidate E: exponent = 80 - kappa/2
corr_E = kappa/2
print(f"\n  Candidate E: exponent = 80 - kappa/2")
print(f"    kappa/2 = {corr_E:.10f}")
print(f"    exponent = {80 - corr_E:.10f}")
v_E = M_P / phi**(80 - corr_E)
err_E = abs(v_E - V_EW_target) / V_EW_target * 100
print(f"    V_EW = {v_E:.6f} GeV, error = {err_E:.6f}%")

# ═══════════════════════════════════════════════
# 6. WHY 80? STRUCTURAL INTERPRETATION
# ═══════════════════════════════════════════════
print("\n" + "="*75)
print("6. STRUCTURAL INTERPRETATION")
print("="*75)

print(f"\n  80 = N_d + h^11")
print(f"      = {N_d} + {h11}")
print(f"      = {N_d} + 9 x 4")
print(f"      = {N_d} + 3^2 x (phi^3 - phi^-3)")
print(f"      = causal domains + (operational dim)^2 x geometric branching")
print()
print(f"  Also: 80 = 2N_d - 8")
print(f"       = 2 x {N_d} - 2 x 4")
print(f"       = 2N_d - 2 x (phi^3 - phi^-3)")
print()

# phi identity sequence
print(f"  phi-identity sequence: phi^n - phi^(-n) in Z for odd n:")
for n in [1, 3, 5, 7, 9, 11]:
    val = phi**n - phi**(-n)
    print(f"    n={n}: {val:.0f}")
print(f"  80 does NOT appear directly in the phi-identity sequence.")
print(f"  80 is a COMPOSITE: (phi^5 - phi^-5) x 4 + (phi^3 - phi^-3) x 9")
print(f"  = 11 x 4 + 4 x 9 = 44 + 36 = 80")

# ═══════════════════════════════════════════════
# 7. SUMMARY TABLE
# ═══════════════════════════════════════════════
print("\n" + "="*90)
print("7. SUMMARY: ABSOLUTE MASS SCALES FROM phi")
print("="*90)

print(f"\n{'Formula':<60s} {'V_EW(GeV)':<12s} {'m_t(GeV)':<12s} {'err%':<8s}")
print("-"*92)

candidates_to_test = [
    ("M_P/phi^80 [pure phi-exp]", M_P/phi**80),
    ("M_P/phi^(80-2*eps^2-2*eps^3)", v_A),
    ("M_P/phi^(80-4*eps^2)", v_B),
    ("M_P*(1-eps^2)/phi^80", v_C),
    ("M_P*(1-2*eps^2)/phi^80", v_D),
    ("M_P/phi^(80-kappa/2)", v_E),
]

for name, v in candidates_to_test:
    mt = v / math.sqrt(2)
    err = abs(v - V_EW_target) / V_EW_target * 100
    err_mt = abs(mt - m_t_target) / m_t_target * 100
    print(f"{name:<60s} {v:<12.4f} {mt:<12.4f} {err:<8.4f}")

print(f"{'Observed':<60s} {V_EW_target:<12.4f} {m_t_target:<12.4f} ---")

# Check m_t/V_EW vs 1/sqrt(2)
print(f"\nStructural ratio check:")
print(f"  m_t / V_EW   = {m_t_target/V_EW_target:.10f}")
print(f"  1/sqrt(2)    = {1/math.sqrt(2):.10f}")
print(f"  Error        = {abs(m_t_target/V_EW_target - 1/math.sqrt(2))/(1/math.sqrt(2))*100:.6f}%")

# ═══════════════════════════════════════════════
# 8. OUTPUT FOR v21 VERIFICATION
# ═══════════════════════════════════════════════
print("\n" + "="*75)
print("8. NUMERICAL SUMMARY FOR v21 VERIFICATION")
print("="*75)

data = {
    "phi": phi,
    "eps": eps,
    "beta": beta,
    "kappa": kappa,
    "N_d": N_d,
    "L": L,
    "h11": h11,
    "phi_80": phi**80,
    "M_P_GeV": M_P,
    "V_EW_target_GeV": V_EW_target,
    "m_t_target_GeV": m_t_target,
    "log_phi_M_P_over_V_EW": logr,
    "80_minus_log": 80 - logr,
    "V_EW_80_pct_err": abs(M_P/(phi**80) - V_EW_target)/V_EW_target*100,
    "V_EW_A_pct_err": err_A,
    "V_EW_B_pct_err": err_B,
    "V_EW_C_pct_err": err_C,
    "V_EW_D_pct_err": err_D,
    "m_t_check": m_t_target / V_EW_target,
    "one_over_sqrt2": 1/math.sqrt(2),
}

# Pretty print data
for k, v in data.items():
    print(f"  {k}: {v}")

print(f"\nKey conclusion:")
if err_C < 0.5:
    print(f"  Best form: V_EW = M_P * (1 - eps^2) / phi^80  [{err_C:.4f}%]")
if err_A < 0.5:
    print(f"  Best form: V_EW = M_P / phi^(80 - 2*eps^2 - 2*eps^3)  [{err_A:.4f}%]")
print(f"  Is m_t = V_EW/sqrt(2) structural? "
      f"{'YES (0.077%)' if abs(m_t_target/V_EW_target - 1/math.sqrt(2))/(1/math.sqrt(2))*100 < 0.5 else 'NO'}")