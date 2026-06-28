from django.db import transaction

from catalog.models import Laptop
from clustering import engine
from clustering.models import Cluster, ClusterModel

MIN_LAPTOPS = 10

# Direct numeric / choice fields on the Laptop model.
DIRECT_FIELDS = [
    "ram_gb",
    "storage_gb",
    "storage_type",
    "screen_inch",
    "battery_hours",
    "price_idr",
]


def _lap_to_record(lap):
    """Flatten a Laptop instance into the dict format the engine expects."""
    rec = {f: getattr(lap, f) for f in DIRECT_FIELDS}
    rec["brand"] = str(lap.brand)
    rec["sub_brand"] = str(lap.sub_brand) if lap.sub_brand else None
    rec["processor_tier"] = lap.processor.tier
    rec["vga_type"] = lap.vga.vga_type
    rec["screen_inch"] = float(rec["screen_inch"])
    rec["battery_hours"] = float(rec["battery_hours"])
    return rec

TIER_NAMES = ["Entry-Level", "Mid-Range", "High-End", "Premium", "Workstation", "Ultra"]


def _interpret(rank, total):
    """Map a price-ascending rank (0..total-1) onto a tier name.

    When clusters fit within the name list (the usual case) names are assigned
    contiguously from the cheapest end (Entry-Level, Mid-Range, High-End, ...)
    so labels read intuitively. If there are more clusters than names, the list
    is stretched proportionally. Works for any k."""
    if total <= 1:
        return TIER_NAMES[0]
    if total <= len(TIER_NAMES):
        return TIER_NAMES[rank]
    idx = int(rank / (total - 1) * (len(TIER_NAMES) - 1) + 1e-9)
    return TIER_NAMES[min(idx, len(TIER_NAMES) - 1)]


@transaction.atomic
def run_training():
    """Train K-Means over all laptops, persist a new active ClusterModel + Clusters.

    Raises ValueError when there are too few laptops to cluster meaningfully.
    """
    laptops = list(Laptop.objects.select_related("brand", "processor", "vga").all())
    if len(laptops) < MIN_LAPTOPS:
        raise ValueError(
            f"Butuh minimal {MIN_LAPTOPS} laptop untuk training (ada {len(laptops)})."
        )

    records = []
    for lap in laptops:
        rec = _lap_to_record(lap)
        rec["_id"] = lap.id
        records.append(rec)

    feature_keys = DIRECT_FIELDS + ["brand", "processor_tier", "vga_type"]
    feature_records = [{f: r[f] for f in feature_keys} for r in records]
    matrix, scaler_params, feature_order = engine.preprocess(feature_records)
    ev = engine.evaluate_k_range(matrix, 2, 10)
    trained = engine.train(matrix, ev["k_optimal"])

    model = ClusterModel.objects.create(
        k_optimal=ev["k_optimal"],
        centroids=trained["centroids"],
        silhouette_score=trained["silhouette_score"],
        wcss_list=ev["wcss"],
        silhouette_list=ev["silhouette"],
        scaler_params=scaler_params,
        feature_order=feature_order,
        is_active=True,
    )

    # assign cluster labels back to laptops and build Cluster rows
    labels = trained["labels"]
    by_label = {}
    for rec, lab in zip(records, labels):
        Laptop.objects.filter(pk=rec["_id"]).update(cluster_label=lab)
        by_label.setdefault(lab, []).append(rec)

    ranked = sorted(
        by_label.items(),
        key=lambda kv: sum(r["price_idr"] for r in kv[1]) / len(kv[1]),
    )
    total = len(ranked)
    label_to_name = {
        lab: _interpret(i, total) for i, (lab, _) in enumerate(ranked)
    }

    for lab, recs in by_label.items():
        n = len(recs)
        Cluster.objects.create(
            cluster_model=model,
            label=lab,
            interpretation=label_to_name[lab],
            centroid=trained["centroids"][lab],
            member_count=n,
            summary={
                "avg_price": round(sum(r["price_idr"] for r in recs) / n),
                "avg_ram": round(sum(r["ram_gb"] for r in recs) / n, 1),
                "avg_tier": round(sum(r["processor_tier"] for r in recs) / n, 1),
            },
        )

    return model
