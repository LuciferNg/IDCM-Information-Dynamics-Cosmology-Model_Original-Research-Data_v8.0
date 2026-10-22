#!/usr/bin/env python3
"""
V_EW structural analysis using v21 reverse compiler.
Tests the structural closure of V_EW formulas.
"""

import json, math, sys, os

# ── Structural constants ──
phi = (1 + math.sqrt(5)) / 2
eps = 1 / (4 * phi)
beta = 1 / (2 * phi)
kappa = 1/16
N_d = 44
L = 53/8
h11 = 36
h21 = 98

# ── Physical constants ──
M_P = 1.22089e19
V_EW_target = 246.22
m_t_target = 172.76

# Compute numeric values
phi80 = phi**80
M_P_over_phi80 = M_P / phi80
exact_exp = math.log(M_P / V_EW_target) / math.log(phi)

# ── Build test corpus ──
corpus = [
    # IDCM structural foundation
    "phi = (1 + sqrt(5)) / 2",
    "eps = phi ^ -1 / 4",
    "kappa = 1 / 16",
    "beta = phi ^ -1 / 2",
    "N_d = 44",
    "L = 53 / 8",
    "h11 = 36",
    "h21 = 98",
    "M_P = 1.22089e19",
    
    # Existing structural formulas
    "alpha_inv = 137",
    "V_cb = phi ^ 2 / 64",
    "lambda_CKM = phi ^ -3",
    "Omega_Lambda = 4 / (phi ^ 4 - 1)",
    "m_H = 2 * sqrt(kappa) * V_EW",
    "k_u = 33 * beta",
    "k_d = 26 * beta - phi ^ -4",
    "k_l = 19 * beta",
    
    # ── Candidate V_EW formulas ──
    # 1) Pure phi^80
    "V_EW_1 = M_P / phi ^ 80",
    # 2) N_d + h^11 form
    "V_EW_2 = M_P / phi ^ (N_d + h11)",
    # 3) 2N_d - 8 form
    "V_EW_3 = M_P / phi ^ (2 * N_d - 8)",
    # 4) With eps correction on exponent
    "V_EW_4 = M_P / phi ^ (80 - 4 * eps ^ 2)",
    # 5) With 5*eps^2 correction
    "V_EW_5 = M_P / phi ^ (80 - 5 * eps ^ 2)",
    # 6) Multiplicative form with correction 
    "V_EW_6 = M_P * (1 - eps ^ 2) / phi ^ 80",
    
    # ── m_t formulas ──
    "m_t_1 = V_EW_1 / sqrt(2)",
    "m_t_2 = M_P / (phi ^ 80 * sqrt(2))",
]

# ── Run v21 stress test ──
sys.path.insert(0, "/home/wsl/idcm_reverse_compiler")
from reverse_compiler_v21 import ReverseCompiler

compiler = ReverseCompiler(corpus)
closure = compiler._build_structural_closure()
results = compiler.stress_test(corpus)

print("="*75)
print("V21 STRUCTURAL CLOSURE ANALYSIS")
print("="*75)
print(f"\nClosure size: {len(closure)} symbols")
print(f"Closure: {sorted(closure)}")
print()

# Report per formula
print(f"{'Formula':<60s} {'Type':<15s} {'Conf':<8s}")
print("-"*83)
for f in corpus:
    clean, _, _ = compiler.prepare_corpus([f])
    key = clean[0] if clean else f
    if key in results['classifications']:
        r = results['classifications'][key]
    else:
        r = {"type": "unknown", "confidence": 0.0}
    conf = r['confidence']
    print(f"{f:<60s} {r['type']:<15s} {conf:<8.2f}")
    if r.get('indicators'):
        for ind in r['indicators']:
            print(f"{'':>60s} -> {ind}")

print()
print("="*75)
print("NUMERICAL VERIFICATION")
print("="*75)
print()

# V_EW candidates
candidates = [
    ("V_EW_1 (M_P/phi^80)", "V_EW_1 = M_P/phi^80", M_P_over_phi80),
    ("V_EW_2 (M_P/phi^(N_d+h11))", "V_EW_2 = M_P/phi^(N_d+h11)", M_P / phi**(N_d+h11)),
    ("V_EW_3 (M_P/phi^(2N_d-8))", "V_EW_3 = M_P/phi^(2N_d-8)", M_P / phi**(2*N_d-8)),
    ("V_EW_4 (80-4eps^2)", "V_EW_4", M_P / phi**(80 - 4*eps**2)),
    ("V_EW_5 (80-5eps^2)", "V_EW_5", M_P / phi**(80 - 5*eps**2)),
]

print(f"{'Name':<35s} {'V_EW(GeV)':<14s} {'err%':<10s} {'Type':<10s}")
print("-"*70)
for name, fkey, val in candidates:
    err = abs(val - V_EW_target)/V_EW_target*100
    r = results['classifications'].get(fkey, results['classifications'].get(name.split(" (")[0], {"type":"?"}))
    print(f"{name:<35s} {val:<14.4f} {err:<10.6f} {r['type']:<10s}")

print()
print(f"Observed V_EW = {V_EW_target} GeV")
print()

# m_t candidates
print(f"{'m_t formula':<45s} {'m_t(GeV)':<12s} {'err%':<10s}")
print("-"*68)

for name, val in [
    ("V_EW_target/sqrt(2)", V_EW_target/math.sqrt(2)),
    ("M_P/(phi^80*sqrt(2))", M_P/(phi80*math.sqrt(2))),
    ("V_EW_4/sqrt(2)", M_P/phi**(80-4*eps**2)/math.sqrt(2)),
]:
    err = abs(val - m_t_target)/m_t_target*100
    print(f"{name:<45s} {val:<12.4f} {err:<10.6f}")

print(f"\nObserved m_t = {m_t_target} GeV")

# ═══════════════════════════════════════════════
# KEY FINDING SUMMARY
# ═══════════════════════════════════════════════
print()
print("="*75)
print("FINDINGS")
print("="*75)

# 1. Pure phi^80 error
err_80 = abs(M_P_over_phi80 - V_EW_target)/V_EW_target*100
print(f"\n1. M_P/phi^80 = {M_P_over_phi80:.4f} GeV (error {err_80:.4f}%)")

# 2. Best eps-correction
err_4e2 = abs(M_P/phi**(80-4*eps**2) - V_EW_target)/V_EW_target*100
err_5e2 = abs(M_P/phi**(80-5*eps**2) - V_EW_target)/V_EW_target*100
print(f"2. M_P/phi^(80-4eps^2) = {M_P/phi**(80-4*eps**2):.4f} GeV (error {err_4e2:.4f}%)")
print(f"   M_P/phi^(80-5eps^2) = {M_P/phi**(80-5*eps**2):.4f} GeV (error {err_5e2:.4f}%)")

# 3. Exact exponent
print(f"3. Exact exponent = {exact_exp:.10f}")
print(f"   phi^exact_exp = {phi**exact_exp:.6e}")

# 4. phi^80 factor
correction_factor = V_EW_target * phi80 / M_P
print(f"4. Correction factor: C = V_EW * phi^80 / M_P = {correction_factor:.10f}")
print(f"   So: M_P / V_EW = phi^80 / {1/correction_factor:.10f}")
print(f"   Or: V_EW = M_P * {correction_factor:.10f} / phi^80")

# 5. m_t/V_EW check
print(f"\n5. m_t/V_EW = {m_t_target/V_EW_target:.10f}")
print(f"   1/sqrt(2) = {1/math.sqrt(2):.10f}")
print(f"   Error = {abs(m_t_target/V_EW_target - 1/math.sqrt(2))/(1/math.sqrt(2))*100:.4f}%")

# 6. Structure: what 80 means
print(f"\n6. phi^80 structural decomposition:")
print(f"   80 = N_d + h^11 = {N_d} + {h11}")
print(f"   80 = 2N_d - 8 = {2*N_d} - 8")
print(f"   h^11 = 3^2 x (phi^3 - phi^-3) = 9 x 4 = {9*4}")
print(f"   80 = N_d + 3^2 x (phi^3 - phi^-3)")

print(f"\n{'='*75}")
print("SUMMARY: V_EW from phi alone requires a structural exponent")
print(f"  M_P / phi^80 gives {err_80:.4f}% error")
print(f"  Best: 80 - 5*eps^2 = {80 - 5*eps**2:.10f}, error = {err_5e2:.4f}%")
print(f"  5*eps^2 = {5*eps**2:.10f} (target: {80 - exact_exp:.10f})")
print("="*75)
