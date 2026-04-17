"""
Ring Radius vs Z — Linear Fit
R_i(z) = Ri0 + beta_i * z
R_o(z) = Ro0 + beta_o * z
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
z_data  = data[:, 0]
Ri_data = data[:, 4]
Ro_data = data[:, 5]

# Linear fit
pi = np.polyfit(z_data, Ri_data, 1)
po = np.polyfit(z_data, Ro_data, 1)
beta_i, Ri0 = pi[0], pi[1]
beta_o, Ro0 = po[0], po[1]

print(f"R_i(z) = {Ri0:.4f} + {beta_i:.4f} * z   R² = {r_squared(Ri_data, np.polyval(pi, z_data)):.4f}")
print(f"R_o(z) = {Ro0:.4f} + {beta_o:.4f} * z   R² = {r_squared(Ro_data, np.polyval(po, z_data)):.4f}")
