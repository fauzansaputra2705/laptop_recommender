from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.template.loader import render_to_string


class DatatableViewMixin:
    """Mixin for ListView that adds server-side sort/search/pagination for HTMX datatables.

    Usage:
        class MyView(DatatableViewMixin, ListView):
            datatable_columns = [
                {"key": "name", "label": "Nama"},
                {"key": "price", "label": "Harga", "searchable": False},
            ]
    """

    datatable_columns = []
    datatable_per_page_default = 20

    def get_datatable_queryset(self):
        """Override to customize the base queryset for the datatable.
        Defaults to get_queryset()."""
        return self.get_queryset()

    def get(self, request, *args, **kwargs):
        if request.headers.get("HX-Request") == "true":
            # HTMX request: return only datatable fragment, no base template
            self.object_list = self.get_queryset()
            ctx = self.get_context_data()
            dt = ctx["datatable"]
            html = render_to_string("datatable/_content.html", dt, request=request)
            return HttpResponse(html)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        columns = self.datatable_columns
        qs = self.get_datatable_queryset()
        params = self.request.GET

        # --- search ---
        search = params.get("search", "").strip()
        if search:
            searchable = [c.get("search_key", c["key"]) for c in columns if c.get("searchable", True)]
            q = Q()
            for field in searchable:
                q |= Q(**{f"{field}__icontains": search})
            qs = qs.filter(q)

        # --- sort ---
        sort_key = params.get("sort", "")
        sort_dir = params.get("dir", "asc")
        sort_key_map = {
            c["key"]: c.get("sort_key", c["key"])
            for c in columns
            if c.get("sortable", True)
        }
        if sort_key and sort_key in sort_key_map:
            db_sort = sort_key_map[sort_key]
            order = db_sort if sort_dir == "asc" else f"-{db_sort}"
            qs = qs.order_by(order)

        # --- paginate ---
        try:
            per_page = int(params.get("per_page", self.datatable_per_page_default))
        except (ValueError, TypeError):
            per_page = self.datatable_per_page_default
        per_page = max(10, min(per_page, 100))

        paginator = Paginator(qs, per_page)
        try:
            page_num = int(params.get("page", 1))
        except (ValueError, TypeError):
            page_num = 1
        page_obj = paginator.get_page(page_num)

        ctx["datatable"] = {
            "columns": columns,
            "page_obj": page_obj,
            "search": search,
            "sort_key": sort_key,
            "sort_dir": sort_dir,
            "per_page": per_page,
            "per_page_options": [10, 20, 50, 100],
            "request_path": self.request.path,
            "total_count": paginator.count,
            "is_htmx": self.request.headers.get("HX-Request") == "true",
        }
        return ctx
