from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import Client as TestClient
from django.test import TestCase
from django.urls import reverse

from users.models import ContractorProfile, User, validate_rut


def make_user(email="u@test.cl", password="pass123", with_profile=True):  # pragma: allowlist secret
    u = User.objects.create_user(username=email, email=email, password=password)  # pragma: allowlist secret
    if with_profile:
        ContractorProfile.objects.create(user=u, company_name="Empresa Test", rut="12345678-9", phone="999")
    return u


# ─── RUT validation ──────────────────────────────────────────────────────────


class RUTValidatorTest(TestCase):
    def test_valid_rut(self):
        # Should not raise
        validate_rut("12345678-9")
        validate_rut("12.345.678-9")

    def test_valid_rut_k(self):
        validate_rut("11111111-K")

    def test_invalid_rut_short(self):
        with self.assertRaises(ValidationError):
            validate_rut("123-4")

    def test_invalid_rut_letters(self):
        with self.assertRaises(ValidationError):
            validate_rut("ABCDEFGH-9")


# ─── Register ────────────────────────────────────────────────────────────────


class RegisterViewTest(TestCase):
    def setUp(self):
        self.tc = TestClient()

    def test_register_get(self):
        r = self.tc.get(reverse("register"))
        self.assertEqual(r.status_code, 200)

    def test_register_valid(self):
        self.tc.post(
            reverse("register"),
            {
                "email": "nuevo@test.cl",
                "username": "nuevo@test.cl",
                "password1": "Segura1234!",  # pragma: allowlist secret
                "password2": "Segura1234!",  # pragma: allowlist secret
                "company_name": "Mi Empresa",
                "rut": "12345678-9",
                "phone": "999",
                "rubro": "construccion",
            },
        )
        self.assertTrue(User.objects.filter(email="nuevo@test.cl").exists())

    def test_register_invalid_rut(self):
        self.tc.post(
            reverse("register"),
            {
                "email": "bad@test.cl",
                "username": "bad@test.cl",
                "password1": "Segura1234!",  # pragma: allowlist secret
                "password2": "Segura1234!",  # pragma: allowlist secret
                "company_name": "X",
                "rut": "INVALIDO",
                "phone": "999",
                "rubro": "otro",
            },
        )
        self.assertFalse(User.objects.filter(email="bad@test.cl").exists())


# ─── Login ───────────────────────────────────────────────────────────────────


class LoginViewTest(TestCase):
    def setUp(self):
        self.tc = TestClient()
        self.user = make_user()

    def test_login_success(self):
        r = self.tc.post(reverse("login"), {"username": "u@test.cl", "password": "pass123"})  # pragma: allowlist secret
        self.assertRedirects(r, reverse("dashboard"))

    def test_login_bad_credentials(self):
        r = self.tc.post(reverse("login"), {"username": "u@test.cl", "password": "wrong"})  # pragma: allowlist secret
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.wsgi_request.user.is_authenticated)

    def test_login_get(self):
        r = self.tc.get(reverse("login"))
        self.assertEqual(r.status_code, 200)


# ─── Logout + NoCacheAuth ─────────────────────────────────────────────────────


class LogoutTest(TestCase):
    def setUp(self):
        self.tc = TestClient()
        self.user = make_user()
        self.tc.login(username="u@test.cl", password="pass123")  # pragma: allowlist secret  # pragma: allowlist secret

    def test_logout_post(self):
        r = self.tc.post(reverse("logout"))
        self.assertRedirects(r, reverse("landing"))

    def test_authenticated_response_has_no_cache_header(self):
        r = self.tc.get(reverse("dashboard"))
        self.assertIn("no-store", r.get("Cache-Control", ""))


# ─── Profile ─────────────────────────────────────────────────────────────────


class ProfileViewTest(TestCase):
    def setUp(self):
        self.tc = TestClient()
        self.user = make_user()
        self.tc.login(username="u@test.cl", password="pass123")  # pragma: allowlist secret

    def test_profile_get(self):
        r = self.tc.get(reverse("profile"))
        self.assertEqual(r.status_code, 200)

    def test_profile_update(self):
        self.tc.post(
            reverse("profile"),
            {
                "company_name": "Nueva Empresa",
                "rut": "12345678-9",
                "phone": "888",
                "rubro": "electricidad",
                "city": "Valparaíso",
                "budget_validity_days": "30",
                "payment_terms": "100% al inicio",
                "notes_template": "",
                "brand_color": "#1e40af",
            },
        )
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.company_name, "Nueva Empresa")

    def test_profile_without_logo(self):
        self.tc.get(reverse("profile"))
        self.assertIsNone(self.user.profile.logo.name or None)


# ─── Context processor ───────────────────────────────────────────────────────


class ContextProcessorTest(TestCase):
    def setUp(self):
        self.tc = TestClient()
        self.user = make_user()
        self.tc.login(username="u@test.cl", password="pass123")  # pragma: allowlist secret

    def test_profile_in_context(self):
        r = self.tc.get(reverse("dashboard"))
        self.assertIn("contractor_profile", r.context)
        self.assertEqual(r.context["contractor_profile"].company_name, "Empresa Test")


# ─── Landing ─────────────────────────────────────────────────────────────────


class LandingViewTest(TestCase):
    def test_landing_renders(self):
        tc = TestClient()
        r = tc.get(reverse("landing"))
        self.assertEqual(r.status_code, 200)


# ─── Dashboard ───────────────────────────────────────────────────────────────


class DashboardViewTest(TestCase):
    def setUp(self):
        self.tc = TestClient()
        self.user = make_user()
        self.tc.login(username="u@test.cl", password="pass123")  # pragma: allowlist secret

    def test_dashboard_ok(self):
        r = self.tc.get(reverse("dashboard"))
        self.assertEqual(r.status_code, 200)

    def test_dashboard_uses_build_alerts(self):
        with patch("users.dashboard_views.build_alerts", return_value=[]) as mock_alerts:
            r = self.tc.get(reverse("dashboard"))
            mock_alerts.assert_called_once_with(self.user)
        self.assertEqual(r.status_code, 200)


# ─── Reports ─────────────────────────────────────────────────────────────────


class ReportsViewTest(TestCase):
    def setUp(self):
        self.tc = TestClient()
        self.user = make_user()
        self.tc.login(username="u@test.cl", password="pass123")  # pragma: allowlist secret

    def test_reports_ok(self):
        r = self.tc.get(reverse("reports"))
        self.assertEqual(r.status_code, 200)

    def test_reports_has_months_data(self):
        r = self.tc.get(reverse("reports"))
        self.assertIn("months_data", r.context)
        self.assertEqual(len(r.context["months_data"]), 6)


# ─── Search ──────────────────────────────────────────────────────────────────


class SearchViewTest(TestCase):
    def setUp(self):
        self.tc = TestClient()
        self.user_a = make_user("sa@test.cl")
        self.user_b = make_user("sb@test.cl")
        self.tc.login(username="sa@test.cl", password="pass123")  # pragma: allowlist secret

    def test_search_requires_login(self):
        self.tc.logout()
        r = self.tc.get(reverse("global_search") + "?q=test")
        self.assertEqual(r.status_code, 302)

    def test_search_returns_200(self):
        r = self.tc.get(reverse("global_search") + "?q=algo")
        self.assertEqual(r.status_code, 200)

    def test_search_isolation(self):
        from clients.models import Client

        Client.objects.create(contractor=self.user_b, name="Cliente Ajeno", phone="1")
        r = self.tc.get(reverse("global_search") + "?q=Ajeno")
        # Los resultados no deben incluir datos del otro tenant
        self.assertNotContains(r, "Cliente Ajeno")


# ─── build_alerts service ─────────────────────────────────────────────────────


class BuildAlertsTest(TestCase):
    def setUp(self):
        self.user = make_user("alerts@test.cl")

    def test_build_alerts_no_budgets(self):
        from users.services.dashboard_alerts import build_alerts

        alerts = build_alerts(self.user)
        # Sin presupuestos: solo alerta de logo si no tiene logo
        self.assertIsInstance(alerts, list)

    def test_build_alerts_no_request_factory_needed(self):
        """Verifica que build_alerts no requiere RequestFactory."""
        from users.services.dashboard_alerts import build_alerts

        alerts = build_alerts(self.user)
        self.assertIsInstance(alerts, list)


# ─── Password reset flow ─────────────────────────────────────────────────────


class PasswordResetFlowTest(TestCase):
    def setUp(self):
        self.tc = TestClient()
        self.user = make_user("reset@test.cl", "OldPass1234!")

    def _generate_token(self, user):
        from django.contrib.auth.tokens import PasswordResetTokenGenerator
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode

        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = PasswordResetTokenGenerator().make_token(user)
        return uidb64, token

    def test_request_get(self):
        r = self.tc.get(reverse("password_reset_request"))
        self.assertEqual(r.status_code, 200)

    def test_request_existing_email_sends_mail(self):
        from django.core import mail

        r = self.tc.post(reverse("password_reset_request"), {"email": "reset@test.cl"})
        self.assertRedirects(r, reverse("password_reset_sent"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("reset@test.cl", mail.outbox[0].to)
        self.assertIn("/usuarios/resetear-clave/", mail.outbox[0].body)

    def test_request_unknown_email_silent(self):
        from django.core import mail

        r = self.tc.post(reverse("password_reset_request"), {"email": "fantasma@test.cl"})
        # Redirige al mismo destino para no revelar si el email existe
        self.assertRedirects(r, reverse("password_reset_sent"))
        self.assertEqual(len(mail.outbox), 0)

    def test_request_case_insensitive_match(self):
        from django.core import mail

        self.tc.post(reverse("password_reset_request"), {"email": "Reset@Test.CL"})
        self.assertEqual(len(mail.outbox), 1)

    def test_confirm_valid_token_get(self):
        uidb64, token = self._generate_token(self.user)
        r = self.tc.get(reverse("password_reset_confirm", args=[uidb64, token]))
        self.assertEqual(r.status_code, 200)

    def test_confirm_valid_token_updates_password(self):
        uidb64, token = self._generate_token(self.user)
        r = self.tc.post(
            reverse("password_reset_confirm", args=[uidb64, token]),
            {
                "new_password1": "NuevaClave9876!",  # pragma: allowlist secret  # pragma: allowlist secret
                "new_password2": "NuevaClave9876!",  # pragma: allowlist secret  # pragma: allowlist secret
            },
        )
        self.assertRedirects(r, reverse("password_reset_complete"))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NuevaClave9876!"))  # pragma: allowlist secret

    def test_confirm_mismatched_passwords_rejected(self):
        uidb64, token = self._generate_token(self.user)
        r = self.tc.post(
            reverse("password_reset_confirm", args=[uidb64, token]),
            {
                "new_password1": "NuevaClave9876!",  # pragma: allowlist secret
                "new_password2": "Otra9876!",  # pragma: allowlist secret
            },
        )
        self.assertEqual(r.status_code, 200)
        self.user.refresh_from_db()
        self.assertFalse(self.user.check_password("NuevaClave9876!"))  # pragma: allowlist secret

    def test_confirm_invalid_token_rejects(self):
        uidb64, _ = self._generate_token(self.user)
        r = self.tc.get(reverse("password_reset_confirm", args=[uidb64, "token-falso"]))
        self.assertEqual(r.status_code, 400)

    def test_confirm_invalid_uid_rejects(self):
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode

        _, token = self._generate_token(self.user)
        ghost_uid = urlsafe_base64_encode(force_bytes(999999))
        r = self.tc.get(reverse("password_reset_confirm", args=[ghost_uid, token]))
        self.assertEqual(r.status_code, 400)

    def test_confirm_token_single_use(self):
        uidb64, token = self._generate_token(self.user)
        self.tc.post(
            reverse("password_reset_confirm", args=[uidb64, token]),
            {
                "new_password1": "NuevaClave9876!",  # pragma: allowlist secret
                "new_password2": "NuevaClave9876!",  # pragma: allowlist secret
            },
        )
        # Reusar el mismo token tras cambiar la password debe fallar
        r = self.tc.get(reverse("password_reset_confirm", args=[uidb64, token]))
        self.assertEqual(r.status_code, 400)

    def test_sent_page_renders(self):
        r = self.tc.get(reverse("password_reset_sent"))
        self.assertEqual(r.status_code, 200)

    def test_complete_page_renders(self):
        r = self.tc.get(reverse("password_reset_complete"))
        self.assertEqual(r.status_code, 200)

    def test_login_page_links_to_reset(self):
        r = self.tc.get(reverse("login"))
        self.assertContains(r, reverse("password_reset_request"))
