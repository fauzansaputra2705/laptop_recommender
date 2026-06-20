# Fresh schema migration: Brand, Processor, Gpu master tables.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Brand",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=50, unique=True)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Gpu",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=80, unique=True)),
                ("vga_type", models.CharField(choices=[("integrated", "Integrated"), ("dedicated", "Dedicated")], default="integrated", max_length=10)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Processor",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120, unique=True)),
                ("tier", models.PositiveSmallIntegerField(help_text="Ordinal performance tier 1-10")),
            ],
            options={"ordering": ["-tier", "name"]},
        ),
        migrations.RemoveField(model_name="laptop", name="processor_tier"),
        migrations.RemoveField(model_name="laptop", name="vga_type"),
        migrations.AlterField(
            model_name="laptop",
            name="brand",
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="laptops", to="catalog.brand"),
        ),
        migrations.AlterField(
            model_name="laptop",
            name="processor",
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="laptops", to="catalog.processor"),
        ),
        migrations.AlterField(
            model_name="laptop",
            name="vga",
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="laptops", to="catalog.gpu"),
        ),
    ]
