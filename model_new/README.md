# Quadrotor Wake Model

This is an analytical model for predicting the downwash velocity $u(r, z)$ at any point below a hovering Crazyflie quadrotor. It was built by fitting a two-stage model to PIV (Particle Image Velocimetry) measurements: first the radial shape at each depth, then how those shapes evolve with depth.

---

## What the wake looks like

When a quadrotor hovers, it pushes air downward. Just below the rotor plane, this downwash organises into two concentric high-velocity rings, one from the inner blade tips and one from the outer blade tips. As you go deeper below the rotor (larger $z$), those rings gradually contract inward, spread out radially, and lose peak velocity.

---

## The model

The velocity profile at depth $z$ is modelled as a sum of two Gaussians, one per ring:

```math
u(r, z) = A_i(z) \cdot \mathcal{G}\left(r - R_i(z), \sigma(z)\right) + A_o(z) \cdot \mathcal{G}\left(r - R_o(z), \sigma(z)\right)
```

where $\mathcal{G}(x, \sigma) = \exp\left(-\frac{x^2}{2\sigma^2}\right)$ is a unit-amplitude Gaussian.

Each of the five parameters changes with depth according to a simple law:

```math
\begin{aligned}
R_i(z) &= R_{i0} + \beta_i \, z  &&\text{inner ring radius (linear contraction)}\\
R_o(z) &= R_{o0} + \beta_o \, z  &&\text{outer ring radius (linear contraction)}\\
\sigma(z) &= \sigma_0 + \alpha \, z  &&\text{ring width (linear growth)}\\
A_i(z) &= A_{0,i} \cdot e^{-z/\lambda_i}  &&\text{inner peak velocity (exponential decay)}\\
A_o(z) &= A_{0,o} \cdot e^{-z/\lambda_o}  &&\text{outer peak velocity (exponential decay)}
\end{aligned}
```

### Why two Gaussians?

The Crazyflie has two propeller tip circles. Each one imprints a distinct velocity ring on the radial profile. A single Gaussian can only capture one peak, so the model uses a sum of two.

### Why linear for the radii and width?

When the fitted radii and widths from each $z$-slice are plotted against depth, they follow straight lines with $R^2 > 0.93$. Linear is the simplest model that fits.

### Why exponential for the amplitudes?

In jet-like wakes, velocity decays because energy dissipates at a rate proportional to the energy remaining, which produces exponential decay. Plotting $\log(A)$ against $z$ gives a straight line, with $R^2 > 0.99$ for both rings. A linear fit was tested and performed worse.

---

## Units

Everything is non-dimensionalised using two reference scales:

| Scale | Symbol | Value |
|---|---|---|
| Length | $l$ | $32.5 \text{ mm}$ (Crazyflie arm length) |
| Velocity | $U_i$ | induced velocity at hover |

So $r, z, R_i, R_o, \sigma$ are in units of $l$, and $u, A_i, A_o$ are in units of $U_i$.

---

## Fitted constants

These ten constants were fitted from 251 depth slices, covering $z = 1.0$ to $z = 3.5$ in steps of $0.01 \, l$:

| Parameter | Value | Meaning |
|---|---|---|
| $R_{i0}$ | $0.7554$ | Inner ring radius at the rotor plane |
| $\beta_i$ | $-0.0939$ | Rate at which inner ring contracts per unit depth |
| $R_{o0}$ | $1.3881$ | Outer ring radius at the rotor plane |
| $\beta_o$ | $-0.0495$ | Rate at which outer ring contracts per unit depth |
| $\sigma_0$ | $0.1088$ | Ring width at the rotor plane |
| $\alpha$ | $0.0993$ | Rate at which rings spread per unit depth |
| $A_{0,i}$ | $1.3983$ | Inner peak velocity at the rotor plane |
| $\lambda_i$ | $3.1376$ | Decay length for inner ring amplitude |
| $A_{0,o}$ | $1.0953$ | Outer peak velocity at the rotor plane |
| $\lambda_o$ | $4.4811$ | Decay length for outer ring amplitude |

---

## Files

```
model_new/
├── radial_fit_test.py     # fits a double Gaussian to each z-slice, writes slice_results.csv
├── slice_results.csv      # per-slice fitted parameters (auto-generated, do not edit)
├── ring_radius_fit.py     # fits linear trends to Ri(z) and Ro(z)
├── sigma_z_fit.py         # fits a linear trend to sigma(z)
├── amplitude_decay_fit.py # fits exponential trends to Ai(z) and Ao(z)
├── wake_model.py          # assembles the final model with all 10 constants
└── predict_profile.py     # plots PIV data against model predictions
```

---

## How it works

The fitting process runs in two stages:

**Stage 1 - radial fitting.** `radial_fit_test.py` takes each horizontal slice of the PIV data and fits a double Gaussian to the radial velocity profile. This gives six numbers per slice: $A_i, A_o, \sigma, R_i, R_o$, and the fit quality $R^2$. Results go into `slice_results.csv`.

**Stage 2 - depth evolution.** Three scripts then look at how those per-slice values change with depth. `ring_radius_fit.py` fits linear trends to $R_i(z)$ and $R_o(z)$. `sigma_z_fit.py` fits a linear trend to $\sigma(z)$. `amplitude_decay_fit.py` fits exponential trends to $A_i(z)$ and $A_o(z)$. Together these produce the 10 constants that define the final model in `wake_model.py`.

---

## How to run

**Step 1 - generate the per-slice fits:**
```bash
python3 model_new/radial_fit_test.py
```

**Step 2 - fit the depth trends:**
```bash
python3 model_new/ring_radius_fit.py
python3 model_new/sigma_z_fit.py
python3 model_new/amplitude_decay_fit.py
```

**Step 3 - query the model at any point $(r, z)$:**
```bash
python3 model_new/wake_model.py <r> <z>
```
Example:
```
python3 model_new/wake_model.py 0.7 2.0

r = 0.700 l,  z = 2.000 l
  predicted u = 0.7855 Ui
  error est.  = ±0.0171 Ui  (RMSE over 32 nearby PIV points)
```

**Step 4 - visualise predictions against PIV data:**
```bash
python3 model_new/predict_profile.py
```

---

## Validation

Evaluated against the full PIV dataset (13,600 points, $z = 1.0$ to $z = 3.5 \, l$):

```math
\text{RMSE} = \pm 0.0313 \; U_i
```