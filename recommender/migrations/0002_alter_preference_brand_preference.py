# Data migration: convert brand_preference from CharField to ForeignKey.

import django.db.models.deletion
from django.db import migrations, models


def populate_brand_preference(apps, schema_editor):
    """Map non-empty brand_preference strings to Brand FK references."""
    Preference = apps.get_model("recommender", "Preference")
    Brand = apps.get_model("catalog", "Brand")

    brands = {b.name: b for b in Brand.objects.all()}

    for pref in Preference.objects.all():
        if pref.brand_preference and pref.brand_preference.strip():
            pref.brand_pref_new = brands.get(pref.brand_preference.strip())
            pref.save(update_fields=["brand_pref_new"])


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0002_brand_gpu_processor_remove_laptop_processor_tier_and_more"),
        ("recommender", "0001_initial"),
    ]

    operations = [
        # Step 1: Add new FK column (nullable)
        migrations.AddField(
            model_name="preference",
            name="brand_pref_new",
            field=models.ForeignKey(
                null=True, blank=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="catalog.brand",
            ),
        ),
        # Step 2: Populate from existing data
        migrations.RunPython(populate_brand_preference, migrations.RunPython.noop),
        # Step 3: Remove old column
        migrations.RemoveField(model_name="preference", name="brand_preference"),
        # Step 4: Rename to final name
        migrations.RenameField(
            model_name="preference",
            old_name="brand_pref_new",
            new_name="brand_preference",
        ),
    ]
