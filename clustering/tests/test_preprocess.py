from clustering.engine import ONEHOT_WEIGHT, preprocess

RECORDS = [
    {"brand": "ASUS", "processor_tier": 3, "ram_gb": 8, "storage_gb": 256,
     "storage_type": "SSD", "vga_type": "integrated", "screen_inch": 14.0,
     "battery_hours": 6.0, "price_idr": 7000000},
    {"brand": "MSI", "processor_tier": 9, "ram_gb": 32, "storage_gb": 1024,
     "storage_type": "SSD", "vga_type": "dedicated", "screen_inch": 17.3,
     "battery_hours": 4.0, "price_idr": 40000000},
    {"brand": "HP", "processor_tier": 5, "ram_gb": 16, "storage_gb": 512,
     "storage_type": "SSD", "vga_type": "integrated", "screen_inch": 15.6,
     "battery_hours": 10.0, "price_idr": 12000000},
]


def test_preprocess_scales_numeric_to_unit_range():
    matrix, scaler_params, feature_order = preprocess(RECORDS)
    assert len(matrix) == 3
    assert len(matrix[0]) == len(feature_order)
    for row in matrix:
        for val in row:
            assert -1e-9 <= val <= 1.0 + 1e-9
    assert "price_idr" in scaler_params["numeric"]


def test_preprocess_is_deterministic_feature_order():
    _, _, fo1 = preprocess(RECORDS)
    _, _, fo2 = preprocess(RECORDS)
    assert fo1 == fo2


def test_preprocess_reuses_scaler_for_new_record():
    _, scaler_params, feature_order = preprocess(RECORDS)
    new = [{"brand": "ASUS", "processor_tier": 5, "ram_gb": 16, "storage_gb": 512,
            "storage_type": "SSD", "vga_type": "integrated", "screen_inch": 14.0,
            "battery_hours": 8.0, "price_idr": 15000000}]
    matrix, sp2, fo2 = preprocess(new, scaler_params=scaler_params, feature_order=feature_order)
    assert fo2 == feature_order
    assert len(matrix[0]) == len(feature_order)


def test_brand_excluded_from_features():
    # Per thesis methodology, brand is NOT a clustering attribute; otherwise the
    # brand one-hot dims dominate and K-Means groups by manufacturer.
    _, _, feature_order = preprocess(RECORDS)
    assert not any(f.startswith("brand=") for f in feature_order)


def test_onehot_columns_weighted_to_match_numeric_scale():
    # A category swap flips two one-hot columns; weighting each by 1/sqrt(2)
    # caps the squared-distance cost of a swap at 1.0, on par with a numeric
    # feature, so categoricals don't dominate distance.
    matrix, _, feature_order = preprocess(RECORDS)
    onehot_idx = [i for i, f in enumerate(feature_order) if "=" in f]
    for row in matrix:
        for i in onehot_idx:
            assert row[i] in (0.0, ONEHOT_WEIGHT)
    # squared cost of swapping one category (1->0 and 0->1) == 1.0
    assert abs(2 * ONEHOT_WEIGHT**2 - 1.0) < 1e-9

