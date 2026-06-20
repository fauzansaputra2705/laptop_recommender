import base64
import io

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def elbow_png(k_values, wcss) -> object:
    """Return ContentFile of elbow plot."""
    from django.core.files.base import ContentFile

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(k_values, wcss, marker="o", color="#4F46E5")
    ax.set_xlabel("Jumlah Cluster (K)")
    ax.set_ylabel("WCSS")
    ax.set_title("Elbow Method")
    ax.grid(True, linestyle="--", alpha=0.5)
    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", dpi=100)
    plt.close(fig)
    buf.seek(0)
    return ContentFile(buf.read())


def silhouette_png(k_values, scores) -> object:
    """Return ContentFile of silhouette score plot."""
    from django.core.files.base import ContentFile

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(k_values, scores, marker="s", color="#10B981")
    ax.set_xlabel("Jumlah Cluster (K)")
    ax.set_ylabel("Silhouette Score")
    ax.set_title("Silhouette Score per K")
    ax.grid(True, linestyle="--", alpha=0.5)
    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", dpi=100)
    plt.close(fig)
    buf.seek(0)
    return ContentFile(buf.read())


def comparison_bar_png(labels: list, silhouette_scores: list, active_idx: int | None = None) -> str:
    """Return base64 PNG string for inline display. Active model bar highlighted."""
    fig, ax = plt.subplots(figsize=(max(6, len(labels) * 1.2), 4))
    colors = [
        "#4F46E5" if i == active_idx else "#94A3B8"
        for i in range(len(labels))
    ]
    bars = ax.bar(labels, silhouette_scores, color=colors, edgecolor="white", linewidth=0.8)
    ax.set_xlabel("Model")
    ax.set_ylabel("Silhouette Score")
    ax.set_title("Perbandingan Silhouette Score Antar Model")
    ax.set_ylim(0, min(max(silhouette_scores) * 1.2, 1.0) if silhouette_scores else 1.0)
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    for bar, score in zip(bars, silhouette_scores):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.01,
            f"{score:.3f}",
            ha="center", va="bottom", fontsize=9,
        )
    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", dpi=100)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()


def cluster_distribution_png(labels: list, counts: list, interpretations: list) -> str:
    """Horizontal bar chart of laptop count per cluster. Returns base64 PNG string."""
    COLOR_MAP = {
        "entry": "#94A3B8",
        "mid": "#4F46E5",
        "high": "#10B981",
        "premium": "#F59E0B",
        "workstation": "#8B5CF6",
        "ultra": "#EF4444",
    }

    def _color(interpretation):
        key = interpretation.lower().split("-")[0].split()[0]
        return COLOR_MAP.get(key, "#64748B")

    bar_labels = [f"Cluster {l} — {i}" for l, i in zip(labels, interpretations)]
    colors = [_color(i) for i in interpretations]

    fig, ax = plt.subplots(figsize=(8, max(2.5, len(labels) * 0.8)))
    bars = ax.barh(bar_labels, counts, color=colors, edgecolor="white", linewidth=0.8)
    ax.set_xlabel("Jumlah Laptop")
    ax.set_title("Distribusi Laptop per Cluster")
    ax.grid(axis="x", linestyle="--", alpha=0.4)
    for bar, count in zip(bars, counts):
        ax.text(
            bar.get_width() + 0.3,
            bar.get_y() + bar.get_height() / 2,
            str(count),
            va="center", fontsize=9,
        )
    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", dpi=100)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()
