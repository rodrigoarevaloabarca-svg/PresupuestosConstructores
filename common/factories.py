import factory
from factory.django import DjangoModelFactory

from budgets.models import Budget, BudgetItemLabor, BudgetItemMaterial
from catalog.models import Product
from clients.models import Client
from users.models import ContractorProfile, User


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f'user{n}@test.cl')
    username = factory.LazyAttribute(lambda o: o.email)
    password = factory.PostGenerationMethodCall('set_password', 'pass123')


class ContractorProfileFactory(DjangoModelFactory):
    class Meta:
        model = ContractorProfile

    user = factory.SubFactory(UserFactory)
    company_name = factory.Sequence(lambda n: f'Empresa {n}')
    rut = '12345678-9'
    phone = '999'


class ClientFactory(DjangoModelFactory):
    class Meta:
        model = Client

    contractor = factory.SubFactory(UserFactory)
    name = factory.Sequence(lambda n: f'Cliente {n}')
    phone = '999'


class ProductFactory(DjangoModelFactory):
    class Meta:
        model = Product

    contractor = factory.SubFactory(UserFactory)
    name = factory.Sequence(lambda n: f'Producto {n}')
    unit = 'un'
    cost_price = 1000
    sale_price = 1500


class BudgetFactory(DjangoModelFactory):
    class Meta:
        model = Budget

    contractor = factory.SubFactory(UserFactory)
    client = factory.SubFactory(ClientFactory, contractor=factory.SelfAttribute('..contractor'))
    title = factory.Sequence(lambda n: f'Presupuesto {n}')
    validity_days = 15
    tax_percent = 0

    @factory.post_generation
    def with_items(self, create, extracted, **kwargs):
        if not create or not extracted:
            return
        BudgetItemMaterialFactory(budget=self)
        BudgetItemLaborFactory(budget=self)


class BudgetItemMaterialFactory(DjangoModelFactory):
    class Meta:
        model = BudgetItemMaterial

    budget = factory.SubFactory(BudgetFactory)
    name = factory.Sequence(lambda n: f'Material {n}')
    unit = 'un'
    quantity = 2
    unit_price = 1000
    order = 0


class BudgetItemLaborFactory(DjangoModelFactory):
    class Meta:
        model = BudgetItemLabor

    budget = factory.SubFactory(BudgetFactory)
    name = factory.Sequence(lambda n: f'Trabajo {n}')
    unit = 'gl'
    quantity = 1
    unit_price = 5000
    order = 0
