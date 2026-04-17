"""
Predicted velocity field from wake_model.py
Plots model prediction alongside raw PIV data for comparison.
"""

import numpy as np
import matplotlib.pyplot as plt
import scipy.io
from pathlib import Path
from wake_model import u_wake

# --- Load raw PIV data for comparison ---------------------------------------
static_dir = Path(__file__).parent.parent / "static"
x_piv = scipy.io.loadmat(static_dir / "x_piv.mat")["x_piv"].astype(float)
z_piv = scipy.io.loadmat(static_dir / "z_piv.mat")["z_piv"].astype(float)
u_piv = scipy.io.loadmat(static_dir / "u_piv.mat")["u_piv"].astype(float)

# --- Build model prediction on the same grid --------------------------------
u_model = u_wake(np.abs(x_piv), z_piv)

# --- Plot -------------------------------------------------------------------
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 6), sharey=True)

cf1 = ax1.contourf(x_piv, z_piv, u_piv, 600, cmap="viridis")
ax1.set_title("PIV data")
ax1.set_xlabel("x / l")
ax1.set_ylabel("z / l")
plt.colorbar(cf1, ax=ax1, label=r"$\bar{u}/U_i$")
cf1.set_clim(0, 1)

cf2 = ax2.contourf(x_piv, z_piv, u_model, 600, cmap="viridis")
ax2.set_title("Wake model")
ax2.set_xlabel("x / l")
plt.colorbar(cf2, ax=ax2, label=r"$\bar{u}/U_i$")
cf2.set_clim(0, 1)

ax1.set_ylim(0, 3.5)
ax2.set_ylim(0, 3.5)

fig.suptitle("PIV vs Wake Model", fontsize=14)
fig.tight_layout()
plt.show()
