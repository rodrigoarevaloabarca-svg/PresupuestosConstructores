import pytest
from django.test import Client as DjangoClient

from common.factories import ContractorProfileFactory, UserFactory


@pytest.fixture
def tenant_user(db):
    """Usuario con perfil completo de contratista."""
    user = UserFactory()
    ContractorProfileFactory(user=user)
    return user


@pytest.fixture
def another_tenant(db):
    """Segundo usuario para tests de aislamiento multi-tenant."""
    user = UserFactory()
    ContractorProfileFactory(user=user)
    return user


@pytest.fixture
def authenticated_client(tenant_user):
    """Django test Client con sesión iniciada para tenant_user."""
    client = DjangoClient()
    client.force_login(tenant_user)
    return client
