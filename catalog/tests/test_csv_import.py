import io

import pytest

from catalog.csv_import import parse_and_validate


VALID_CSV = """brand,model,processor,processor_tier,ram_gb,storage_gb,storage_type,vga,vga_type,screen_inch,battery_hours,price_idr
ASUS,VivoBook 14,Intel Core i5,5,16,512,SSD,Intel Iris Xe,integrated,14.0,8.0,12000000
Lenovo,IdeaPad Slim,AMD Ryzen 5,5,8,256,SSD,AMD Radeon,integrated,15.6,7.5,9000000
"""

BAD_TIER_CSV = """brand,model,processor,processor_tier,ram_gb,storage_gb,storage_type,vga,vga_type,screen_inch,battery_hours,price_idr
ASUS,VivoBook 14,Intel Core i5,15,16,512,SSD,Intel Iris Xe,integrated,14.0,8.0,12000000
"""

MISSING_COL_CSV = """brand,model,processor
ASUS,VivoBook 14,Intel Core i5
"""


def test_valid_csv_returns_rows():
    result = parse_and_validate(io.StringIO(VALID_CSV))
    assert result["missing_columns"] == []
    assert len(result["valid_rows"]) == 2
    assert result["error_rows"] == []
    assert len(result["preview"]) == 2


def test_valid_row_types():
    result = parse_and_validate(io.StringIO(VALID_CSV))
    row = result["valid_rows"][0]
    assert row["processor_tier"] == 5
    assert row["ram_gb"] == 16
    assert row["storage_type"] == "SSD"
    assert row["vga_type"] == "integrated"


def test_bad_processor_tier_goes_to_error_rows():
    result = parse_and_validate(io.StringIO(BAD_TIER_CSV))
    assert result["missing_columns"] == []
    assert result["valid_rows"] == []
    assert len(result["error_rows"]) == 1
    assert any("processor_tier" in e for e in result["error_rows"][0]["errors"])


def test_missing_columns():
    result = parse_and_validate(io.StringIO(MISSING_COL_CSV))
    assert len(result["missing_columns"]) > 0
    assert result["valid_rows"] == []


def test_preview_max_10():
    rows = ["brand,model,processor,processor_tier,ram_gb,storage_gb,storage_type,vga,vga_type,screen_inch,battery_hours,price_idr"]
    for i in range(15):
        rows.append(f"ASUS,Model{i},i5,5,8,256,SSD,Intel,integrated,14.0,6.0,8000000")
    result = parse_and_validate(io.StringIO("\n".join(rows) + "\n"))
    assert len(result["valid_rows"]) == 15
    assert len(result["preview"]) == 10
