import math

from django import forms
from django.views.generic import TemplateView

from accounts.mixins import AdminRequiredMixin
from catalog.models import Brand, Laptop, SubBrand
from clustering import engine as cengine
from clustering.models import ClusterModel
from clustering.services import _lap_to_record
from recommender import engine as rengine
from recommender.models import Preference
from recommender.profiles import target_for

INPUT_CSS = (
    "w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm "
    "placeholder:text-slate-400 focus:border-indigo-500 focus:ring-2 "
    "focus:ring-indigo-500 dark:border-slate-600 dark:bg-slate-800 "
    "dark:text-white dark:placeholder:text-slate-500 transition-colors"
)
SELECT_CSS = INPUT_CSS + " appearance-none"


class ManualCalcDBForm(forms.Form):
    """Pick existing Preference + Laptop from DB."""
    preference = forms.ModelChoiceField(
        queryset=Preference.objects.select_related("user").all(),
        label="Preference User",
        widget=forms.Select(attrs={"class": SELECT_CSS}),
    )
    laptop = forms.ModelChoiceField(
        queryset=Laptop.objects.select_related("brand", "processor", "vga").all(),
        label="Laptop (untuk demo preprocessing)",
        widget=forms.Select(attrs={"class": SELECT_CSS}),
    )


class ManualCalcInputForm(forms.Form):
    """Manual input fields."""
    role_target = forms.ChoiceField(
        choices=Preference.ROLE_CHOICES,
        label="Role Target",
        widget=forms.Select(attrs={"class": SELECT_CSS}),
    )
    budget_min_idr = forms.IntegerField(
        label="Budget Min (IDR)",
        widget=forms.NumberInput(attrs={"class": INPUT_CSS, "inputmode": "numeric", "placeholder": "8000000"}),
    )
    budget_max_idr = forms.IntegerField(
        label="Budget Max (IDR)",
        widget=forms.NumberInput(attrs={"class": INPUT_CSS, "inputmode": "numeric", "placeholder": "20000000"}),
    )
    min_ram_gb = forms.IntegerField(
        label="Min RAM (GB)",
        widget=forms.NumberInput(attrs={"class": INPUT_CSS, "inputmode": "numeric", "placeholder": "8"}),
    )
    min_processor_tier = forms.IntegerField(
        label="Min Processor Tier", min_value=1, max_value=10,
        widget=forms.NumberInput(attrs={"class": INPUT_CSS, "inputmode": "numeric", "min": "1", "max": "10", "placeholder": "5"}),
    )
    min_storage_gb = forms.IntegerField(
        label="Min Storage (GB)",
        widget=forms.NumberInput(attrs={"class": INPUT_CSS, "inputmode": "numeric", "placeholder": "256"}),
    )
    storage_type = forms.ChoiceField(
        choices=[("", "---")] + list(Preference.STORAGE_CHOICES),
        label="Storage Type", required=False,
        widget=forms.Select(attrs={"class": SELECT_CSS}),
    )
    vga_type = forms.ChoiceField(
        choices=[("", "---")] + list(Preference.VGA_CHOICES),
        label="VGA Type", required=False,
        widget=forms.Select(attrs={"class": SELECT_CSS}),
    )
    min_screen_inch = forms.FloatField(
        label="Min Screen (inch)", required=False,
        widget=forms.NumberInput(attrs={"class": INPUT_CSS, "step": "0.1", "placeholder": "14.0"}),
    )
    min_battery_hours = forms.FloatField(
        label="Min Battery (hours)", required=False,
        widget=forms.NumberInput(attrs={"class": INPUT_CSS, "step": "0.1", "placeholder": "8.0"}),
    )

    # Laptop specs for preprocessing demo
    lap_processor_tier = forms.IntegerField(
        label="Laptop: Processor Tier", min_value=1, max_value=10,
        widget=forms.NumberInput(attrs={"class": INPUT_CSS, "inputmode": "numeric", "min": "1", "max": "10", "placeholder": "7"}),
    )
    lap_ram_gb = forms.IntegerField(
        label="Laptop: RAM (GB)",
        widget=forms.NumberInput(attrs={"class": INPUT_CSS, "inputmode": "numeric", "placeholder": "16"}),
    )
    lap_storage_gb = forms.IntegerField(
        label="Laptop: Storage (GB)",
        widget=forms.NumberInput(attrs={"class": INPUT_CSS, "inputmode": "numeric", "placeholder": "512"}),
    )
    lap_storage_type = forms.ChoiceField(
        choices=Preference.STORAGE_CHOICES, label="Laptop: Storage Type",
        widget=forms.Select(attrs={"class": SELECT_CSS}),
    )
    lap_vga_type = forms.ChoiceField(
        choices=Preference.VGA_CHOICES, label="Laptop: VGA Type",
        widget=forms.Select(attrs={"class": SELECT_CSS}),
    )
    lap_screen_inch = forms.FloatField(
        label="Laptop: Screen (inch)",
        widget=forms.NumberInput(attrs={"class": INPUT_CSS, "step": "0.1", "placeholder": "15.6"}),
    )
    lap_battery_hours = forms.FloatField(
        label="Laptop: Battery (hours)",
        widget=forms.NumberInput(attrs={"class": INPUT_CSS, "step": "0.1", "placeholder": "10.0"}),
    )
    lap_price_idr = forms.IntegerField(
        label="Laptop: Price (IDR)",
        widget=forms.NumberInput(attrs={"class": INPUT_CSS, "inputmode": "numeric", "placeholder": "15000000"}),
    )


class ManualCalcView(AdminRequiredMixin, TemplateView):
    template_name = "clustering/manual_calc.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["db_form"] = ManualCalcDBForm()
        ctx["input_form"] = ManualCalcInputForm()
        ctx["has_result"] = False
        return ctx

    def post(self, request, *args, **kwargs):
        ctx = self.get_context_data(**kwargs)
        mode = request.POST.get("mode", "db")

        model = ClusterModel.objects.filter(is_active=True).first()
        if model is None:
            ctx["error"] = "Belum ada model clustering aktif. Lakukan training terlebih dahulu."
            return self.render_to_response(ctx)

        try:
            if mode == "db":
                ctx = self._process_db(request, ctx, model)
            else:
                ctx = self._process_manual(request, ctx, model)
        except Exception as exc:
            ctx["error"] = f"Error: {exc}"

        return self.render_to_response(ctx)

    def _process_db(self, request, ctx, model):
        form = ManualCalcDBForm(request.POST)
        if not form.is_valid():
            ctx["db_form"] = form
            return ctx

        pref = form.cleaned_data["preference"]
        laptop = form.cleaned_data["laptop"]

        # Build routing record from preference
        from recommender.services import _routing_record
        pref_record = _routing_record(pref)

        # Build laptop record
        lap_record = _lap_to_record(laptop)

        return self._calculate(ctx, model, pref_record, lap_record, pref, laptop)

    def _process_manual(self, request, ctx, model):
        form = ManualCalcInputForm(request.POST)
        if not form.is_valid():
            ctx["input_form"] = form
            return ctx
        d = form.cleaned_data

        # Floor values with role target
        target = target_for(d["role_target"])
        screen = d.get("min_screen_inch") or 0.0
        battery = d.get("min_battery_hours") or 0.0
        user_vga = d.get("vga_type") or ""
        vga = "dedicated" if "dedicated" in (user_vga, target["vga_type"]) else "integrated"

        pref_record = {
            "brand": "ASUS",
            "processor_tier": max(d["min_processor_tier"], target["processor_tier"]),
            "ram_gb": max(d["min_ram_gb"], target["ram_gb"]),
            "storage_gb": max(d["min_storage_gb"], target["storage_gb"]),
            "storage_type": d.get("storage_type") or "SSD",
            "vga_type": vga,
            "screen_inch": max(screen, target["screen_inch"]),
            "battery_hours": max(battery, target["battery_hours"]),
            "price_idr": (d["budget_min_idr"] + d["budget_max_idr"]) // 2,
        }

        lap_record = {
            "processor_tier": d["lap_processor_tier"],
            "ram_gb": d["lap_ram_gb"],
            "storage_gb": d["lap_storage_gb"],
            "storage_type": d["lap_storage_type"],
            "vga_type": d["lap_vga_type"],
            "screen_inch": d["lap_screen_inch"],
            "battery_hours": d["lap_battery_hours"],
            "price_idr": d["lap_price_idr"],
            "brand": "Manual",
        }

        # Build a pseudo pref dict for relevance/explain
        pref_raw = {
            "budget_min_idr": d["budget_min_idr"],
            "budget_max_idr": d["budget_max_idr"],
            "min_ram_gb": d["min_ram_gb"],
            "min_processor_tier": d["min_processor_tier"],
            "min_storage_gb": d["min_storage_gb"],
            "min_screen_inch": d.get("min_screen_inch"),
            "min_battery_hours": d.get("min_battery_hours"),
            "storage_type": d.get("storage_type") or None,
            "vga_type": d.get("vga_type") or None,
        }

        ctx["pref_raw"] = pref_raw
        ctx["pref_display"] = pref_record
        ctx["lap_display"] = lap_record
        ctx["role_target"] = target
        return self._calculate(ctx, model, pref_record, lap_record)

    def _calculate(self, ctx, model, pref_record, lap_record, pref_obj=None, laptop_obj=None):
        scaler_params = model.scaler_params
        feature_order = model.feature_order
        centroids = model.centroids

        # ── Step 1: Preprocessing ──
        pref_verbose = cengine.preprocess_verbose(
            [pref_record], scaler_params, feature_order
        )
        lap_verbose = cengine.preprocess_verbose(
            [lap_record], scaler_params, feature_order
        )
        pref_vector = pref_verbose["matrix"][0]

        ctx["step1"] = {
            "pref": pref_verbose["verbose_rows"][0],
            "lap": lap_verbose["verbose_rows"][0],
            "feature_order": feature_order,
            "onehot_weight": pref_verbose["onehot_weight"],
            "numeric_cols": pref_verbose["numeric_cols"],
            "onehot_cols": pref_verbose["onehot_cols"],
            "scaler_params": scaler_params,
        }

        # ── Step 2: Elbow & Silhouette ──
        ctx["step2"] = {
            "k_values": model.wcss_list and list(range(2, 2 + len(model.wcss_list))),
            "wcss": model.wcss_list or [],
            "silhouette": model.silhouette_list or [],
            "k_optimal": model.k_optimal,
            "silhouette_score": model.silhouette_score,
        }

        # ── Step 3: Centroids ──
        clusters = model.clusters.all()
        ctx["step3"] = {
            "clusters": [
                {
                    "label": c.label,
                    "interpretation": c.interpretation,
                    "centroid": c.centroid,
                    "member_count": c.member_count,
                    "summary": c.summary,
                }
                for c in clusters
            ],
        }

        # ── Step 4: Euclidean Distance ──
        euclidean = rengine.pick_cluster_verbose(pref_vector, centroids)
        ctx["step4"] = {
            "distances": euclidean,
            "selected_cluster": next(r for r in euclidean if r["is_closest"]),
            "pref_vector": [round(v, 6) for v in pref_vector],
        }

        # ── Step 5: Cosine Similarity ──
        selected_label = ctx["step4"]["selected_cluster"]["index"]
        selected_cluster_obj = model.clusters.get(label=selected_label)

        laptops = list(Laptop.objects.filter(cluster_label=selected_label).select_related(
            "brand", "sub_brand", "processor", "vga"
        ))
        lap_records = []
        for lap in laptops:
            rec = _lap_to_record(lap)
            rec["id"] = lap.id
            rec["name"] = str(lap)
            lap_records.append(rec)

        feature_keys = [
            "processor_tier", "ram_gb", "storage_gb", "storage_type",
            "vga_type", "screen_inch", "battery_hours", "price_idr",
        ]
        if lap_records:
            lap_matrix, _, _ = cengine.preprocess(
                [{f: r[f] for f in feature_keys} for r in lap_records],
                scaler_params=scaler_params,
                feature_order=feature_order,
            )
        else:
            lap_matrix = []
        for rec, vec in zip(lap_records, lap_matrix):
            rec["vector"] = vec

        top_n = 5
        cosine_results = rengine.cosine_verbose(pref_vector, lap_records, n=top_n)

        ctx["step5"] = {
            "results": cosine_results,
            "top_n": top_n,
            "pref_vector": [round(v, 6) for v in pref_vector],
            "formula": "cos(A, B) = (A · B) / (||A|| × ||B||)",
        }

        # ── Step 6: Precision@K ──
        if pref_obj:
            from recommender.services import _pref_dict
            pref_d = _pref_dict(pref_obj)
            pref_raw = {
                "budget_min_idr": pref_obj.budget_min_idr,
                "budget_max_idr": pref_obj.budget_max_idr,
                "min_ram_gb": pref_obj.min_ram_gb,
                "min_processor_tier": pref_obj.min_processor_tier,
                "min_storage_gb": pref_obj.min_storage_gb,
                "min_screen_inch": float(pref_obj.min_screen_inch) if pref_obj.min_screen_inch else None,
                "min_battery_hours": float(pref_obj.min_battery_hours) if pref_obj.min_battery_hours else None,
                "storage_type": pref_obj.storage_type or None,
                "vga_type": pref_obj.vga_type or None,
            }
        else:
            pref_d = ctx.get("pref_raw", {})
            pref_raw = ctx.get("pref_raw", {})

        precision_rows = []
        relevant_count = 0
        for rank, t in enumerate(cosine_results, 1):
            laptop_raw = {
                "price_idr": t["price_idr"],
                "ram_gb": t["ram_gb"],
                "processor_tier": t["processor_tier"],
                "storage_gb": t["storage_gb"],
                "screen_inch": t["screen_inch"],
                "battery_hours": t["battery_hours"],
                "storage_type": t["storage_type"],
                "vga_type": t["vga_type"],
            }
            is_rel = rengine.is_relevant(t, pref_d)
            if is_rel:
                relevant_count += 1
            breakdown = rengine.explain_result(pref_raw, laptop_raw, model.feature_order)
            precision_rows.append({
                "rank": rank,
                "name": t["name"],
                "similarity": t["similarity"],
                "relevant": is_rel,
                "breakdown": breakdown,
                "laptop": laptop_raw,
            })

        precision = relevant_count / top_n if top_n > 0 else 0.0

        ctx["step6"] = {
            "rows": precision_rows,
            "relevant_count": relevant_count,
            "top_n": top_n,
            "precision": round(precision, 4),
            "precision_pct": f"{precision * 100:.0f}",
        }

        ctx["has_result"] = True
        ctx["model"] = model
        ctx["pref_display"] = pref_record
        ctx["lap_display"] = lap_record
        return ctx
