from clustering.engine import preprocess

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
