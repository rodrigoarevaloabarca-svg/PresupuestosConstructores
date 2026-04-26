from django.conf import settings
from django.test import Client as TestClient
from django.test import TestCase
from django.urls import reverse

from clients.models import Client
from clients.serializers import ClientSerializer
from users.models import ContractorProfile, User


def make_user(email="user@test.cl", password="pass123", with_profile=True):  # pragma: allowlist secret
    u = User.objects.create_user(username=email, email=email, password=password)  # pragma: allowlist secret
    if with_profile:
        ContractorProfile.objects.create(user=u, company_name="Empresa", rut="12345678-9", phone="999")
    return u


class ClientCRUDViewTest(TestCase):
    def setUp(self):
        self.tc = TestClient()
        self.user = make_user()
        self.tc.login(username="user@test.cl", password="pass123")  # pragma: allowlist secret

    def test_client_list_ok(self):
        r = self.tc.get(reverse("client_list"))
        self.assertEqual(r.status_code, 200)

    def test_client_list_requires_login(self):
        self.tc.logout()
        r = self.tc.get(reverse("client_list"))
        self.assertEqual(r.status_code, 302)

    def test_client_create_get(self):
        r = self.tc.get(reverse("client_create"))
        self.assertEqual(r.status_code, 200)

    def test_client_create_post(self):
        r = self.tc.post(
            reverse("client_create"),
            {
                "name": "Pedro Pérez",
                "phone": "123456",
                "email": "",
                "rut": "",
                "address": "",
                "city": "",
                "notes": "",
            },
        )
        self.assertEqual(Client.objects.filter(contractor=self.user).count(), 1)
        self.assertRedirects(r, reverse("client_list"))

    def test_client_edit(self):
        c = Client.objects.create(contractor=self.user, name="Original", phone="1")
        self.tc.post(
            reverse("client_edit", args=[c.pk]),
            {
                "name": "Editado",
                "phone": "2",
                "email": "",
                "rut": "",
                "address": "",
                "city": "",
                "notes": "",
            },
        )
        c.refresh_from_db()
        self.assertEqual(c.name, "Editado")

    def test_client_delete(self):
        c = Client.objects.create(contractor=self.user, name="Borrar", phone="1")
        self.tc.post(reverse("client_delete", args=[c.pk]))
        self.assertFalse(Client.objects.filter(pk=c.pk).exists())

    def test_client_detail_ok(self):
        c = Client.objects.create(contractor=self.user, name="Detalle", phone="1")
        r = self.tc.get(reverse("client_detail", args=[c.pk]))
        self.assertEqual(r.status_code, 200)


class ClientMultiTenantTest(TestCase):
    def setUp(self):
        self.tc = TestClient()
        self.user_a = make_user("a@test.cl")
        self.user_b = make_user("b@test.cl")
        self.client_b = Client.objects.create(contractor=self.user_b, name="De B", phone="1")
        self.tc.login(username="a@test.cl", password="pass123")  # pragma: allowlist secret

    def test_user_a_cannot_see_client_of_b(self):
        r = self.tc.get(reverse("client_detail", args=[self.client_b.pk]))
        self.assertEqual(r.status_code, 404)

    def test_user_a_cannot_edit_client_of_b(self):
        r = self.tc.post(
            reverse("client_edit", args=[self.client_b.pk]),
            {
                "name": "Hack",
                "phone": "0",
                "email": "",
                "rut": "",
                "address": "",
                "city": "",
                "notes": "",
            },
        )
        self.assertEqual(r.status_code, 404)

    def test_client_list_only_shows_own(self):
        Client.objects.create(contractor=self.user_a, name="De A", phone="1")
        r = self.tc.get(reverse("client_list"))
        self.assertContains(r, "De A")
        self.assertNotContains(r, "De B")


class ClientPlanLimitTest(TestCase):
    def setUp(self):
        self.tc = TestClient()
        self.user = make_user("limit@test.cl")
        self.tc.login(username="limit@test.cl", password="pass123")  # pragma: allowlist secret
        limit = settings.PLAN_FREE_MAX_CLIENTS
        for i in range(limit):
            Client.objects.create(contractor=self.user, name=f"C{i}", phone="1")

    def test_extra_client_allowed(self):
        self.tc.post(
            reverse("client_create"),
            {
                "name": "Extra",
                "phone": "1",
                "email": "",
                "rut": "",
                "address": "",
                "city": "",
                "notes": "",
            },
        )
        # Sin límites de plan — el cliente se crea
        self.assertEqual(
            Client.objects.filter(contractor=self.user).count(),
            settings.PLAN_FREE_MAX_CLIENTS + 1,
        )


class ClientModelTest(TestCase):
    def setUp(self):
        self.user = make_user("model@test.cl")

    def test_budget_count_empty(self):
        c = Client.objects.create(contractor=self.user, name="C", phone="1")
        self.assertEqual(c.budget_count(), 0)

    def test_str(self):
        c = Client.objects.create(contractor=self.user, name="Pepe", phone="1")
        self.assertEqual(str(c), "Pepe")


class ClientAPITest(TestCase):
    def setUp(self):
        self.tc = TestClient()
        self.user = make_user("api@test.cl")
        self.tc.login(username="api@test.cl", password="pass123")  # pragma: allowlist secret

    def test_api_list_empty(self):
        r = self.tc.get("/api/v1/clientes/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["count"], 0)

    def test_api_create(self):
        r = self.tc.post("/api/v1/clientes/", {"name": "API Client", "phone": "1"}, content_type="application/json")
        self.assertEqual(r.status_code, 201)
        self.assertEqual(Client.objects.filter(contractor=self.user).count(), 1)

    def test_api_detail(self):
        c = Client.objects.create(contractor=self.user, name="Det", phone="1")
        r = self.tc.get(f"/api/v1/clientes/{c.pk}/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["name"], "Det")

    def test_api_update(self):
        c = Client.objects.create(contractor=self.user, name="Old", phone="1")
        r = self.tc.patch(f"/api/v1/clientes/{c.pk}/", {"name": "New"}, content_type="application/json")
        self.assertEqual(r.status_code, 200)
        c.refresh_from_db()
        self.assertEqual(c.name, "New")

    def test_api_delete(self):
        c = Client.objects.create(contractor=self.user, name="Del", phone="1")
        r = self.tc.delete(f"/api/v1/clientes/{c.pk}/")
        self.assertEqual(r.status_code, 204)
        self.assertFalse(Client.objects.filter(pk=c.pk).exists())

    def test_api_isolation(self):
        other = make_user("other@test.cl")
        c_other = Client.objects.create(contractor=other, name="Ajena", phone="1")
        r = self.tc.get(f"/api/v1/clientes/{c_other.pk}/")
        self.assertEqual(r.status_code, 404)

    def test_serializer_valid(self):
        data = {"name": "Valid", "phone": "999", "email": "", "rut": "", "address": "", "city": "", "notes": ""}
        s = ClientSerializer(data=data)
        self.assertTrue(s.is_valid())

    def test_serializer_missing_name(self):
        s = ClientSerializer(data={"phone": "999"})
        self.assertFalse(s.is_valid())
        self.assertIn("name", s.errors)
