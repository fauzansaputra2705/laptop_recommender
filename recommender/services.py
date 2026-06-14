from catalog.models import Laptop
from clustering import engine as cengine
from clustering.models import ClusterModel
from clustering.services import FIELDS
from recommender import engine as rengine
from recommender.models import Recommendation
from recommender.profiles import target_for


class NoActiveModel(Exception):
    """Raised when no active ClusterModel exists (admin hasn't trained yet)."""


def _routing_record(pref):
    """Shape a Preference like a Laptop record for cluster routing + cosine.

    The user's minimum specs are floored at the role's target profile so a
    conservatively-low minimum doesn't route the recommendation toward a
    cheaper cluster than the role warrants. Price uses the budget midpoint
    (more representative than the max). This vector is used ONLY for routing /
    similarity — relevance + Precision@K still use the raw user minimums.
    """
    target = target_for(pref.role_target)
    screen = float(pref.min_screen_inch) if pref.min_screen_inch else 0.0
    battery = float(pref.min_battery_hours) if pref.min_battery_hours else 0.0
    user_vga = pref.vga_type or ""
    vga = "dedicated" if "dedicated" in (user_vga, target["vga_type"]) else "integrated"
    return {
        "brand": pref.brand_preference or "ASUS",
        "processor_tier": max(pref.min_processor_tier, target["processor_tier"]),
        "ram_gb": max(pref.min_ram_gb, target["ram_gb"]),
        "storage_gb": max(pref.min_storage_gb, target["storage_gb"]),
        "storage_type": pref.storage_type or "SSD",
        "vga_type": vga,
        "screen_inch": max(screen, target["screen_inch"]),
        "battery_hours": max(battery, target["battery_hours"]),
        "price_idr": (pref.budget_min_idr + pref.budget_max_idr) // 2,
    }


def _pref_dict(pref):
    return {
        "budget_min_idr": pref.budget_min_idr,
        "budget_max_idr": pref.budget_max_idr,
        "min_ram_gb": pref.min_ram_gb,
        "min_processor_tier": pref.min_processor_tier,
        "min_storage_gb": pref.min_storage_gb,
        "min_screen_inch": float(pref.min_screen_inch) if pref.min_screen_inch else None,
        "min_battery_hours": float(pref.min_battery_hours) if pref.min_battery_hours else None,
        "storage_type": pref.storage_type or None,
        "vga_type": pref.vga_type or None,
        "brand_preference": pref.brand_preference or None,
    }


def generate_recommendation(pref, top_n=5):
    """Map a Preference into the active feature space, pick its cluster, rank
    laptops by cosine similarity, score relevance, and persist a Recommendation.
    """
    model = ClusterModel.objects.filter(is_active=True).first()
    if model is None:
        raise NoActiveModel("Admin belum melakukan training cluster.")

    pref_matrix, _, _ = cengine.preprocess(
        [_routing_record(pref)],
        scaler_params=model.scaler_params,
        feature_order=model.feature_order,
    )
    pref_vector = pref_matrix[0]

    cluster_label = rengine.pick_cluster(pref_vector, model.centroids)
    selected_cluster = model.clusters.get(label=cluster_label)

    laptops = list(Laptop.objects.filter(cluster_label=cluster_label))
    lap_records = []
    for lap in laptops:
        rec = {f: getattr(lap, f) for f in FIELDS}
        rec["screen_inch"] = float(rec["screen_inch"])
        rec["battery_hours"] = float(rec["battery_hours"])
        rec["id"] = lap.id
        rec["name"] = str(lap)
        lap_records.append(rec)

    lap_matrix, _, _ = cengine.preprocess(
        [{f: r[f] for f in FIELDS} for r in lap_records],
        scaler_params=model.scaler_params,
        feature_order=model.feature_order,
    ) if lap_records else ([], None, None)
    for rec, vec in zip(lap_records, lap_matrix):
        rec["vector"] = vec

    top = rengine.cosine_topn(pref_vector, lap_records, n=top_n)
    pref_d = _pref_dict(pref)
    results = []
    for t in top:
        results.append({
            "id": t["id"],
            "name": t["name"],
            "brand": t["brand"],
            "processor_tier": t["processor_tier"],
            "ram_gb": t["ram_gb"],
            "storage_gb": t["storage_gb"],
            "storage_type": t["storage_type"],
            "vga_type": t["vga_type"],
            "screen_inch": t["screen_inch"],
            "battery_hours": t["battery_hours"],
            "price_idr": t["price_idr"],
            "similarity": round(t["similarity"], 4),
            "relevant": rengine.is_relevant(t, pref_d),
        })
    precision = rengine.precision_at_k(results, k=top_n)

    return Recommendation.objects.create(
        user=pref.user,
        preference=pref,
        cluster_model=model,
        selected_cluster=selected_cluster,
        results=results,
        precision_at_k=precision,
        k_value=top_n,
    )
