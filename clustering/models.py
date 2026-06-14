from django.db import models


class ClusterModel(models.Model):
    """A versioned snapshot of one training run."""

    k_optimal = models.PositiveSmallIntegerField()
    centroids = models.JSONField()
    silhouette_score = models.FloatField()
    wcss_list = models.JSONField()
    silhouette_list = models.JSONField()
    scaler_params = models.JSONField()
    feature_order = models.JSONField()
    elbow_plot = models.ImageField(upload_to="plots/", null=True, blank=True)
    silhouette_plot = models.ImageField(upload_to="plots/", null=True, blank=True)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_active:
            ClusterModel.objects.exclude(pk=self.pk).filter(is_active=True).update(
                is_active=False
            )

    def __str__(self):
        return f"Model #{self.pk} k={self.k_optimal} sil={self.silhouette_score:.3f}"


class Cluster(models.Model):
    cluster_model = models.ForeignKey(
        ClusterModel, on_delete=models.CASCADE, related_name="clusters"
    )
    label = models.IntegerField()
    interpretation = models.CharField(max_length=40)
    centroid = models.JSONField()
    member_count = models.PositiveIntegerField()
    summary = models.JSONField(default=dict)

    class Meta:
        ordering = ["label"]

    def __str__(self):
        return f"Cluster {self.label}: {self.interpretation}"
