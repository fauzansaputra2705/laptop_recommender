import numpy as np

from clustering.engine import evaluate_k_range, preprocess, train


def _records(n=60):
    rng = np.random.default_rng(42)
    recs = []
    for _ in range(n):
        tier = int(rng.integers(1, 11))
        recs.append({
            "brand": str(rng.choice(["ASUS", "HP", "MSI"])),
            "processor_tier": tier,
            "ram_gb": int(rng.choice([8, 16, 32])),
            "storage_gb": int(rng.choice([256, 512, 1024])),
            "storage_type": "SSD",
            "vga_type": str(rng.choice(["integrated", "dedicated"])),
            "screen_inch": float(rng.choice([14.0, 15.6, 17.3])),
            "battery_hours": float(rng.integers(4, 12)),
            "price_idr": int(tier * 3_000_000 + rng.integers(0, 2_000_000)),
        })
    return recs


def test_evaluate_k_range_returns_scores():
    matrix, _, _ = preprocess(_records())
    result = evaluate_k_range(matrix, k_min=2, k_max=6)
    assert list(result["k_values"]) == [2, 3, 4, 5, 6]
    assert len(result["wcss"]) == 5
    assert len(result["silhouette"]) == 5
    assert 2 <= result["k_optimal"] <= 6


def test_train_assigns_labels_and_centroids():
    matrix, _, _ = preprocess(_records())
    model = train(matrix, k=3)
    assert len(model["centroids"]) == 3
    assert len(model["labels"]) == len(matrix)
    assert set(model["labels"]).issubset({0, 1, 2})
    assert -1.0 <= model["silhouette_score"] <= 1.0
