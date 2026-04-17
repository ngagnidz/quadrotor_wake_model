# Quadrotor Wake Model

## What this is

An analytical model that predicts the downwash velocity `u(r, z)` at any point below a hovering quadrotor. Built from PIV (Particle Image Velocimetry) measurements and fitted using a two-stage approach: radial shape first, then axial evolution.

---

## The physical picture

A quadrotor in hover pushes air downward. Below the rotor plane, this creates a wake with two concentric high-velocity rings — one from the inner blade tips, one from the outer blade tips. As you move further below the rotor (increasing z), those rings:

- Contract inward (smaller radius)
- Spread out (wider Gaussian width)
- Weaken (lower amplitude)

---

## The model

```
u(r, z) = Ai(z) · G(r - Ri(z), σ(z))  +  Ao(z) · G(r - Ro(z), σ(z))
```

where `G(x, σ) = exp(-x² / 2σ²)` is an amplitude-normalised Gaussian.

The five z-dependent parameters follow simple laws:


 Ri(z) = Ri0 + beta_i · z   - inner ring radius contracts linearly 
 Ro(z) = Ro0 + beta_o · z   - outer ring radius contracts linearly 
 σ(z)  = s0 + alpha · z     - ring width grows linearly (viscous spreading) 
 Ai(z) = A0_i · exp(-z/λ_i) - inner amplitude decays exponentially 
 Ao(z) = A0_o · exp(-z/λ_o) - outer amplitude decays exponentially 

### Why two Gaussians?

The drone has two propeller tip circles. Each creates a distinct velocity ring in the radial profile. A single Gaussian cannot capture two peaks — a sum of two can.

### Why linear for radii and width?

The rings contract and spread at a roughly constant rate with depth. When I plotted the fitted radii and widths from each z-slice, they fell on straight lines (R² > 0.93). Linear is the simplest model consistent with the data.

### Why exponential for amplitudes?

Velocity in a jet-like wake decays exponentially with distance — energy dissipates at a rate proportional to how much energy is left. When we plotted log(amplitude) vs z, it was a straight line, confirming exponential decay. R² > 0.99 for both rings. Linear fit was also tested and scored lower.

---

## Units

All quantities are non-dimensionalised:
- Length scale: `l = 32.5 mm` (Crazyflie arm length)
- Velocity scale: `U_i` (induced velocity at hover)
- `r, z, Ri, Ro, σ` are in `[l]`
- `u, Ai, Ao` are in `[U_i]`

---

## Fitted constants

```python
# Ring radii
Ri0    =  0.7554,  beta_i = -0.0939
Ro0    =  1.3881,  beta_o = -0.0495

# Ring width
s0     =  0.1088,  alpha  =  0.0993

# Amplitudes
A0_i   =  1.3983,  lambda_i = 3.1376
A0_o   =  1.0953,  lambda_o = 4.4811
```

Fitted from 251 z-slices (z = 1.0 to 3.5 l, step = 0.01 l).

---

## Files

```
model_new/
├── radial_fit_test.py     # Fits double Gaussian at each z-slice → slice_results.csv
├── slice_results.csv      # Per-slice fitted parameters (generated, do not edit)
├── ring_radius_fit.py     # Fits linear trend on Ri, Ro vs z
├── sigma_z_fit.py         # Fits linear trend on sigma vs z
├── amplitude_decay_fit.py # Fits exponential trend on Ai, Ao vs z
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
```
python3 model_new/radial_fit_test.py
```

**Step 2 — fit the trends:**
```
python3 model_new/ring_radius_fit.py
python3 model_new/sigma_z_fit.py
python3 model_new/amplitude_decay_fit.py
```

**Step 3 — query the model at any point:**
```
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
```
python3 model_new/predict_profile.py
```

---