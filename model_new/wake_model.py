"""
Quadrotor Wake Model
=====================
u(r, z) = Ai(z) · G(r - Ri(z), sigma(z))  +  Ao(z) · G(r - Ro(z), sigma(z))

Constants fitted from 251 slices (z = 1.0 to 3.5 l, step 0.01 l).
"""

import numpy as np

# --- Fitted constants -------------------------------------------------------

# Ring radii:  R(z) = R0 + beta * z
Ri0    =  0.7554
beta_i = -0.0939
Ro0    =  1.3881
beta_o = -0.0495

# Ring width:  sigma(z) = s0 + alpha * z
s0    = 0.1088
alpha = 0.0993

# Amplitudes:  A(z) = A0 * exp(-z / lambda)
A0_i     = 1.3983
lambda_i = 3.1376
A0_o     = 1.0953
lambda_o = 4.4811

# --- Model ------------------------------------------------------------------

def u_wake(r, z):
    r = np.asarray(r, dtype=float)
    z = np.asarray(z, dtype=float)

    Ri  = Ri0  + beta_i * z
    Ro  = Ro0  + beta_o * z
    sig = s0   + alpha  * z
    Ai  = A0_i * np.exp(-z / lambda_i)
    Ao  = A0_o * np.exp(-z / lambda_o)

    G = lambda x, mu, s: np.exp(-((x - mu) ** 2) / (2.0 * s ** 2))

    return Ai * G(r, Ri, sig) + Ao * G(r, Ro, sig)


# --- CLI: python3 wake_model.py <r> <z> -------------------------------------

if __name__ == "__main__":
    import sys
    import scipy.io
    from pathlib import Path

    if len(sys.argv) != 3:
        print("Usage: python3 wake_model.py <r> <z>")
        print("  r  radial distance from centre  [l]")
        print("  z  height below rotor           [l]  (valid range: 1.0 to 3.5)")
        sys.exit(1)

    r_in = float(sys.argv[1])
    z_in = float(sys.argv[2])

    u_pred = float(u_wake(r_in, z_in))

    # --- Error estimate from PIV data ---------------------------------------
    # Load PIV, find all measurement points within a small window around (r, z)
    # and compute RMSE between model and those points
    static_dir = Path(__file__).parent.parent / "static"
    x_piv = scipy.io.loadmat(static_dir / "x_piv.mat")["x_piv"].astype(float).ravel()
    z_piv = scipy.io.loadmat(static_dir / "z_piv.mat")["z_piv"].astype(float).ravel()
    u_piv = scipy.io.loadmat(static_dir / "u_piv.mat")["u_piv"].astype(float).ravel()
    r_piv = np.abs(x_piv)

    # window: ±0.1 l in both r and z
    tol_r, tol_z = 0.1, 0.1
    mask = (np.abs(r_piv - r_in) < tol_r) & (np.abs(z_piv - z_in) < tol_z)

    if mask.sum() == 0:
        err_str = "no PIV points in window — error estimate unavailable"
    else:
        u_local   = u_piv[mask]
        u_pred_local = u_wake(r_piv[mask], z_piv[mask])
        rmse = float(np.sqrt(np.mean((u_pred_local - u_local) ** 2)))
        err_str = f"±{rmse:.4f} Ui  (RMSE over {mask.sum()} nearby PIV points)"

    print(f"\nr = {r_in:.3f} l,  z = {z_in:.3f} l")
    print(f"  predicted u = {u_pred:.4f} Ui")
    print(f"  error est.  = {err_str}")
