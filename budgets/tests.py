from unittest.mock import patch

from django.conf import settings
from django.test import Client as TestClient
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from catalog.models import Product
from clients.models import Client
from users.models import ContractorProfile, User

from .models import Budget, BudgetItemLabor, BudgetItemMaterial, BudgetPublicToken, MaterialRecipe, MaterialRecipeItem


def make_user(email="test@test.cl", password="pass123"):  # pragma: allowlist secret
    u = User.objects.create_user(username=email, email=email, password=password)  # pragma: allowlist secret
    ContractorProfile.objects.create(user=u, company_name="Test SA", rut="12345678-9", phone="999")
    return u


def make_budget(user, client, title="Obra Test", tax_percent=0):
    return Budget.objects.create(
        contractor=user,
        client=client,
        title=title,
        validity_days=15,
        tax_percent=tax_percent,
    )


class BudgetModelTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.client_obj = Client.objects.create(contractor=self.user, name="Cliente Test", phone="999")
        self.budget = make_budget(self.user, self.client_obj)

    def test_budget_number_autoincrement(self):
        self.assertEqual(self.budget.number, 1)
        b2 = make_budget(self.user, self.client_obj, "Obra 2")
        self.assertEqual(b2.number, 2)

    def test_budget_totals(self):
        BudgetItemMaterial.objects.create(budget=self.budget, name="Mat A", unit="un", quantity=2, unit_price=1000)
        BudgetItemLabor.objects.create(budget=self.budget, name="MdO A", unit="gl", quantity=1, unit_price=5000)
        self.assertEqual(self.budget.subtotal_materials, 2000)
        self.assertEqual(self.budget.subtotal_labor, 5000)
        self.assertEqual(self.budget.total, 7000)

    def test_budget_total_with_iva(self):
        self.budget.tax_percent = 19
        self.budget.save()
        BudgetItemMaterial.objects.create(budget=self.budget, name="Mat", unit="un", quantity=1, unit_price=100000)
        self.assertEqual(self.budget.tax_amount, 19000)
        self.assertEqual(self.budget.total, 119000)

    def test_budget_valid_until(self):
        delta = self.budget.valid_until - self.budget.created_at
        self.assertAlmostEqual(delta.days, 15, delta=1)

    def test_str_representation(self):
        self.assertIn("Obra Test", str(self.budget))


class BudgetViewTest(TestCase):
    def setUp(self):
        self.tc = TestClient()
        self.user = make_user("vtest@test.cl")
        self.client_obj = Client.objects.create(contractor=self.user, name="Cliente", phone="999")
        self.tc.login(username="vtest@test.cl", password="pass123")  # pragma: allowlist secret

    def test_budget_list_requires_login(self):
        self.tc.logout()
        r = self.tc.get(reverse("budget_list"))
        self.assertEqual(r.status_code, 302)

    def test_budget_list_ok(self):
        r = self.tc.get(reverse("budget_list"))
        self.assertEqual(r.status_code, 200)

    def test_budget_create_get(self):
        r = self.tc.get(reverse("budget_create"))
        self.assertEqual(r.status_code, 200)

    def test_budget_create_post(self):
        self.tc.post(
            reverse("budget_create"),
            {
                "client": self.client_obj.pk,
                "title": "Nueva Obra",
                "validity_days": 15,
                "tax_percent": 0,
                "payment_terms": "50/50",
                "notes": "",
            },
        )
        self.assertEqual(Budget.objects.filter(contractor=self.user).count(), 1)

    def test_cannot_view_other_users_budget(self):
        other = make_user("other@test.cl")
        other_client = Client.objects.create(contractor=other, name="C", phone="1")
        b = make_budget(other, other_client)
        r = self.tc.get(reverse("budget_detail", args=[b.pk]))
        self.assertEqual(r.status_code, 404)


class BudgetEditTest(TestCase):
    def setUp(self):
        self.tc = TestClient()
        self.user = make_user("edit@test.cl")
        self.client_obj = Client.objects.create(contractor=self.user, name="C", phone="1")
        self.budget = make_budget(self.user, self.client_obj)
        BudgetItemMaterial.objects.create(budget=self.budget, name="Viejo", unit="un", quantity=1, unit_price=100)
        self.tc.login(username="edit@test.cl", password="pass123")  # pragma: allowlist secret

    def test_budget_edit_replaces_items(self):
        self.tc.post(
            reverse("budget_edit", args=[self.budget.pk]),
            {
                "client": self.client_obj.pk,
                "title": "Editado",
                "validity_days": 15,
                "tax_percent": 0,
                "payment_terms": "",
                "notes": "",
                "mat_name[]": ["Nuevo Item"],
                "mat_unit[]": ["un"],
                "mat_qty[]": ["2"],
                "mat_price[]": ["500"],
            },
        )
        self.assertEqual(self.budget.material_items.count(), 1)
        self.assertEqual(self.budget.material_items.first().name, "Nuevo Item")


class BudgetDeleteTest(TestCase):
    def setUp(self):
        self.tc = TestClient()
        self.user = make_user("del@test.cl")
        self.client_obj = Client.objects.create(contractor=self.user, name="C", phone="1")
        self.budget = make_budget(self.user, self.client_obj)
        BudgetItemMaterial.objects.create(budget=self.budget, name="Mat", unit="un", quantity=1, unit_price=100)
        BudgetPublicToken.objects.create(budget=self.budget)
        self.tc.login(username="del@test.cl", password="pass123")  # pragma: allowlist secret

    def test_budget_delete_cascades(self):
        pk = self.budget.pk
        self.tc.post(reverse("budget_delete", args=[pk]))
        self.assertFalse(Budget.objects.filter(pk=pk).exists())
        self.assertFalse(BudgetItemMaterial.objects.filter(budget_id=pk).exists())
        self.assertFalse(BudgetPublicToken.objects.filter(budget_id=pk).exists())


class BudgetDuplicateTest(TestCase):
    def setUp(self):
        self.tc = TestClient()
        self.user = make_user("dup@test.cl")
        self.client_obj = Client.objects.create(contractor=self.user, name="C", phone="1")
        self.original = make_budget(self.user, self.client_obj, "Original")
        BudgetItemMaterial.objects.create(budget=self.original, name="Mat", unit="un", quantity=1, unit_price=100)
        BudgetItemLabor.objects.create(budget=self.original, name="Mano", unit="gl", quantity=1, unit_price=200)
        self.tc.login(username="dup@test.cl", password="pass123")  # pragma: allowlist secret

    def test_budget_duplicate_copies_items(self):
        self.tc.post(reverse("budget_duplicate", args=[self.original.pk]))
        new = Budget.objects.exclude(pk=self.original.pk).get(contractor=self.user)
        self.assertEqual(new.status, "borrador")
        self.assertEqual(new.material_items.count(), 1)
        self.assertEqual(new.labor_items.count(), 1)

    def test_budget_duplicate_no_plan_limit(self):
        limit = settings.PLAN_FREE_MAX_BUDGETS_PER_MONTH
        # fill well past the old limit
        for _ in range(limit - 1):
            make_budget(self.user, self.client_obj)
        count_before = Budget.objects.filter(contractor=self.user).count()
        self.tc.post(reverse("budget_duplicate", args=[self.original.pk]))
        # Sin límites de plan — la duplicación siempre crea
        self.assertEqual(Budget.objects.filter(contractor=self.user).count(), count_before + 1)


class BudgetStatusTest(TestCase):
    def setUp(self):
        self.tc = TestClient()
        self.user = make_user("status@test.cl")
        self.client_obj = Client.objects.create(contractor=self.user, name="C", phone="1")
        self.budget = make_budget(self.user, self.client_obj)
        self.tc.login(username="status@test.cl", password="pass123")  # pragma: allowlist secret

    def test_budget_status_transitions(self):
        self.tc.post(reverse("budget_update_status", args=[self.budget.pk]), {"status": "enviado"})
        self.budget.refresh_from_db()
        self.assertEqual(self.budget.status, "enviado")
        self.assertIsNotNone(self.budget.sent_at)

    def test_sent_at_set_when_enviado(self):
        self.assertIsNone(self.budget.sent_at)
        self.tc.post(reverse("budget_update_status", args=[self.budget.pk]), {"status": "enviado"})
        self.budget.refresh_from_db()
        self.assertIsNotNone(self.budget.sent_at)


class BudgetPDFTest(TestCase):
    def setUp(self):
        self.tc = TestClient()
        self.user = make_user("pdf@test.cl")
        self.client_obj = Client.objects.create(contractor=self.user, name="C", phone="1")
        self.budget = make_budget(self.user, self.client_obj)
        self.tc.login(username="pdf@test.cl", password="pass123")  # pragma: allowlist secret

    def test_budget_pdf_returns_pdf(self):
        mock_pdf = b"%PDF-fake"
        with patch("weasyprint.HTML") as mock_html:
            mock_html.return_value.write_pdf.return_value = mock_pdf
            r = self.tc.get(reverse("budget_pdf", args=[self.budget.pk]))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r["Content-Type"], "application/pdf")


class BudgetEmailTest(TestCase):
    def setUp(self):
        self.tc = TestClient()
        self.user = make_user("email@test.cl")
        self.client_obj = Client.objects.create(contractor=self.user, name="C", phone="1", email="cliente@test.cl")
        self.budget = make_budget(self.user, self.client_obj)
        self.tc.login(username="email@test.cl", password="pass123")  # pragma: allowlist secret

    def test_budget_send_email_success(self):
        with patch("budgets.email_utils.EmailMultiAlternatives.send", return_value=1):
            self.tc.post(reverse("budget_send_email", args=[self.budget.pk]))
        # Budget status cambió a enviado
        self.budget.refresh_from_db()
        self.assertEqual(self.budget.status, "enviado")

    def test_budget_send_email_no_client_email(self):
        self.client_obj.email = ""
        self.client_obj.save()
        r = self.tc.post(reverse("budget_send_email", args=[self.budget.pk]))
        # Debe redirigir sin crash
        self.assertEqual(r.status_code, 302)


class BudgetPublicViewTest(TestCase):
    def setUp(self):
        self.tc = TestClient()
        self.user = make_user("pub@test.cl")
        self.client_obj = Client.objects.create(contractor=self.user, name="C", phone="1")
        self.budget = make_budget(self.user, self.client_obj)
        self.token_obj = BudgetPublicToken.objects.create(budget=self.budget)

    def test_budget_public_view_ok(self):
        r = self.tc.get(reverse("budget_public", args=[self.token_obj.token]))
        self.assertEqual(r.status_code, 200)

    def test_budget_public_view_expired(self):
        from datetime import timedelta

        self.token_obj.expires_at = timezone.now() - timedelta(days=1)
        self.token_obj.save()
        r = self.tc.get(reverse("budget_public", args=[self.token_obj.token]))
        self.assertEqual(r.status_code, 404)

    def test_budget_public_view_revoked(self):
        self.token_obj.is_revoked = True
        self.token_obj.save()
        r = self.tc.get(reverse("budget_public", args=[self.token_obj.token]))
        self.assertEqual(r.status_code, 404)

    def test_budget_generate_link_regenerates_token(self):
        self.tc.login(username="pub@test.cl", password="pass123")  # pragma: allowlist secret
        original_token = self.token_obj.token
        self.tc.post(reverse("budget_generate_link", args=[self.budget.pk]), {"regenerate": "1"})
        self.token_obj.refresh_from_db()
        self.assertNotEqual(self.token_obj.token, original_token)


class BudgetAPITest(TestCase):
    def setUp(self):
        self.tc = TestClient()
        self.user = make_user("api@test.cl")
        self.other = make_user("other@test.cl")
        self.client_obj = Client.objects.create(contractor=self.user, name="C", phone="1")
        self.other_client = Client.objects.create(contractor=self.other, name="D", phone="1")
        make_budget(self.user, self.client_obj, "Propio")
        make_budget(self.other, self.other_client, "Ajeno")
        self.tc.login(username="api@test.cl", password="pass123")  # pragma: allowlist secret

    def test_api_list_only_returns_own_budgets(self):
        r = self.tc.get("/api/v1/presupuestos/")
        titles = [b["title"] for b in r.json()["results"]]
        self.assertIn("Propio", titles)
        self.assertNotIn("Ajeno", titles)


class ClientModelTest(TestCase):
    def setUp(self):
        self.user = make_user("t2@test.cl")

    def test_budget_count(self):
        c = Client.objects.create(contractor=self.user, name="C", phone="1")
        self.assertEqual(c.budget_count(), 0)

    def test_client_str(self):
        c = Client.objects.create(contractor=self.user, name="Pepe", phone="1")
        self.assertEqual(str(c), "Pepe")


class ProductModelTest(TestCase):
    def setUp(self):
        self.user = make_user("t3@test.cl")

    def test_margin_calculation(self):
        p = Product.objects.create(contractor=self.user, name="P1", unit="un", cost_price=1000, sale_price=1200)
        self.assertEqual(p.margin, 20.0)

    def test_margin_zero_cost(self):
        p = Product.objects.create(contractor=self.user, name="P2", unit="un", cost_price=0, sale_price=1000)
        self.assertEqual(p.margin, 0)


class APITest(TestCase):
    def setUp(self):
        self.tc = TestClient()
        self.user = make_user("apigeneral@test.cl")
        self.tc.login(username="apigeneral@test.cl", password="pass123")  # pragma: allowlist secret

    def test_stats_api(self):
        r = self.tc.get("/api/v1/stats/")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn("total_clients", data)
        self.assertIn("total_revenue", data)

    def test_clients_api_empty(self):
        r = self.tc.get("/api/v1/clientes/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["count"], 0)

    def test_products_api_empty(self):
        r = self.tc.get("/api/v1/productos/")
        self.assertEqual(r.status_code, 200)

    def test_api_requires_auth(self):
        self.tc.logout()
        r = self.tc.get("/api/v1/stats/")
        self.assertIn(r.status_code, [401, 403])

    def test_no_monthly_budget_limit(self):
        client_obj = Client.objects.create(contractor=self.user, name="C", phone="1")
        limit = settings.PLAN_FREE_MAX_BUDGETS_PER_MONTH
        for _ in range(limit):
            make_budget(self.user, client_obj)
        count_before = Budget.objects.filter(contractor=self.user).count()
        self.tc.post(
            reverse("budget_create"),
            {
                "client": client_obj.pk,
                "title": "Extra",
                "validity_days": 15,
                "tax_percent": 0,
                "payment_terms": "",
                "notes": "",
            },
        )
        # Sin límites de plan — el presupuesto se crea
        self.assertEqual(Budget.objects.filter(contractor=self.user).count(), count_before + 1)


def make_recipe(user, name="Receta test", rubro="Pintura"):
    recipe = MaterialRecipe.objects.create(
        contractor=user,
        name=name,
        rubro=rubro,
        icon="🎨",
        input_label="Superficie",
        input_unit="m²",
        input_placeholder="Ej: 20",
    )
    MaterialRecipeItem.objects.create(recipe=recipe, name="Pintura látex", unit="lt", quantity_factor="0.2500", order=0)
    return recipe


class RecipeModelTest(TestCase):
    def setUp(self):
        self.user = make_user("recmodel@test.cl")

    def test_str(self):
        recipe = make_recipe(self.user)
        self.assertEqual(str(recipe), "Receta test")

    def test_to_api_dict_structure(self):
        recipe = make_recipe(self.user)
        d = recipe.to_api_dict()
        self.assertEqual(d["name"], "Receta test")
        self.assertEqual(d["rubro"], "Pintura")
        self.assertEqual(len(d["items"]), 1)
        self.assertEqual(d["items"][0]["name"], "Pintura látex")
        self.assertEqual(d["items"][0]["unit"], "lt")
        self.assertEqual(d["items"][0]["factor"], "0.2500")


class RecipeViewTest(TestCase):
    def setUp(self):
        self.tc = TestClient()
        self.user = make_user("recview@test.cl")
        self.tc.login(username="recview@test.cl", password="pass123")  # pragma: allowlist secret
        self.recipe = make_recipe(self.user)

    def test_calculadora_get(self):
        r = self.tc.get(reverse("calculadora"))
        self.assertEqual(r.status_code, 200)

    def test_calculadora_requires_login(self):
        self.tc.logout()
        r = self.tc.get(reverse("calculadora"))
        self.assertEqual(r.status_code, 302)

    def test_recipe_list_ok(self):
        r = self.tc.get(reverse("recipe_list"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Receta test")

    def test_api_custom_recipes_returns_own(self):
        r = self.tc.get(reverse("api_custom_recipes"))
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["name"], "Receta test")
        self.assertEqual(len(data[0]["items"]), 1)

    def test_api_custom_recipes_requires_login(self):
        self.tc.logout()
        r = self.tc.get(reverse("api_custom_recipes"))
        self.assertEqual(r.status_code, 302)

    def test_api_does_not_return_other_users_recipes(self):
        other = make_user("other_rec@test.cl")
        make_recipe(other, name="Receta ajena")
        r = self.tc.get(reverse("api_custom_recipes"))
        names = [d["name"] for d in r.json()]
        self.assertNotIn("Receta ajena", names)

    def test_recipe_create_get(self):
        r = self.tc.get(reverse("recipe_create"))
        self.assertEqual(r.status_code, 200)

    def test_recipe_create_post_valid(self):
        r = self.tc.post(
            reverse("recipe_create"),
            {
                "name": "Nueva receta",
                "rubro": "Cerámica",
                "icon": "🟫",
                "input_label": "Superficie",
                "input_unit": "m²",
                "input_placeholder": "Ej: 20",
                "item_name[]": ["Cerámica"],
                "item_unit[]": ["m2"],
                "item_factor[]": ["1.1"],
            },
        )
        self.assertEqual(r.status_code, 302)
        self.assertTrue(MaterialRecipe.objects.filter(contractor=self.user, name="Nueva receta").exists())

    def test_recipe_create_post_invalid_no_name(self):
        r = self.tc.post(
            reverse("recipe_create"),
            {"name": "", "rubro": "Cerámica", "input_label": "Superficie", "input_unit": "m²"},
        )
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "obligatorio")

    def test_recipe_create_post_invalid_no_items(self):
        r = self.tc.post(
            reverse("recipe_create"),
            {"name": "Sin ítems", "rubro": "Pintura", "input_label": "Superficie", "input_unit": "m²"},
        )
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "al menos un material")

    def test_recipe_edit_post(self):
        r = self.tc.post(
            reverse("recipe_edit", args=[self.recipe.pk]),
            {
                "name": "Editada",
                "rubro": "Pintura",
                "icon": "🎨",
                "input_label": "Área",
                "input_unit": "m²",
                "input_placeholder": "",
                "item_name[]": ["Pintura nueva"],
                "item_unit[]": ["lt"],
                "item_factor[]": ["0.3"],
            },
        )
        self.assertEqual(r.status_code, 302)
        self.recipe.refresh_from_db()
        self.assertEqual(self.recipe.name, "Editada")
        self.assertEqual(self.recipe.items.count(), 1)
        self.assertEqual(self.recipe.items.first().name, "Pintura nueva")

    def test_recipe_delete_post(self):
        pk = self.recipe.pk
        r = self.tc.post(reverse("recipe_delete", args=[pk]))
        self.assertEqual(r.status_code, 302)
        self.assertFalse(MaterialRecipe.objects.filter(pk=pk).exists())

    def test_cannot_edit_other_users_recipe(self):
        other = make_user("other_edit@test.cl")
        other_recipe = make_recipe(other, name="Ajena")
        r = self.tc.post(
            reverse("recipe_edit", args=[other_recipe.pk]),
            {
                "name": "Hackeado",
                "rubro": "Pintura",
                "input_label": "Superficie",
                "input_unit": "m²",
                "item_name[]": ["X"],
                "item_unit[]": ["un"],
                "item_factor[]": ["1"],
            },
        )
        self.assertEqual(r.status_code, 404)
        other_recipe.refresh_from_db()
        self.assertEqual(other_recipe.name, "Ajena")

    def test_cannot_delete_other_users_recipe(self):
        other = make_user("other_del@test.cl")
        other_recipe = make_recipe(other, name="Ajena del")
        r = self.tc.post(reverse("recipe_delete", args=[other_recipe.pk]))
        self.assertEqual(r.status_code, 404)
        self.assertTrue(MaterialRecipe.objects.filter(pk=other_recipe.pk).exists())
