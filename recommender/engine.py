from __future__ import annotations

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


def pick_cluster(pref_vector, centroids):
    """Return the index of the centroid closest (Euclidean) to the preference."""
    pv = np.asarray(pref_vector, dtype=float)
    dists = [np.linalg.norm(pv - np.asarray(c, dtype=float)) for c in centroids]
    return int(np.argmin(dists))


def cosine_topn(pref_vector, laptops, n=5):
    """laptops: list of dicts each with a 'vector' key.

    Returns the top-n copies (with a 'similarity' key) sorted descending.
    """
    if not laptops:
        return []
    vectors = [lap["vector"] for lap in laptops]
    sims = cosine_similarity([pref_vector], vectors)[0]
    ranked = sorted(
        ({**lap, "similarity": float(s)} for lap, s in zip(laptops, sims)),
        key=lambda d: d["similarity"],
        reverse=True,
    )
    return ranked[:n]


def precision_at_k(results, k):
    top = results[:k]
    if not top:
        return 0.0
    relevant = sum(1 for r in top if r.get("relevant"))
    return relevant / len(top)


def is_relevant(laptop, pref):
    """Rule: relevant if within budget and meets every supplied minimum spec."""
    if pref.get("budget_max_idr") and laptop["price_idr"] > pref["budget_max_idr"]:
        return False
    if pref.get("budget_min_idr") and laptop["price_idr"] < pref["budget_min_idr"]:
        return False

    minimum_checks = [
        ("min_ram_gb", "ram_gb"),
        ("min_processor_tier", "processor_tier"),
        ("min_storage_gb", "storage_gb"),
        ("min_screen_inch", "screen_inch"),
        ("min_battery_hours", "battery_hours"),
    ]
    for pref_key, lap_key in minimum_checks:
        if pref.get(pref_key) and laptop[lap_key] < pref[pref_key]:
            return False

    if pref.get("storage_type") and laptop["storage_type"] != pref["storage_type"]:
        return False
    if pref.get("vga_type") and laptop["vga_type"] != pref["vga_type"]:
        return False
    if pref.get("brand_preference") and laptop["brand"] != pref["brand_preference"]:
        return False
    return True
