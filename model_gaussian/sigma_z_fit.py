"""
Ring Width vs Z — Linear Fit
sigma(z) = s0 + alpha * z
Reads per-slice results from slice_results.csv (produced by radial_fit_test.py).
"""

import numpy as np
from pathlib import Path

def r_squared(y_true, y_pred):
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    return 1.0 - ss_res / ss_tot

# Load CSV
data = np.genfromtxt(Path(__file__).parent / "slice_results.csv",
                     delimiter=",", skip_header=1)
z_data     = data[:, 0]
sigma_data = data[:, 3]

# Linear fit (full z range)
p = np.polyfit(z_data, sigma_data, 1)
alpha, s0 = p[0], p[1]

print(f"sigma(z) = {s0:.4f} + {alpha:.4f} * z   R² = {r_squared(sigma_data, np.polyval(p, z_data)):.4f}")
