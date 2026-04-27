# Quadrotor Wake Model — 2D Spline

A bicubic spline (`RectBivariateSpline`, k=3, s=0.05) is fitted directly to PIV data over the domain r ≥ 0, z ∈ [1.0, 6.5] l.

## Cross-validation

Walk-forward validation: train on an earlier z region, test on the next region ahead. The model never sees test data during training, and the ordering is always train -> test in increasing z.

## Usage

```bash
# predict at a point and show 2D field
python3 spline_model.py <r> <z>

# run cross-validation
python3 crossval_spline.py
```
