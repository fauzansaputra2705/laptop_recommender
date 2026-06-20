import pytest
from django.test import RequestFactory
from django.views.generic import ListView

from catalog.models import Brand, Gpu, Laptop, Processor
from datatable.mixins import DatatableViewMixin


class LaptopDatatableView(DatatableViewMixin, ListView):
    model = Laptop
    template_name = "catalog/list.html"
    context_object_name = "laptops"
    datatable_columns = [
        {"key": "brand", "label": "Merek", "sortable": True, "searchable": True, "search_key": "brand__name", "sort_key": "brand__name"},
        {"key": "model", "label": "Model", "sortable": True, "searchable": True},
        {"key": "price_idr", "label": "Harga", "sortable": True, "searchable": False},
        {"key": "ram_gb", "label": "RAM", "sortable": True, "searchable": False},
    ]


@pytest.fixture
def laptops(db):
    """Create test laptops — 3 core + 9 extras for pagination testing."""
    asus = Brand.objects.create(name="Asus")
    lenovo = Brand.objects.create(name="Lenovo")
    i3 = Processor.objects.create(name="i3", tier=3)
    i5 = Processor.objects.create(name="i5", tier=5)
    i9 = Processor.objects.create(name="i9", tier=9)
    intel = Gpu.objects.create(name="Intel", vga_type="integrated")
    rtx = Gpu.objects.create(name="RTX 4060", vga_type="dedicated")

    Laptop.objects.create(
        brand=asus, model="VivoBook 14", processor=i5,
        ram_gb=8, storage_gb=256, storage_type="SSD", vga=intel,
        screen_inch=14.0, battery_hours=8.0, price_idr=8000000,
    )
    Laptop.objects.create(
        brand=lenovo, model="IdeaPad Slim 3", processor=i3,
        ram_gb=4, storage_gb=256, storage_type="SSD", vga=intel,
        screen_inch=14.0, battery_hours=7.0, price_idr=6000000,
    )
    Laptop.objects.create(
        brand=asus, model="ROG Zephyrus", processor=i9,
        ram_gb=32, storage_gb=1024, storage_type="SSD", vga=rtx,
        screen_inch=15.6, battery_hours=5.0, price_idr=25000000,
    )
    # Extra laptops so total=12, enabling pagination tests with per_page=10 (mixin min clamp)
    other_brand = Brand.objects.create(name="Other")
    for i in range(9):
        Laptop.objects.create(
            brand=other_brand, model=f"Model{i}", processor=i5,
            ram_gb=8, storage_gb=256, storage_type="SSD", vga=intel,
            screen_inch=14.0, battery_hours=8.0, price_idr=10000000 + i * 1000000,
        )


@pytest.mark.django_db
class TestDatatableViewMixin:
    def _get_view(self, **params):
        factory = RequestFactory()
        request = factory.get("/test/", data=params)
        view = LaptopDatatableView.as_view()
        return request, view

    def test_default_context_contains_datatable(self, laptops):
        request, view = self._get_view()
        response = view(request)
        ctx = response.context_data
        assert "datatable" in ctx
        dt = ctx["datatable"]
        assert dt["total_count"] == 12
        assert dt["search"] == ""
        assert dt["sort_key"] == ""
        assert dt["per_page"] == 20

    def test_search_filters_results(self, laptops):
        request, view = self._get_view(search="asus")
        response = view(request)
        dt = response.context_data["datatable"]
        assert dt["total_count"] == 2
        assert dt["search"] == "asus"

    def test_search_no_results(self, laptops):
        request, view = self._get_view(search="dell")
        response = view(request)
        dt = response.context_data["datatable"]
        assert dt["total_count"] == 0

    def test_sort_ascending(self, laptops):
        request, view = self._get_view(sort="price_idr", dir="asc")
        response = view(request)
        dt = response.context_data["datatable"]
        prices = [obj.price_idr for obj in dt["page_obj"].object_list]
        assert prices == sorted(prices)

    def test_sort_descending(self, laptops):
        request, view = self._get_view(sort="price_idr", dir="desc")
        response = view(request)
        dt = response.context_data["datatable"]
        prices = [obj.price_idr for obj in dt["page_obj"].object_list]
        assert prices == sorted(prices, reverse=True)

    def test_pagination(self, laptops):
        # per_page=10 is the minimum clamp; 12 laptops → page 1 has 10, has_next
        request, view = self._get_view(per_page=10, page=1)
        response = view(request)
        dt = response.context_data["datatable"]
        assert len(dt["page_obj"].object_list) == 10
        assert dt["page_obj"].has_next()

    def test_pagination_page_2(self, laptops):
        request, view = self._get_view(per_page=10, page=2)
        response = view(request)
        dt = response.context_data["datatable"]
        assert len(dt["page_obj"].object_list) == 2

    def test_per_page_clamped(self, laptops):
        request, view = self._get_view(per_page=5)
        response = view(request)
        dt = response.context_data["datatable"]
        assert dt["per_page"] == 10  # clamped to min 10

    def test_invalid_page_defaults_to_1(self, laptops):
        request, view = self._get_view(page="abc")
        response = view(request)
        dt = response.context_data["datatable"]
        assert dt["page_obj"].number == 1

    def test_search_and_sort_combined(self, laptops):
        request, view = self._get_view(search="asus", sort="price_idr", dir="desc")
        response = view(request)
        dt = response.context_data["datatable"]
        assert dt["total_count"] == 2
        prices = [obj.price_idr for obj in dt["page_obj"].object_list]
        assert prices == sorted(prices, reverse=True)
