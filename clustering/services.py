from django.db import transaction

from catalog.models import Laptop
from clustering import engine
from clustering.models import Cluster, ClusterModel
from clustering.plots import elbow_png, silhouette_png

MIN_LAPTOPS = 10

# Fields pulled from each Laptop for the feature matrix (must match engine inputs).
FIELDS = [
    "brand",
    "processor_tier",
    "ram_gb",
    "storage_gb",
    "storage_type",
    "vga_type",
    "screen_inch",
    "battery_hours",
    "price_idr",
]

TIER_NAMES = ["Entry-Level", "Mid-Range", "High-End", "Premium", "Workstation", "Ultra"]


@transaction.atomic
def run_training():
    """Train K-Means over all laptops, persist a new active ClusterModel + Clusters.

    Raises ValueError when there are too few laptops to cluster meaningfully.
    """
    laptops = list(Laptop.objects.all())
    if len(laptops) < MIN_LAPTOPS:
        raise ValueError(
            f"Butuh minimal {MIN_LAPTOPS} laptop untuk training (ada {len(laptops)})."
        )

    records = []
    for lap in laptops:
        rec = {f: getattr(lap, f) for f in FIELDS}
        # decimals -> float so numpy/json behave
        rec["screen_inch"] = float(rec["screen_inch"])
        rec["battery_hours"] = float(rec["battery_hours"])
        rec["_id"] = lap.id
        records.append(rec)

    feature_records = [{f: r[f] for f in FIELDS} for r in records]
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
    model.elbow_plot.save(
        f"elbow_{model.pk}.png",
        elbow_png(ev["k_values"], ev["wcss"], ev["k_optimal"]),
        save=False,
    )
    model.silhouette_plot.save(
        f"sil_{model.pk}.png",
        silhouette_png(ev["k_values"], ev["silhouette"], ev["k_optimal"]),
        save=False,
    )
    model.save()

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
    label_to_name = {
        lab: TIER_NAMES[min(i, len(TIER_NAMES) - 1)]
        for i, (lab, _) in enumerate(ranked)
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
