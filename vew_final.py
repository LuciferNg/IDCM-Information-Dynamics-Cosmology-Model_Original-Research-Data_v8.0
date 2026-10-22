#!/usr/bin/env python3
"""V_EW from phi: Final analysis"""
import math

phi = (1 + math.sqrt(5)) / 2
eps = 1 / (4 * phi)
beta = 1 / (2 * phi)
kappa = 1/16
N_d = 44
L = 53/8
h11 = 36

M_P = 1.22089e19
V_EW_t = 246.22
m_t_t = 172.76

ratio = M_P / V_EW_t
logr = math.log(ratio) / math.log(phi)
target_delta = 80 - logr

# Structural corrections
candidates = [
    ("4*eps^2", 4*eps**2),
    ("5*eps^2", 5*eps**2),
    ("phi^-4 - eps^2", phi**(-4) - eps**2),
    ("beta/3", beta/3),
    ("2*kappa", 2*kappa),
    ("eps - eps^2 - eps^3", eps - eps**2 - eps**3),
]

print("="*68)
print("V_EW FROM phi: ABSOLUTE MASS SCALE DERIVATION")
print("="*68)
print(f"\nphi = {phi:.10f}")
print(f"eps = {eps:.10f}")
print(f"beta = {beta:.10f}")
print(f"kappa = {kappa}")
print(f"N_d = {N_d}, h^11 = {h11}, 80 = N_d + h^11 = {N_d + h11}")
print(f"\nM_P = {M_P:.4e} GeV")
print(f"V_EW = {V_EW_t} GeV")
print(f"m_t = {m_t_t} GeV")
print(f"\n{'─'*68}")
print("1. THE GAP")
print(f"M_P / V_EW = {ratio:.8e}")
print(f"log_phi(M_P/V_EW) = {logr:.10f}")
print(f"80 - log_phi = {target_delta:.10f}  ← correction needed")
print(f"phi^80 = {phi**80:.8e}")
print(f"Pure phi^80 error: {abs(M_P/phi**80 - V_EW_t)/V_EW_t*100:.4f}%")
print(f"\n{'─'*68}")
print("2. STRUCTURAL CORRECTIONS TO EXPONENT")
print(f"{'Correction':<20s} {'delta':<12s} {'exp':<12s} {'V_EW(GeV)':<12s} {'err%':<10s}")
print("-"*66)
for name, d in candidates:
    exp = 80 - d
    v = M_P / phi**exp
    err = abs(v - V_EW_t)/V_EW_t*100
    print(f"{name:<20s} {d:<12.8f} {exp:<12.8f} {v:<12.4f} {err:<10.4f}")
print(f"\n{'─'*68}")
print("3. m_t CHECK")
v4 = M_P / phi**(80 - 4*eps**2)
v5 = M_P / phi**(80 - 5*eps**2)
print(f"V_EW(tgt)   = {V_EW_t} -> m_t = V_EW/sqrt(2) = {V_EW_t/math.sqrt(2):.4f} GeV (err: {abs(V_EW_t/math.sqrt(2)-m_t_t)/m_t_t*100:.4f}%)")
print(f"V_EW(80-4e2) = {v4:.4f} -> m_t = V_EW/sqrt(2) = {v4/math.sqrt(2):.4f} GeV (err: {abs(v4/math.sqrt(2)-m_t_t)/m_t_t*100:.4f}%)")
print(f"V_EW(80-5e2) = {v5:.4f} -> m_t = V_EW/sqrt(2) = {v5/math.sqrt(2):.4f} GeV (err: {abs(v5/math.sqrt(2)-m_t_t)/m_t_t*100:.4f}%)")
print(f"\n{'─'*68}")
print("4. SUMMARY")
print(f"80 = N_d + h^11 = {N_d} + {h11} = {N_d + h11} = 2*{N_d} - 8 = {2*N_d - 8}")
print(f"  Where h^11 = 3^2 * (phi^3 - phi^-3) = 9 * 4 = {h11}")
print(f"\nBest structural form: V_EW = M_P / phi^(80 - 4*eps^2)")
print(f"  = {v4:.4f} GeV (err: {abs(v4-V_EW_t)/V_EW_t*100:.4f}%)")
print(f"  -> m_t = V_EW/sqrt(2) = {v4/math.sqrt(2):.4f} GeV (err: {abs(v4/math.sqrt(2)-m_t_t)/m_t_t*100:.4f}%)")
print(f"\nAlt: V_EW = M_P / phi^(80 - 5*eps^2)")
print(f"  = {v5:.4f} GeV (err: {abs(v5-V_EW_t)/V_EW_t*100:.4f}%)")
print(f"  -> m_t = V_EW/sqrt(2) = {v5/math.sqrt(2):.4f} GeV (err: {abs(v5/math.sqrt(2)-m_t_t)/m_t_t*100:.4f}%)")
print(f"\nNOTES:")
print(f"  - 5*eps^2 = {5*eps**2:.10f} vs target {target_delta:.10f} (off by {abs(5*eps**2-target_delta):.8f})")
print(f"  - 4*eps^2 = {4*eps**2:.10f} vs target {target_delta:.10f} (off by {abs(4*eps**2-target_delta):.8f})")
print(f"  - 4*eps^2 gives 0.85% error on V_EW but only 0.077% on m_t (!)")