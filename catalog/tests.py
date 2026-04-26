import csv
import io

from django.conf import settings
from django.test import Client as TestClient
from django.test import TestCase
from django.urls import reverse

from catalog.models import Product
from users.models import ContractorProfile, User


def make_user(email="cat@test.cl", password="pass123"):
    u = User.objects.create_user(username=email, email=email, password=password)
    ContractorProfile.objects.create(user=u, company_name="Empresa", rut="12345678-9", phone="999")
    return u


def make_product(user, name="Producto", cost=1000, sale=1200):
    return Product.objects.create(contractor=user, name=name, unit="un", cost_price=cost, sale_price=sale)


class ProductCRUDTest(TestCase):
    def setUp(self):
        self.tc = TestClient()
        self.user = make_user()
        self.tc.login(username="cat@test.cl", password="pass123")

    def test_product_list_ok(self):
        r = self.tc.get(reverse("product_list"))
        self.assertEqual(r.status_code, 200)

    def test_product_list_requires_login(self):
        self.tc.logout()
        r = self.tc.get(reverse("product_list"))
        self.assertEqual(r.status_code, 302)

    def test_product_create_get(self):
        r = self.tc.get(reverse("product_create"))
        self.assertEqual(r.status_code, 200)

    def test_product_create_post(self):
        self.tc.post(
            reverse("product_create"),
            {
                "name": "Cerámica",
                "unit": "un",
                "category": "ceramica",
                "cost_price": "5000",
                "sale_price": "7000",
                "sku": "",
                "description": "",
            },
        )
        self.assertEqual(Product.objects.filter(contractor=self.user).count(), 1)

    def test_product_edit(self):
        p = make_product(self.user, "Viejo")
        self.tc.post(
            reverse("product_edit", args=[p.pk]),
            {
                "name": "Nuevo",
                "unit": "un",
                "category": "materiales",
                "cost_price": "1000",
                "sale_price": "1500",
                "sku": "",
                "description": "",
            },
        )
        p.refresh_from_db()
        self.assertEqual(p.name, "Nuevo")

    def test_product_delete_soft(self):
        p = make_product(self.user)
        self.tc.post(reverse("product_delete", args=[p.pk]))
        p.refresh_from_db()
        self.assertFalse(p.is_active)


class ProductMultiTenantTest(TestCase):
    def setUp(self):
        self.tc = TestClient()
        self.user_a = make_user("pa@test.cl")
        self.user_b = make_user("pb@test.cl")
        self.product_b = make_product(self.user_b, "De B")
        self.tc.login(username="pa@test.cl", password="pass123")

    def test_list_only_shows_own(self):
        make_product(self.user_a, "De A")
        r = self.tc.get(reverse("product_list"))
        self.assertContains(r, "De A")
        self.assertNotContains(r, "De B")

    def test_api_isolation(self):
        r = self.tc.get("/api/v1/productos/")
        names = [p["name"] for p in r.json()["results"]]
        self.assertNotIn("De B", names)


class ProductMarginTest(TestCase):
    def setUp(self):
        self.user = make_user("margin@test.cl")

    def test_margin_positive(self):
        p = make_product(self.user, cost=1000, sale=1200)
        self.assertEqual(p.margin, 20.0)

    def test_margin_zero_cost(self):
        p = make_product(self.user, cost=0, sale=1000)
        self.assertEqual(p.margin, 0)

    def test_margin_negative(self):
        p = make_product(self.user, cost=1200, sale=1000)
        self.assertLess(p.margin, 0)

    def test_margin_equal(self):
        p = make_product(self.user, cost=1000, sale=1000)
        self.assertEqual(p.margin, 0.0)


class ProductPlanLimitTest(TestCase):
    def setUp(self):
        self.tc = TestClient()
        self.user = make_user("planlim@test.cl")
        self.tc.login(username="planlim@test.cl", password="pass123")
        limit = settings.PLAN_FREE_MAX_PRODUCTS
        for i in range(limit):
            make_product(self.user, name=f"P{i}")

    def test_extra_product_allowed(self):
        count_before = Product.objects.filter(contractor=self.user, is_active=True).count()
        self.tc.post(
            reverse("product_create"),
            {
                "name": "Extra",
                "unit": "un",
                "category": "otro",
                "cost_price": "0",
                "sale_price": "0",
                "sku": "",
                "description": "",
            },
        )
        # Sin límites de plan — el producto se crea
        self.assertEqual(
            Product.objects.filter(contractor=self.user, is_active=True).count(),
            count_before + 1,
        )


class ProductCSVTest(TestCase):
    def setUp(self):
        self.tc = TestClient()
        self.user = make_user("csv@test.cl")
        self.tc.login(username="csv@test.cl", password="pass123")

    def _make_csv(self, rows):
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["Nombre", "Descripción", "Categoría", "Unidad", "Precio Costo", "Precio Venta", "SKU"])
        for row in rows:
            writer.writerow(row)
        buf.seek(0)
        return io.BytesIO(buf.read().encode("utf-8-sig"))

    def test_csv_import_success(self):
        f = self._make_csv([["Pintura Látex", "", "Pintura", "Litro", "3000", "4500", ""]])
        f.name = "productos.csv"
        self.tc.post(reverse("product_import_csv"), {"csv_file": f})
        self.assertEqual(Product.objects.filter(contractor=self.user).count(), 1)

    def test_csv_import_empty_file(self):
        f = self._make_csv([])
        f.name = "vacio.csv"
        self.tc.post(reverse("product_import_csv"), {"csv_file": f})
        self.assertEqual(Product.objects.filter(contractor=self.user).count(), 0)

    def test_csv_import_invalid_row_skipped(self):
        # Fila sin nombre → se omite
        f = self._make_csv([["", "", "", "un", "0", "0", ""]])
        f.name = "inv.csv"
        self.tc.post(reverse("product_import_csv"), {"csv_file": f})
        self.assertEqual(Product.objects.filter(contractor=self.user).count(), 0)

    def test_csv_export_format(self):
        make_product(self.user, "Tornillo")
        r = self.tc.get(reverse("product_export_csv"))
        self.assertEqual(r.status_code, 200)
        self.assertIn("text/csv", r["Content-Type"])
        content = r.content.decode("utf-8-sig")
        self.assertIn("Tornillo", content)
        self.assertIn("Nombre", content)
