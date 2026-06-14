from recommender.engine import cosine_topn, is_relevant, pick_cluster, precision_at_k


def test_pick_cluster_returns_nearest_centroid():
    centroids = [[0.0, 0.0], [1.0, 1.0]]
    assert pick_cluster([0.1, 0.1], centroids) == 0
    assert pick_cluster([0.9, 0.8], centroids) == 1


def test_cosine_topn_orders_descending():
    pref = [1.0, 0.0]
    laptops = [
        {"id": 1, "vector": [1.0, 0.0]},
        {"id": 2, "vector": [0.0, 1.0]},
        {"id": 3, "vector": [0.7, 0.7]},
    ]
    top = cosine_topn(pref, laptops, n=2)
    assert [t["id"] for t in top] == [1, 3]
    assert top[0]["similarity"] >= top[1]["similarity"]


def test_cosine_topn_empty():
    assert cosine_topn([1.0, 0.0], [], n=5) == []


def test_precision_at_k():
    results = [
        {"relevant": True}, {"relevant": True}, {"relevant": False},
        {"relevant": True}, {"relevant": False},
    ]
    assert precision_at_k(results, k=5) == 0.6
    assert precision_at_k(results, k=2) == 1.0


def test_is_relevant_within_budget_and_specs():
    laptop = {
        "price_idr": 15_000_000, "ram_gb": 16, "processor_tier": 7,
        "storage_gb": 512, "screen_inch": 14.0, "battery_hours": 8.0,
        "storage_type": "SSD", "vga_type": "dedicated", "brand": "ASUS",
    }
    pref = {
        "budget_min_idr": 8_000_000, "budget_max_idr": 25_000_000,
        "min_ram_gb": 16, "min_processor_tier": 5, "min_storage_gb": 512,
    }
    assert is_relevant(laptop, pref) is True


def test_is_relevant_fails_when_under_spec():
    laptop = {
        "price_idr": 15_000_000, "ram_gb": 8, "processor_tier": 7,
        "storage_gb": 512, "screen_inch": 14.0, "battery_hours": 8.0,
        "storage_type": "SSD", "vga_type": "dedicated", "brand": "ASUS",
    }
    pref = {"budget_max_idr": 25_000_000, "min_ram_gb": 16, "min_processor_tier": 5}
    assert is_relevant(laptop, pref) is False


def test_is_relevant_fails_over_budget():
    laptop = {"price_idr": 30_000_000, "ram_gb": 16, "processor_tier": 7,
              "storage_gb": 512, "screen_inch": 14.0, "battery_hours": 8.0,
              "storage_type": "SSD", "vga_type": "dedicated", "brand": "ASUS"}
    pref = {"budget_max_idr": 25_000_000, "min_ram_gb": 8, "min_processor_tier": 5}
    assert is_relevant(laptop, pref) is False
