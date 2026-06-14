from __future__ import annotations

import numpy as np

NUMERIC = ["processor_tier", "ram_gb", "storage_gb", "screen_inch", "battery_hours", "price_idr"]
ONEHOT = ["brand", "vga_type", "storage_type"]


def _iqr_clip(values):
    arr = np.asarray(values, dtype=float)
    q1, q3 = np.percentile(arr, [25, 75])
    iqr = q3 - q1
    lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    return np.clip(arr, lo, hi)


def preprocess(records, scaler_params=None, feature_order=None):
    """Build a numeric feature matrix from laptop-shaped dicts.

    Returns (matrix: list[list[float]], scaler_params: dict, feature_order: list[str]).

    When scaler_params / feature_order are provided they are reused (recommendation
    path) so the produced vectors live in the same feature space as training.
    """
    fit = scaler_params is None
    if fit:
        scaler_params = {"numeric": {}, "categories": {}}
        clipped = {col: _iqr_clip([r[col] for r in records]) for col in NUMERIC}
        for col in NUMERIC:
            vmin, vmax = float(clipped[col].min()), float(clipped[col].max())
            scaler_params["numeric"][col] = {"min": vmin, "max": vmax}
        for col in ONEHOT:
            scaler_params["categories"][col] = sorted({str(r[col]) for r in records})

    if feature_order is None:
        feature_order = list(NUMERIC)
        for col in ONEHOT:
            for cat in scaler_params["categories"][col]:
                feature_order.append(f"{col}={cat}")

    matrix = []
    for r in records:
        row = []
        for col in NUMERIC:
            p = scaler_params["numeric"][col]
            span = p["max"] - p["min"]
            v = (float(r[col]) - p["min"]) / span if span else 0.0
            row.append(min(max(v, 0.0), 1.0))
        for col in ONEHOT:
            for cat in scaler_params["categories"][col]:
                row.append(1.0 if str(r[col]) == cat else 0.0)
        matrix.append(row)
    return matrix, scaler_params, feature_order
