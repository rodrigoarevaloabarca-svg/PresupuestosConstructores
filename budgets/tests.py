from django.test import TestCase, Client as TestClient
from django.urls import reverse
from users.models import User, ContractorProfile
from clients.models import Client
from catalog.models import Product
from .models import Budget, BudgetItemMaterial, BudgetItemLabor


class BudgetModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='test', email='test@test.cl', password='pass123'
        )
        ContractorProfile.objects.create(
            user=self.user, company_name='Test SA', rut='12345678-9', phone='999'
        )
        self.client_obj = Client.objects.create(
            contractor=self.user, name='Cliente Test', phone='999'
        )
        self.budget = Budget.objects.create(
            contractor=self.user, client=self.client_obj,
            title='Obra Test', validity_days=15, tax_percent=0,
        )

    def test_budget_number_autoincrement(self):
        self.assertEqual(self.budget.number, 1)
        b2 = Budget.objects.create(
            contractor=self.user, client=self.client_obj, title='Obra 2'
        )
        self.assertEqual(b2.number, 2)

    def test_budget_totals(self):
        BudgetItemMaterial.objects.create(
            budget=self.budget, name='Mat A', unit='un', quantity=2, unit_price=1000
        )
        BudgetItemLabor.objects.create(
            budget=self.budget, name='MdO A', unit='gl', quantity=1, unit_price=5000
        )
        self.assertEqual(self.budget.subtotal_materials, 2000)
        self.assertEqual(self.budget.subtotal_labor, 5000)
        self.assertEqual(self.budget.total, 7000)

    def test_budget_total_with_iva(self):
        self.budget.tax_percent = 19
        self.budget.save()
        BudgetItemMaterial.objects.create(
            budget=self.budget, name='Mat', unit='un', quantity=1, unit_price=100000
        )
        self.assertEqual(self.budget.tax_amount, 19000)
        self.assertEqual(self.budget.total, 119000)

    def test_budget_valid_until(self):
        from django.utils import timezone
        from datetime import timedelta
        delta = self.budget.valid_until - self.budget.created_at
        self.assertAlmostEqual(delta.days, 15, delta=1)

    def test_str_representation(self):
        self.assertIn('Obra Test', str(self.budget))


class BudgetViewTest(TestCase):
    def setUp(self):
        self.tc = TestClient()
        self.user = User.objects.create_user(
            username='vtest', email='vtest@test.cl', password='pass123'
        )
        ContractorProfile.objects.create(
            user=self.user, company_name='Test SA', rut='12345678-9', phone='999'
        )
        self.client_obj = Client.objects.create(
            contractor=self.user, name='Cliente', phone='999'
        )
        self.tc.login(username='vtest@test.cl', password='pass123')

    def test_budget_list_requires_login(self):
        self.tc.logout()
        r = self.tc.get(reverse('budget_list'))
        self.assertEqual(r.status_code, 302)

    def test_budget_list_ok(self):
        r = self.tc.get(reverse('budget_list'))
        self.assertEqual(r.status_code, 200)

    def test_budget_create_get(self):
        r = self.tc.get(reverse('budget_create'))
        self.assertEqual(r.status_code, 200)

    def test_budget_create_post(self):
        r = self.tc.post(reverse('budget_create'), {
            'client': self.client_obj.pk,
            'title': 'Nueva Obra',
            'validity_days': 15,
            'tax_percent': 0,
            'payment_terms': '50/50',
            'notes': '',
        })
        self.assertEqual(Budget.objects.filter(contractor=self.user).count(), 1)

    def test_cannot_view_other_users_budget(self):
        other = User.objects.create_user(
            username='other', email='other@test.cl', password='pass123'
        )
        other_client = Client.objects.create(contractor=other, name='C', phone='1')
        b = Budget.objects.create(contractor=other, client=other_client, title='Ajena')
        r = self.tc.get(reverse('budget_detail', args=[b.pk]))
        self.assertEqual(r.status_code, 404)


class ClientModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='t2', email='t2@test.cl', password='pass'
        )

    def test_budget_count(self):
        c = Client.objects.create(contractor=self.user, name='C', phone='1')
        self.assertEqual(c.budget_count(), 0)

    def test_client_str(self):
        c = Client.objects.create(contractor=self.user, name='Pepe', phone='1')
        self.assertEqual(str(c), 'Pepe')


class ProductModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='t3', email='t3@test.cl', password='pass'
        )

    def test_margin_calculation(self):
        p = Product.objects.create(
            contractor=self.user, name='P1', unit='un',
            cost_price=1000, sale_price=1200
        )
        self.assertEqual(p.margin, 20.0)

    def test_margin_zero_cost(self):
        p = Product.objects.create(
            contractor=self.user, name='P2', unit='un',
            cost_price=0, sale_price=1000
        )
        self.assertEqual(p.margin, 0)


class APITest(TestCase):
    def setUp(self):
        self.tc = TestClient()
        self.user = User.objects.create_user(
            username='api', email='api@test.cl', password='pass123'
        )
        self.tc.login(username='api@test.cl', password='pass123')

    def test_stats_api(self):
        r = self.tc.get('/api/v1/stats/')
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn('total_clients', data)
        self.assertIn('total_revenue', data)

    def test_clients_api_empty(self):
        r = self.tc.get('/api/v1/clientes/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['count'], 0)

    def test_products_api_empty(self):
        r = self.tc.get('/api/v1/productos/')
        self.assertEqual(r.status_code, 200)

    def test_api_requires_auth(self):
        self.tc.logout()
        r = self.tc.get('/api/v1/stats/')
        self.assertIn(r.status_code, [401, 403])
