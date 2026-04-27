"""
Amplitude Decay vs Z — Exponential vs Linear Fit
Reads per-slice results from slice_results.csv (produced by radial_fit_test.py).
"""

import numpy as np
from pathlib import Path

def r_squared(y_true, y_pred):
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    return 1.0 - ss_res / ss_tot

def fit_exponential(z, A):
    """Linearise via log: log(A) = log(A0) - z/lambda, then polyfit."""
    p = np.polyfit(z, np.log(A), 1)
    lam = -1.0 / p[0]
    A0  = np.exp(p[1])
    return A0, lam, A0 * np.exp(-z / lam)

# Load CSV
data = np.genfromtxt(Path(__file__).parent / "slice_results.csv",
                     delimiter=",", skip_header=1)
z_data = data[:, 0]
Ai     = data[:, 1]
Ao     = data[:, 2]

# Exponential fits
A0_i, lam_i, Ai_exp = fit_exponential(z_data, Ai)
A0_o, lam_o, Ao_exp = fit_exponential(z_data, Ao)

# Linear fits for comparison
Ai_lin = np.polyval(np.polyfit(z_data, Ai, 1), z_data)
Ao_lin = np.polyval(np.polyfit(z_data, Ao, 1), z_data)

print("Inner ring:")
print(f"  Exp:    A_i(z) = {A0_i:.4f} * exp(-z / {lam_i:.4f})   R² = {r_squared(Ai, Ai_exp):.4f}")
print(f"  Linear:                                                 R² = {r_squared(Ai, Ai_lin):.4f}")
print("Outer ring:")
print(f"  Exp:    A_o(z) = {A0_o:.4f} * exp(-z / {lam_o:.4f})   R² = {r_squared(Ao, Ao_exp):.4f}")
print(f"  Linear:                                                 R² = {r_squared(Ao, Ao_lin):.4f}")
