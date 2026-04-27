"""
Radial Gaussian Fit — per z-slice
===================================
Goal
----
For each horizontal slice of the drone wake (a fixed height z below the rotors),
independently fit the measured velocity profile u(r) with a sum of two Gaussians:

    u(r) = A_i · G(r – R_i, σ)  +  A_o · G(r – R_o, σ)

where
  • r          = radial distance from the drone center              [l]
  • A_i, A_o   = amplitudes of the inner / outer velocity rings     [U_i]
  • R_i, R_o   = radial positions of the inner / outer ring peaks   [l]
  • σ          = shared Gaussian width (how wide each ring is)      [l]
  • G(x, σ)   = exp(–x² / 2σ²)  — a Gaussian centered at 0

Only points where the velocity exceeds a threshold (u > U_THRESHOLD)
are used — these are called "active" points.

Physical units (non-dimensionalised)
  l   = 32.5 mm — the Crazyflie arm length, used as the length scale
  U_i = induced velocity at hover, used as the velocity scale
  All r, z, R_i, R_o, σ are in [l]; all u, A_i, A_o are in [U_i]
"""

# ---------------------------------------------------------------------------
# BLOCK 1 — Imports
# ---------------------------------------------------------------------------

import numpy as np
import scipy.io
from pathlib import Path
from scipy.optimize import minimize

# ---------------------------------------------------------------------------
# BLOCK 2 — Constants + math functions
# ---------------------------------------------------------------------------

# Geometric reference radii at z = 0 (propeller tip positions)  [l]
R_INNER_GEOM = 0.62
R_OUTER_GEOM = 1.35


def gaussian(r, mu, sigma):
    """Amplitude-normalised Gaussian: exp( -(r-mu)^2 / 2sigma^2 )"""
    r = np.asarray(r, dtype=float)
    return np.exp(-((r - mu) ** 2) / (2.0 * sigma ** 2))


def double_gaussian_radial(r, Ai, Ao, sigma, Ri, Ro):
    """u(r) = Ai·G(r-Ri, sigma) + Ao·G(r-Ro, sigma)"""
    return Ai * gaussian(r, Ri, sigma) + Ao * gaussian(r, Ro, sigma)


def r_squared(y_true, y_pred):
    """R² = 1 - SS_res / SS_tot"""
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    return 1.0 - ss_res / ss_tot


def load_piv(static_dir=None):
    """Load x_piv, z_piv, u_piv grids from static/ folder."""
    if static_dir is None:
        static_dir = Path(__file__).parent.parent / "static"
    static_dir = Path(static_dir)
    x_piv = scipy.io.loadmat(static_dir / "x_piv.mat")["x_piv"].astype(float)
    z_piv = scipy.io.loadmat(static_dir / "z_piv.mat")["z_piv"].astype(float)
    u_piv = scipy.io.loadmat(static_dir / "u_piv.mat")["u_piv"].astype(float)
    return x_piv, z_piv, u_piv

# ---------------------------------------------------------------------------
# BLOCK 3 — Settings + load + flatten the PIV data
# ---------------------------------------------------------------------------

U_THRESHOLD = 0.10                       # active-point velocity cutoff  [U_i]
Z_LEVELS    = np.arange(1.0, 3.51, 0.01)  # z-slices to fit  [l]
Z_TOL       = 0.15                       # half-width of slice window  [l]

x_piv, z_piv, u_piv = load_piv()

# fold signed x into radial distance r (wake is axisymmetric)
r_all = np.abs(x_piv.ravel())   # [l]
z_all = z_piv.ravel()           # [l]
u_all = u_piv.ravel()           # [U_i]

# ---------------------------------------------------------------------------
# BLOCK 4 — Results storage
# ---------------------------------------------------------------------------

n = len(Z_LEVELS)

results = {
    "z":     Z_LEVELS,
    "Ai":    np.zeros(n),
    "Ao":    np.zeros(n),
    "sigma": np.zeros(n),
    "Ri":    np.zeros(n),
    "Ro":    np.zeros(n),
    "R2":    np.full(n, np.nan),     # NaN until fitted
    "N":     np.zeros(n, dtype=int), # active point count per slice
}

# ---------------------------------------------------------------------------
# BLOCK 5 — Fitting loop: one Gaussian fit per z-slice
# ---------------------------------------------------------------------------

for k, z0 in enumerate(Z_LEVELS):
    # enumerate gives us both the index k (0,1,2,...) and the value z0 (1.0,1.5,...)

    # --- Step 1: slice the data -----------------------------------------------
    # Boolean mask: True for every point whose z-coordinate is within Z_TOL of z0.
    # np.abs(z_all - z0) computes the distance of each point from the target height.
    mask = np.abs(z_all - z0) < Z_TOL

    # Extract only the points in this slice
    r_sl = r_all[mask]   # radial positions of slice points  [l]
    u_sl = u_all[mask]   # velocities of slice points        [U_i]

    # Sort by r so the profile reads left-to-right (not required for fitting,
    # but makes any future plotting or inspection cleaner)
    sort_idx = np.argsort(r_sl)
    r_sl = r_sl[sort_idx]
    u_sl = u_sl[sort_idx]

    # --- Step 2: apply active-point threshold ----------------------------------
    # Only keep points with u > U_THRESHOLD.
    # Low-velocity points are dominated by noise and would pull the Gaussian flat.
    active  = u_sl > U_THRESHOLD
    r_act   = r_sl[active]   # [l]
    u_act   = u_sl[active]   # [U_i]

    # Record how many active points were found in this slice
    results["N"][k] = active.sum()

    # --- Step 3: define the cost function -------------------------------------
    # The optimiser calls cost(p) repeatedly, adjusting p to make it smaller.
    # p is a list of 5 numbers: [Ai, Ao, sigma, Ri, Ro]
    def cost(p):
        Ai, Ao, sigma, Ri, Ro = p

        # Hard constraint: reject physically impossible parameter combinations.
        # sigma must be positive (a negative width is meaningless).
        # Ri must be positive (ring can't be at negative radius).
        # Ro must be larger than Ri (outer ring must be outside inner ring).
        if sigma <= 0 or Ri <= 0 or Ro <= Ri:
            return 1e9   # return a huge cost to steer the optimiser away

        # Evaluate the model at the active PIV points
        u_pred = double_gaussian_radial(r_act, Ai, Ao, sigma, Ri, Ro)

        # Sum of squared residuals: how far the model is from the measurements
        return float(np.sum((u_pred - u_act) ** 2))

    # --- Step 4: run the optimiser --------------------------------------------
    # Initial guess for [Ai, Ao, sigma, Ri, Ro].
    # We start amplitudes at 0.6 (typical near-field value),
    # sigma at 0.3 l (a reasonable ring width),
    # and radii at the known geometric positions.
    if k == 0 or np.isnan(results["R2"][k - 1]):
        p0 = [0.6, 0.6, 0.3, R_INNER_GEOM, R_OUTER_GEOM]
    else:
        p0 = [results["Ai"][k-1], results["Ao"][k-1], results["sigma"][k-1],
              results["Ri"][k-1], results["Ro"][k-1]]

    # Nelder-Mead: a derivative-free simplex search.
    # Good choice here because the cost function has hard jumps (the 1e9 wall)
    # which would break gradient-based methods.
    # maxiter / maxfev: cap on iterations and function evaluations.
    # xatol: stop when parameter changes are smaller than this tolerance.
    res = minimize(cost, p0, method="Nelder-Mead",
                   options={"maxiter": 2000, "maxfev": 2000, "xatol": 1e-6})

    # res.x holds the best [Ai, Ao, sigma, Ri, Ro] found
    pf = res.x

    # --- Step 5: store results ------------------------------------------------
    results["Ai"][k]    = pf[0]
    results["Ao"][k]    = pf[1]
    results["sigma"][k] = pf[2]
    results["Ri"][k]    = pf[3]
    results["Ro"][k]    = pf[4]

    # Evaluate R² on the active points using the fitted parameters
    u_pred_act      = double_gaussian_radial(r_act, *pf)  # *pf unpacks the 5 values
    results["R2"][k] = r_squared(u_act, u_pred_act)

# ---------------------------------------------------------------------------
# BLOCK 7 — Save results to CSV
# ---------------------------------------------------------------------------

import csv

out_path = Path(__file__).parent / "slice_results.csv"
with open(out_path, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["z", "Ai", "Ao", "sigma", "Ri", "Ro", "R2", "N"])
    for k in range(n):
        if np.isnan(results["R2"][k]):
            continue   # skip slices that were not fitted
        writer.writerow([
            round(results["z"][k], 4),
            round(results["Ai"][k], 6),
            round(results["Ao"][k], 6),
            round(results["sigma"][k], 6),
            round(results["Ri"][k], 6),
            round(results["Ro"][k], 6),
            round(results["R2"][k], 6),
            int(results["N"][k]),
        ])

print(f"Saved {(~np.isnan(results['R2'])).sum()} fitted slices to {out_path}")

