"""Pure CSV parsing + validation for bulk laptop import.

No Django ORM here — caller is responsible for DB writes.
Returns dicts with string field values; caller resolves FKs.
"""
from __future__ import annotations

import csv
import io
from decimal import Decimal, InvalidOperation

REQUIRED_COLUMNS = [
    "brand", "model", "processor", "processor_tier",
    "ram_gb", "storage_gb", "storage_type", "vga", "vga_type",
    "screen_inch", "battery_hours", "price_idr",
]

STORAGE_CHOICES = {"SSD", "HDD"}
VGA_CHOICES = {"integrated", "dedicated"}


def _to_int(val, min_val=None, max_val=None):
    try:
        v = int(str(val).strip())
    except (ValueError, TypeError):
        return None, "bukan bilangan bulat"
    if min_val is not None and v < min_val:
        return None, f"nilai minimum {min_val}"
    if max_val is not None and v > max_val:
        return None, f"nilai maksimum {max_val}"
    return v, None


def _to_decimal(val, min_val=None, max_val=None):
    try:
        v = Decimal(str(val).strip())
    except (InvalidOperation, TypeError):
        return None, "bukan angka desimal"
    if min_val is not None and v < Decimal(str(min_val)):
        return None, f"nilai minimum {min_val}"
    if max_val is not None and v > Decimal(str(max_val)):
        return None, f"nilai maksimum {max_val}"
    return v, None


def _validate_row(raw: dict) -> tuple[dict | None, list[str]]:
    """Validate one CSV row. Returns (cleaned_dict, errors_list)."""
    errors = []
    clean = {}

    # --- string fields ---
    for field in ("brand", "model", "processor", "vga"):
        val = str(raw.get(field, "")).strip()
        if not val:
            errors.append(f"{field}: tidak boleh kosong")
        else:
            clean[field] = val

    # --- processor_tier ---
    v, err = _to_int(raw.get("processor_tier"), min_val=1, max_val=10)
    if err:
        errors.append(f"processor_tier: {err}")
    else:
        clean["processor_tier"] = v

    # --- ram_gb ---
    v, err = _to_int(raw.get("ram_gb"), min_val=1)
    if err:
        errors.append(f"ram_gb: {err}")
    else:
        clean["ram_gb"] = v

    # --- storage_gb ---
    v, err = _to_int(raw.get("storage_gb"), min_val=1)
    if err:
        errors.append(f"storage_gb: {err}")
    else:
        clean["storage_gb"] = v

    # --- storage_type ---
    st = str(raw.get("storage_type", "")).strip().upper()
    if st not in STORAGE_CHOICES:
        errors.append(f"storage_type: harus SSD atau HDD (dapat: {st!r})")
    else:
        clean["storage_type"] = st

    # --- vga_type ---
    vt = str(raw.get("vga_type", "")).strip().lower()
    if vt not in VGA_CHOICES:
        errors.append(f"vga_type: harus integrated atau dedicated (dapat: {vt!r})")
    else:
        clean["vga_type"] = vt

    # --- screen_inch ---
    v, err = _to_decimal(raw.get("screen_inch"), min_val=11.0, max_val=17.3)
    if err:
        errors.append(f"screen_inch: {err}")
    else:
        clean["screen_inch"] = v

    # --- battery_hours ---
    v, err = _to_decimal(raw.get("battery_hours"), min_val=0.1)
    if err:
        errors.append(f"battery_hours: {err}")
    else:
        clean["battery_hours"] = v

    # --- price_idr ---
    v, err = _to_int(raw.get("price_idr"), min_val=1_000_000)
    if err:
        errors.append(f"price_idr: {err}")
    else:
        clean["price_idr"] = v

    return (clean if not errors else None), errors


def parse_and_validate(file_obj) -> dict:
    """
    Parse a CSV file object and validate each row.

    Returns:
        {
          "valid_rows": list[dict],
          "error_rows": [{"row_num": int, "data": dict, "errors": list[str]}],
          "missing_columns": list[str],
          "preview": list[dict],  # first 10 valid rows
        }
    """
    try:
        content = file_obj.read()
        if isinstance(content, bytes):
            content = content.decode("utf-8-sig")  # handle BOM
        reader = csv.DictReader(io.StringIO(content))
        fieldnames = reader.fieldnames or []
    except Exception as exc:
        return {
            "valid_rows": [],
            "error_rows": [{"row_num": 0, "data": {}, "errors": [f"Gagal membaca file: {exc}"]}],
            "missing_columns": REQUIRED_COLUMNS,
            "preview": [],
        }

    missing = [c for c in REQUIRED_COLUMNS if c not in fieldnames]
    if missing:
        return {
            "valid_rows": [],
            "error_rows": [],
            "missing_columns": missing,
            "preview": [],
        }

    valid_rows: list[dict] = []
    error_rows: list[dict] = []

    for row_num, raw in enumerate(reader, start=2):  # row 1 is header
        cleaned, errors = _validate_row(raw)
        if errors:
            error_rows.append({"row_num": row_num, "data": dict(raw), "errors": errors})
        else:
            valid_rows.append(cleaned)

    return {
        "valid_rows": valid_rows,
        "error_rows": error_rows,
        "missing_columns": [],
        "preview": valid_rows[:10],
    }
