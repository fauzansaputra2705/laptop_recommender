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


def explain_result(pref_raw, laptop_raw, feature_order):
    """Return match_breakdown: per-feature status (met/exceeded/below) vs user minimums."""
    numeric_exceeded = {"ram_gb", "storage_gb", "processor_tier", "battery_hours"}
    breakdown = {}

    for feat in feature_order:
        if feat not in laptop_raw:
            continue
        lap_val = laptop_raw[feat]

        # Price range check
        if feat == "price_idr":
            bmin = pref_raw.get("budget_min_idr")
            bmax = pref_raw.get("budget_max_idr")
            if bmax and lap_val > bmax:
                breakdown[feat] = {"status": "below", "actual": lap_val, "minimum": bmax}
            elif bmin and lap_val < bmin:
                breakdown[feat] = {"status": "below", "actual": lap_val, "minimum": bmin}
            else:
                breakdown[feat] = {"status": "met", "actual": lap_val, "minimum": bmin}
            continue

        # Numeric minimums
        pref_key_map = {
            "ram_gb": "min_ram_gb",
            "storage_gb": "min_storage_gb",
            "processor_tier": "min_processor_tier",
            "screen_inch": "min_screen_inch",
            "battery_hours": "min_battery_hours",
        }
        if feat in pref_key_map:
            min_val = pref_raw.get(pref_key_map[feat])
            if min_val is None:
                continue
            min_val = float(min_val)
            lap_val = float(lap_val)
            if lap_val < min_val:
                breakdown[feat] = {"status": "below", "actual": lap_val, "minimum": min_val}
            elif feat in numeric_exceeded and lap_val > min_val:
                breakdown[feat] = {"status": "exceeded", "actual": lap_val, "minimum": min_val}
            else:
                breakdown[feat] = {"status": "met", "actual": lap_val, "minimum": min_val}
            continue

        # Categorical (storage_type, vga_type)
        cat_key_map = {"storage_type": "storage_type", "vga_type": "vga_type"}
        if feat in cat_key_map:
            pref_val = pref_raw.get(cat_key_map[feat])
            if pref_val is None:
                continue
            if lap_val == pref_val:
                breakdown[feat] = {"status": "met", "actual": lap_val, "minimum": pref_val}
            else:
                breakdown[feat] = {"status": "below", "actual": lap_val, "minimum": pref_val}

    return breakdown


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
    if pref.get("sub_brand_preference") and laptop.get("sub_brand") != pref["sub_brand_preference"]:
        return False
    return True


def pick_cluster_verbose(pref_vector, centroids):
    """Same as pick_cluster() but returns per-centroid distance breakdown.

    Returns list of dicts: {index, centroid, distance, is_closest}
    """
    pv = np.asarray(pref_vector, dtype=float)
    results = []
    for i, c in enumerate(centroids):
        cv = np.asarray(c, dtype=float)
        diff = pv - cv
        sq_diff = diff ** 2
        dist = float(np.sqrt(np.sum(sq_diff)))
        results.append({
            "index": i,
            "centroid": [round(v, 6) for v in c],
            "sq_diff": [round(v, 6) for v in sq_diff],
            "distance": round(dist, 6),
        })
    closest_idx = int(np.argmin([r["distance"] for r in results]))
    results[closest_idx]["is_closest"] = True
    for r in results:
        r.setdefault("is_closest", False)
    return results


def cosine_verbose(pref_vector, laptops, n=5):
    """Same as cosine_topn() but returns per-laptop similarity breakdown.

    Returns list of dicts with: name, id, dot_product, norm_a, norm_b, similarity, feature_products
    """
    if not laptops:
        return []
    pv = np.asarray(pref_vector, dtype=float)
    norm_a = float(np.sqrt(np.sum(pv ** 2)))

    results = []
    for lap in laptops:
        lv = np.asarray(lap["vector"], dtype=float)
        norm_b = float(np.sqrt(np.sum(lv ** 2)))
        dot = float(np.dot(pv, lv))
        sim = dot / (norm_a * norm_b) if norm_a > 0 and norm_b > 0 else 0.0
        # Per-feature product breakdown
        feature_products = [round(float(a * b), 6) for a, b in zip(pv, lv)]
        results.append({
            **lap,
            "dot_product": round(dot, 6),
            "norm_a": round(norm_a, 6),
            "norm_b": round(norm_b, 6),
            "similarity": round(sim, 6),
            "feature_products": feature_products,
        })

    results.sort(key=lambda d: d["similarity"], reverse=True)
    return results[:n]
