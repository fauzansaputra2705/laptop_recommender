import base64
import io

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def _to_b64(fig) -> str:
    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", dpi=100)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def role_distribution_png(labels, counts) -> str:
    """Donut chart distribusi role target. Returns base64 PNG string."""
    fig, ax = plt.subplots(figsize=(5, 4))
    wedges, texts, autotexts = ax.pie(
        counts,
        labels=labels,
        autopct="%1.1f%%",
        startangle=90,
        wedgeprops={"width": 0.6},
        colors=["#4F46E5", "#7C3AED", "#0EA5E9", "#10B981"],
    )
    ax.set_title("Distribusi Role Target")
    return _to_b64(fig)


def precision_trend_png(dates, avg_precisions) -> str:
    """Line chart trend precision@K per hari. Returns base64 PNG string."""
    fig, ax = plt.subplots(figsize=(7, 3))
    ax.plot(dates, avg_precisions, marker="o", color="#4F46E5", linewidth=2)
    ax.set_ylim(0, 1)
    ax.set_xlabel("Tanggal")
    ax.set_ylabel("Avg Precision@K")
    ax.set_title("Trend Precision@K (30 Hari Terakhir)")
    ax.grid(True, linestyle="--", alpha=0.4)
    fig.autofmt_xdate(rotation=45)
    return _to_b64(fig)


def cluster_usage_png(labels, counts) -> str:
    """Horizontal bar chart distribusi cluster terpilih. Returns base64 PNG string."""
    fig, ax = plt.subplots(figsize=(6, 3))
    bars = ax.barh(labels, counts, color="#4F46E5")
    ax.bar_label(bars, padding=4)
    ax.set_xlabel("Jumlah Rekomendasi")
    ax.set_title("Distribusi Cluster Terpilih")
    ax.grid(True, axis="x", linestyle="--", alpha=0.4)
    return _to_b64(fig)
