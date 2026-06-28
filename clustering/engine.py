from __future__ import annotations

import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

NUMERIC = ["processor_tier", "ram_gb", "storage_gb", "screen_inch", "battery_hours", "price_idr"]
# Clustering attributes per thesis methodology: RAM, prosesor, VGA, penyimpanan,
# layar, baterai, harga. Brand is intentionally excluded so K-Means groups by
# specification/price, not by manufacturer.
ONEHOT = ["vga_type", "storage_type"]
# A one-hot category swap flips two columns (1->0 and 0->1), which would cost
# 2.0 in squared Euclidean distance vs at most 1.0 for any [0,1]-scaled numeric
# feature. Weighting each one-hot column by 1/sqrt(2) caps a category swap at
# 1.0 so categoricals don't dominate K-Means clustering / cluster routing.
ONEHOT_WEIGHT = 1.0 / np.sqrt(2.0)


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
                row.append(ONEHOT_WEIGHT if str(r[col]) == cat else 0.0)
        matrix.append(row)
    return matrix, scaler_params, feature_order


def evaluate_k_range(matrix, k_min=2, k_max=10):
    """Run K-Means across a K range, returning WCSS (Elbow) + Silhouette per K.

    k_optimal is chosen as the K with the highest Silhouette Score.
    """
    X = np.asarray(matrix, dtype=float)
    k_max = min(k_max, len(X) - 1)
    k_values, wcss, silhouette = [], [], []
    for k in range(k_min, k_max + 1):
        km = KMeans(n_clusters=k, random_state=42, n_init=10).fit(X)
        k_values.append(k)
        wcss.append(float(km.inertia_))
        silhouette.append(float(silhouette_score(X, km.labels_)))
    k_optimal = int(k_values[int(np.argmax(silhouette))])
    return {
        "k_values": k_values,
        "wcss": wcss,
        "silhouette": silhouette,
        "k_optimal": k_optimal,
    }


def train(matrix, k):
    """Fit final K-Means with the chosen K. Returns centroids, labels, scores."""
    X = np.asarray(matrix, dtype=float)
    km = KMeans(n_clusters=k, random_state=42, n_init=10).fit(X)
    return {
        "k": k,
        "centroids": km.cluster_centers_.tolist(),
        "labels": km.labels_.tolist(),
        "silhouette_score": float(silhouette_score(X, km.labels_)),
        "wcss": float(km.inertia_),
    }


def preprocess_verbose(records, scaler_params, feature_order):
    """Same as preprocess() but returns per-row intermediate values for manual calc display.

    Returns dict with:
    - matrix: the feature matrix
    - verbose_rows: list of dicts per record with raw, clipped, scaled, onehot, final_vector
    - feature_order: the feature order used
    - scaler_params: the scaler params used
    - onehot_weight: the ONEHOT_WEIGHT value
    - numeric_cols: list of numeric column names
    - onehot_cols: list of one-hot column names with categories
    """
    mins = {col: scaler_params["numeric"][col]["min"] for col in NUMERIC}
    maxs = {col: scaler_params["numeric"][col]["max"] for col in NUMERIC}
    categories = scaler_params["categories"]

    matrix = []
    verbose_rows = []

    for r in records:
        row = []
        verbose = {"raw": {}, "clipped": {}, "scaled": {}, "onehot": {}, "final_vector": []}

        # Raw values
        for col in NUMERIC:
            verbose["raw"][col] = float(r[col])
        for col in ONEHOT:
            verbose["raw"][col] = str(r[col])

        # Numeric: raw → scaled (single record, no IQR clipping needed)
        for col in NUMERIC:
            raw_val = float(r[col])
            verbose["clipped"][col] = raw_val
            span = maxs[col] - mins[col]
            scaled = (raw_val - mins[col]) / span if span else 0.0
            scaled = min(max(scaled, 0.0), 1.0)
            verbose["scaled"][col] = round(scaled, 6)
            row.append(scaled)

        # One-hot encoding
        for col in ONEHOT:
            for cat in categories[col]:
                key = f"{col}={cat}"
                val = ONEHOT_WEIGHT if str(r[col]) == cat else 0.0
                verbose["onehot"][key] = round(val, 6)
                row.append(val)

        verbose["final_vector"] = [round(v, 6) for v in row]
        matrix.append(row)
        verbose_rows.append(verbose)

    # Build onehot column info for template
    onehot_cols = []
    for col in ONEHOT:
        for cat in categories[col]:
            onehot_cols.append({"field": col, "category": cat, "label": f"{col}={cat}"})

    return {
        "matrix": matrix,
        "verbose_rows": verbose_rows,
        "feature_order": feature_order,
        "scaler_params": scaler_params,
        "onehot_weight": round(ONEHOT_WEIGHT, 6),
        "numeric_cols": list(NUMERIC),
        "onehot_cols": onehot_cols,
    }
