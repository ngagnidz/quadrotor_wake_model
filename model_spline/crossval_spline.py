import numpy as np
import matplotlib.pyplot as plt
import scipy.io
from scipy.interpolate import RectBivariateSpline
from pathlib import Path

# --- Load data ---------------------------------------------------------------
static = Path(__file__).parent.parent / "static"
x_2d = scipy.io.loadmat(static / "x_piv.mat")["x_piv"].astype(float)
z_2d = scipy.io.loadmat(static / "z_piv.mat")["z_piv"].astype(float)
u_2d = scipy.io.loadmat(static / "u_piv.mat")["u_piv"].astype(float)

x1d = x_2d[:, 0]
z1d = z_2d[0, :]

r1d   = x1d[x1d >= 0]
z_val = z1d[(z1d >= 1.0) & (z1d <= 6.5)]
u_sub = u_2d[x1d >= 0, :][:, (z1d >= 1.0) & (z1d <= 6.5)]

S = 0.05
K = 3

# --- Plotting function -------------------------------------------------------
def plot_window(axes_row, spl, z_test, u_test):
    plot_idx = np.linspace(0, len(z_test) - 1, 4, dtype=int)
    for ax, idx in zip(axes_row, plot_idx):
        u_slice  = u_test[:, idx]
        u_pred_s = spl(r1d, z_test[idx]).ravel()
        rmse     = np.sqrt(np.mean((u_slice - u_pred_s) ** 2))

        ax.plot(r1d, u_slice,  "k.", ms=2, label="PIV")
        ax.plot(r1d, u_pred_s, color="tab:orange", lw=1.5, label="spline")
        ax.set_title(f"z={z_test[idx]:.2f}  RMSE={rmse:.3f}", fontsize=8)
        ax.set_xlabel("r / l", fontsize=7)
        ax.set_xlim(0, 3)
        ax.grid(True, alpha=0.3)

# --- Walk-forward windows ----------------------------------------------------
windows = [
    (1.0, 1.5, 1.5, 2.0),
    (1.5, 2.5, 2.5, 3.5),
    (2.5, 4.0, 4.0, 5.0),
    (4.0, 5.5, 5.5, 6.5),
]

print(f"{'Window':<35} {'Train slices':>12} {'Test slices':>11} {'R²':>8} {'RMSE':>8}")
print("-" * 80)

fig, axes = plt.subplots(len(windows), 4, figsize=(15, 3 * len(windows)))

for row, (z0_tr, z1_tr, z0_te, z1_te) in enumerate(windows):
    train_mask = (z_val >= z0_tr) & (z_val < z1_tr)
    test_mask  = (z_val >= z0_te) & (z_val < z1_te)

    z_train = z_val[train_mask]
    z_test  = z_val[test_mask]
    u_train = u_sub[:, train_mask]
    u_test  = u_sub[:, test_mask]

    spl    = RectBivariateSpline(r1d, z_train, u_train, kx=K, ky=K, s=S)
    u_pred = spl(r1d, z_test)

    active = u_test > 0.10
    u_true = u_test[active]
    u_p    = u_pred[active]
    rmse   = np.sqrt(np.mean((u_p - u_true) ** 2))
    r2     = 1.0 - np.sum((u_p - u_true) ** 2) / np.sum((u_true - u_true.mean()) ** 2)

    label = f"train z={z0_tr}–{z1_tr} → test z={z0_te}–{z1_te}"
    print(f"{label:<35} {len(z_train):>12} {len(z_test):>11} {r2:>8.4f} {rmse:>8.4f}")

    axes[row, 0].set_ylabel(r"$\bar{u}/U_i$", fontsize=8)
    plot_window(axes[row], spl, z_test, u_test)

axes[0, 0].legend(fontsize=7)
fig.suptitle("Walk-forward cross-validation", fontsize=12)
fig.tight_layout()
plt.show()
