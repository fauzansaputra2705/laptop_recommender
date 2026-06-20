from datetime import datetime

from recommender.exports import build_recommendation_excel, build_recommendation_pdf

SAMPLE_ROWS = [
    {
        "user": "alice",
        "role_target": "developer",
        "cluster": "Mid-Range",
        "precision_at_k": 0.8,
        "budget_max": 20000000,
        "tanggal": datetime(2026, 6, 20, 10, 0),
    },
    {
        "user": "bob",
        "role_target": "manajemen",
        "cluster": "Entry-Level",
        "precision_at_k": 0.6,
        "budget_max": 10000000,
        "tanggal": datetime(2026, 6, 19, 9, 0),
    },
]


def test_build_excel_with_user_col():
    result = build_recommendation_excel(SAMPLE_ROWS, include_user_col=True)
    assert isinstance(result, bytes)
    assert len(result) > 0
    assert result[:2] == b"PK"


def test_build_excel_without_user_col():
    result = build_recommendation_excel(SAMPLE_ROWS, include_user_col=False)
    assert isinstance(result, bytes)
    assert result[:2] == b"PK"


def test_build_excel_empty_rows():
    result = build_recommendation_excel([], include_user_col=True)
    assert isinstance(result, bytes)
    assert result[:2] == b"PK"


def test_build_pdf_with_user_col():
    result = build_recommendation_pdf(SAMPLE_ROWS, include_user_col=True)
    assert isinstance(result, bytes)
    assert len(result) > 0
    assert result[:4] == b"%PDF"


def test_build_pdf_without_user_col():
    result = build_recommendation_pdf(SAMPLE_ROWS, include_user_col=False)
    assert isinstance(result, bytes)
    assert result[:4] == b"%PDF"
