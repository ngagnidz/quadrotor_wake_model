"""
Quadrotor Wake Model — 2D Spline
Fits a RectBivariateSpline directly to PIV data (r >= 0, z = 1.0 to 6.5 l).
"""

import numpy as np
import scipy.io
from scipy.interpolate import RectBivariateSpline
from pathlib import Path

# --- Load data ---------------------------------------------------------------
_static = Path(__file__).parent.parent / "static"
x_2d = scipy.io.loadmat(_static / "x_piv.mat")["x_piv"].astype(float)
z_2d = scipy.io.loadmat(_static / "z_piv.mat")["z_piv"].astype(float)
u_2d = scipy.io.loadmat(_static / "u_piv.mat")["u_piv"].astype(float)

# Extract unique coordinates
x1d = x_2d[:, 0]
z1d = z_2d[0, :]

# Keep r >= 0 and z in valid range
r1d   = x1d[x1d >= 0]
z_val = z1d[(z1d >= 1.0) & (z1d <= 6.5)]
u_sub = u_2d[x1d >= 0, :][:, (z1d >= 1.0) & (z1d <= 6.5)]

# --- Fit 2D spline -----------------------------------------------------------
S = 0.05   # smoothing factor
K = 3      # polynomial degree (cubic)

_spline = RectBivariateSpline(r1d, z_val, u_sub, kx=K, ky=K, s=S)

# --- Public interface --------------------------------------------------------
def u_wake(r, z):
    r = np.asarray(r, dtype=float)
    z = np.asarray(z, dtype=float)
    return _spline(r, z, grid=False)

def plot_2d_field():
    import matplotlib.pyplot as plt

    R2d, Z2d = np.meshgrid(r1d, z_val, indexing="ij")
    u_pred   = _spline(r1d, z_val)

    active = u_sub > 0.10
    rmse   = np.sqrt(np.mean((u_pred[active] - u_sub[active]) ** 2))
    r2     = 1.0 - np.sum((u_pred[active] - u_sub[active]) ** 2) / np.sum((u_sub[active] - u_sub[active].mean()) ** 2)
    print(f"R² = {r2:.4f}  |  RMSE = {rmse:.4f} Ui")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 6), sharey=True)

    cf1 = ax1.contourf(R2d, Z2d, u_sub,  300, cmap="viridis")
    ax1.set_title("PIV data")
    ax1.set_xlabel("r / l")
    ax1.set_ylabel("z / l")
    plt.colorbar(cf1, ax=ax1, label=r"$\bar{u}/U_i$")
    cf1.set_clim(0, 1)

    cf2 = ax2.contourf(R2d, Z2d, u_pred, 300, cmap="viridis")
    ax2.set_title(f"Spline  (R²={r2:.4f}, RMSE={rmse:.4f})")
    ax2.set_xlabel("r / l")
    plt.colorbar(cf2, ax=ax2, label=r"$\bar{u}/U_i$")
    cf2.set_clim(0, 1)

    fig.tight_layout()
    plt.show()


def predict(r_in, z_in):
    u_pred = float(u_wake(r_in, z_in))

    z_idx   = np.argmin(np.abs(z_val - z_in))
    r_idx   = np.argmin(np.abs(r1d   - r_in))
    u_actual = float(u_sub[r_idx, z_idx])
    error   = abs(u_pred - u_actual)

    print(f"r = {r_in:.3f} l,  z = {z_in:.3f} l")
    print(f"  predicted u = {u_pred:.4f} Ui")
    print(f"  PIV u       = {u_actual:.4f} Ui")
    print(f"  error       = {error:.4f} Ui")

    return u_pred, error


if __name__ == "__main__":
    import sys
    if len(sys.argv) == 3:
        predict(float(sys.argv[1]), float(sys.argv[2]))
    plot_2d_field()