"""
Radial Gaussian Fit — per z-slice plot
========================================
Loads fitted parameters from slice_results.csv and raw PIV data,
then plots PIV points vs double-Gaussian fit for each z level.
"""

import numpy as np
import matplotlib.pyplot as plt
import scipy.io
import csv
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
R_INNER_GEOM = 0.62
R_OUTER_GEOM = 1.35
Z_LEVELS     = np.array([1.0, 1.5, 2.0, 2.5, 3.0, 3.5])
Z_TOL        = 0.15
U_THRESHOLD  = 0.10

# ---------------------------------------------------------------------------
# Load PIV
# ---------------------------------------------------------------------------
static_dir = Path(__file__).parent.parent / "static"
x_piv = scipy.io.loadmat(static_dir / "x_piv.mat")["x_piv"].astype(float).ravel()
z_piv = scipy.io.loadmat(static_dir / "z_piv.mat")["z_piv"].astype(float).ravel()
u_piv = scipy.io.loadmat(static_dir / "u_piv.mat")["u_piv"].astype(float).ravel()
r_all = np.abs(x_piv)

# ---------------------------------------------------------------------------
# Load fitted parameters
# ---------------------------------------------------------------------------
fits = {}
with open(Path(__file__).parent / "slice_results.csv") as f:
    for row in csv.DictReader(f):
        fits[float(row["z"])] = {k: float(row[k]) for k in ("Ai", "Ao", "sigma", "Ri", "Ro", "R2")}

def double_gaussian(r, Ai, Ao, sigma, Ri, Ro):
    return (Ai * np.exp(-((r - Ri) ** 2) / (2 * sigma ** 2)) +
            Ao * np.exp(-((r - Ro) ** 2) / (2 * sigma ** 2)))

# ---------------------------------------------------------------------------
# Plot
# ---------------------------------------------------------------------------
r_fine = np.linspace(0, 8.5, 500)

fig, axes = plt.subplots(2, 3, figsize=(13, 8), sharey=True)
axes = axes.ravel()

for k, z0 in enumerate(Z_LEVELS):
    ax = axes[k]

    # PIV slice
    mask = np.abs(z_piv - z0) < Z_TOL
    r_sl = r_all[mask]
    u_sl = u_piv[mask]
    sort_idx = np.argsort(r_sl)
    r_sl, u_sl = r_sl[sort_idx], u_sl[sort_idx]

    # nearest fitted z
    z_key = min(fits.keys(), key=lambda z: abs(z - z0))
    p = fits[z_key]

    u_pred_act = double_gaussian(r_sl[u_sl > U_THRESHOLD], **{k: p[k] for k in ("Ai", "Ao", "sigma", "Ri", "Ro")})

    ax.plot(r_sl, u_sl, "k.", ms=4, label="PIV")
    ax.plot(r_fine, double_gaussian(r_fine, p["Ai"], p["Ao"], p["sigma"], p["Ri"], p["Ro"]),
            "r-", lw=1.5, label="Fit")
    ax.axvline(R_INNER_GEOM, ls="--", color="b", lw=0.8, label=r"$R_i^{geom}$")
    ax.axvline(R_OUTER_GEOM, ls="--", color="g", lw=0.8, label=r"$R_o^{geom}$")

    ax.set_title(
        f"z={z0:.1f} l   σ={p['sigma']:.3f}  Ri={p['Ri']:.3f}  Ro={p['Ro']:.3f}  R²={p['R2']:.3f}",
        fontsize=9
    )
    ax.set_xlabel("r / l")
    ax.set_ylabel("u / U_i")
    ax.set_ylim(0, 1.15)
    ax.grid(True, lw=0.4)
    if k == 0:
        ax.legend(fontsize=7)

fig.suptitle(r"Radial Gaussian Fit:  $u(r) = A_i\,G(r-R_i,\sigma) + A_o\,G(r-R_o,\sigma)$", fontsize=13)
fig.tight_layout()
plt.show()
