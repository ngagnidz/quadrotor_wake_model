# Quadrotor Wake Model

## What this is

An analytical model that predicts the downwash velocity $u(r, z)$ at any point below a hovering quadrotor. Built from PIV (Particle Image Velocimetry) measurements and fitted using a two-stage approach: radial shape first, then axial evolution.

---

## The physical picture

A quadrotor in hover pushes air downward. Below the rotor plane, this creates a wake with two concentric high-velocity rings — one from the inner blade tips, one from the outer blade tips. As you move further below the rotor (increasing $z$), those rings:

- Contract inward (smaller radius)
- Spread out (wider Gaussian width)
- Weaken (lower amplitude)

---

## The model

```math
u(r, z) = A_i(z) \cdot \mathcal{G}\left(r - R_i(z),\, \sigma(z)\right) \;+\; A_o(z) \cdot \mathcal{G}\left(r - R_o(z),\, \sigma(z)\right)
```

where $\mathcal{G}(x, \sigma) = \exp\left(-\dfrac{x^2}{2\sigma^2}\right)$ is an amplitude-normalised Gaussian.

The five $z$-dependent parameters follow simple laws:

```math
\begin{aligned}
R_i(z) &= R_{i0} + \beta_i \cdot z  &&\text{inner ring radius contracts linearly}\\
R_o(z) &= R_{o0} + \beta_o \cdot z  &&\text{outer ring radius contracts linearly}\\
\sigma(z) &= \sigma_0 + \alpha \cdot z  &&\text{ring width grows linearly (viscous spreading)}\\
A_i(z) &= A_{0,i} \cdot e^{-z/\lambda_i}  &&\text{inner amplitude decays exponentially}\\
A_o(z) &= A_{0,o} \cdot e^{-z/\lambda_o}  &&\text{outer amplitude decays exponentially}
\end{aligned}
```

### Why two Gaussians?

The drone has two propeller tip circles. Each creates a distinct velocity ring in the radial profile. A single Gaussian cannot capture two peaks — a sum of two can.

### Why linear for radii and width?

The rings contract and spread at a roughly constant rate with depth. When the fitted $R_i$, $R_o$, and $\sigma$ from each $z$-slice are plotted against $z$, they fall on straight lines ($R^2 > 0.93$). Linear is the simplest model consistent with the data.

### Why exponential for amplitudes?

Velocity in a jet-like wake decays exponentially with distance — energy dissipates at a rate proportional to how much energy remains. Plotting $\log(A)$ vs $z$ yields a straight line, confirming exponential decay ($R^2 > 0.99$ for both rings). A linear fit was also tested and scored lower.

---

## Units

All quantities are non-dimensionalised:

| Quantity | Scale | Value |
|---|---|---|
| Length | $l$ | $32.5\ \text{mm}$ (Crazyflie arm length) |
| Velocity | $U_i$ | induced velocity at hover |

So $r, z, R_i, R_o, \sigma$ are in units of $[l]$, and $u, A_i, A_o$ are in units of $[U_i]$.

---

## Fitted constants

Fitted from 251 $z$-slices ($z = 1.0$ to $3.5\ l$, step $= 0.01\ l$):

| Parameter | Value | Description |
|---|---|---|
| $R_{i0}$ | $0.7554$ | Inner ring radius at $z=0$ |
| $\beta_i$ | $-0.0939$ | Inner ring contraction rate |
| $R_{o0}$ | $1.3881$ | Outer ring radius at $z=0$ |
| $\beta_o$ | $-0.0495$ | Outer ring contraction rate |
| $\sigma_0$ | $0.1088$ | Ring width at $z=0$ |
| $\alpha$ | $0.0993$ | Width growth rate |
| $A_{0,i}$ | $1.3983$ | Inner amplitude at $z=0$ |
| $\lambda_i$ | $3.1376$ | Inner amplitude decay length |
| $A_{0,o}$ | $1.0953$ | Outer amplitude at $z=0$ |
| $\lambda_o$ | $4.4811$ | Outer amplitude decay length |

---

## Files

```
model_new/
├── radial_fit_test.py     # Fits double Gaussian at each z-slice → slice_results.csv
├── slice_results.csv      # Per-slice fitted parameters (generated, do not edit)
├── ring_radius_fit.py     # Fits linear trend on Ri(z), Ro(z)
├── sigma_z_fit.py         # Fits linear trend on sigma(z)
├── amplitude_decay_fit.py # Fits exponential trend on Ai(z), Ao(z)
├── wake_model.py          # Final model: u_wake(r, z) with the 10 fitted constants
└── predict_profile.py     # Plots PIV data vs model prediction side by side
```

---

## Pipeline

```
PIV data (static/)
      │
      ▼
radial_fit_test.py        ← fits double Gaussian slice by slice (step 0.01 l)
      │
      ▼
slice_results.csv         ← z, Ai, Ao, sigma, Ri, Ro, R², N per slice
      │
      ├──▶ ring_radius_fit.py     → linear fit on Ri(z), Ro(z)
      ├──▶ sigma_z_fit.py         → linear fit on sigma(z)
      └──▶ amplitude_decay_fit.py → exponential fit on Ai(z), Ao(z)
                                          │
                                          ▼
                                    wake_model.py
                                    10 constants + u_wake(r, z)
```

---

## How to run

**Step 1 — generate slice results:**
```bash
python3 model_new/radial_fit_test.py
```

**Step 2 — fit the trends:**
```bash
python3 model_new/ring_radius_fit.py
python3 model_new/sigma_z_fit.py
python3 model_new/amplitude_decay_fit.py
```

**Step 3 — query the model at any point** $(r, z)$:
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

**Step 4 — visualise:**
```bash
python3 model_new/predict_profile.py
```

---

## Validation

Global RMSE over the full PIV domain ($z = 1.0$–$3.5\ l$, 13 600 points):

```math
\text{RMSE} = \pm 0.0313\ U_i
```