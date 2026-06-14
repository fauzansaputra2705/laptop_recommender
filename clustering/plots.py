import io

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from django.core.files.base import ContentFile  # noqa: E402


def _fig_to_contentfile(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return ContentFile(buf.read())


def elbow_png(k_values, wcss, k_optimal=None):
    fig, ax = plt.subplots(figsize=(5, 3.5))
    ax.plot(k_values, wcss, marker="o", color="#4f46e5")
    if k_optimal is not None:
        ax.axvline(k_optimal, color="#ef4444", linestyle="--", linewidth=1,
                   label=f"K optimal = {k_optimal}")
        ax.legend()
    ax.set_title("Elbow Method (WCSS vs K)")
    ax.set_xlabel("Jumlah Cluster (K)")
    ax.set_ylabel("WCSS (Inertia)")
    ax.grid(True, color="#e2e8f0")
    return _fig_to_contentfile(fig)


def silhouette_png(k_values, scores, k_optimal=None):
    fig, ax = plt.subplots(figsize=(5, 3.5))
    ax.plot(k_values, scores, marker="o", color="#0891b2")
    if k_optimal is not None:
        ax.axvline(k_optimal, color="#ef4444", linestyle="--", linewidth=1,
                   label=f"K optimal = {k_optimal}")
        ax.legend()
    ax.set_title("Silhouette Score vs K")
    ax.set_xlabel("Jumlah Cluster (K)")
    ax.set_ylabel("Silhouette Score")
    ax.grid(True, color="#e2e8f0")
    return _fig_to_contentfile(fig)
