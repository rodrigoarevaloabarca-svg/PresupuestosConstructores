# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Constructor Express** is a Django SaaS platform for Chilean contractors (plumbers, electricians, carpenters, etc.) to create professional budget PDFs, manage clients, and track projects. It targets the Chilean market with CLP pricing, RUT validation, and IVA (VAT) calculations.

## Commands

### Development Setup
```bash
python -m venv .venv && source .venv/Scripts/activate  # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo      # loads demo data
python manage.py runserver
```
Demo credentials: `demo@constructorexpress.cl` / `Demo1234!`

### Tests
```bash
python manage.py test budgets clients catalog users
python manage.py test budgets.tests.BudgetModelTest   # single test class
```

### Utilities
```bash
python manage.py seed_demo              # create demo user + sample data
python manage.py clean_data --email user@example.com  # clear user data
python manage.py clean_data --all       # clear all data
```

### Docker (production-like)
```bash
docker-compose up   # runs PostgreSQL + gunicorn, auto-migrates, seeds demo
```

## Architecture

### Apps
- **users** — Custom User model (email-based auth), ContractorProfile, dashboard, reports, global search
- **clients** — Client CRUD
- **catalog** — Product catalog with CSV import/export, soft-delete via `is_active`
- **budgets** — Core business logic: budget builder, PDF generation (WeasyPrint), public sharing via tokens, email delivery

### Key Data Relationships
```
User (contractor)
  ├── ContractorProfile (company branding, RUT, logo, trade type)
  ├── Client[] → Budget[] → BudgetItemMaterial[] + BudgetItemLabor[]
  │                      └── BudgetPublicToken (shareable link, no auth)
  └── Product[] (catalog)
```

### Multi-Tenancy Pattern
Every model has `contractor = ForeignKey(User)`. All views filter with `filter(contractor=request.user)` — enforced manually, not at the ORM level. Never omit this filter in new views.

### Plan-Based Limits
Free vs. pro plans enforced in views using `request.user.is_pro()`. Limits are defined in `settings.py`:
```python
PLAN_FREE_MAX_CLIENTS = 10
PLAN_FREE_MAX_PRODUCTS = 20
PLAN_FREE_MAX_BUDGETS_PER_MONTH = 5
```

### Budget Items Submission
Budget items (materials and labor) are submitted as POST arrays (`mat_name[]`, `mat_qty[]`, etc.) and parsed by `_save_items()` in `budgets/views.py`. On edit, all items are deleted and re-created from scratch.

### Database
- Development: SQLite (auto-selected when `DB_NAME` env var is absent)
- Production: PostgreSQL (set `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`)

### PDF Generation
WeasyPrint renders `budgets/pdf_template.html`. If WeasyPrint is unavailable, the view falls back to HTML. System-level WeasyPrint dependencies (cairo, pango, etc.) are installed in the Dockerfile.

### Context Processor
`users/context_processors.py` injects `contractor_profile`, `is_pro`, and `plan_limits` into every template automatically.

### No-Cache Middleware
`users/middleware.NoCacheAuthMiddleware` adds `Cache-Control: no-store` headers to authenticated pages to prevent browser back-button exposure after logout.

### Custom Template Filter
`budgets/templatetags/budget_filters.py` provides `|clp` to format numbers as Chilean pesos: `1234567` → `$1.234.567`.

### URL Namespaces
- `/usuarios/` → users app (auth, profile)
- `/clientes/` → clients app
- `/catalogo/` → catalog app
- `/presupuestos/` → budgets app
- `/dashboard/` → dashboard, reports, search
- `/api/v1/` → DRF REST API (requires authentication)
- `/ver/<token>/` → public budget view (no auth required)

### Localization
- `LANGUAGE_CODE = 'es-cl'`, `TIME_ZONE = 'America/Santiago'`
- RUT validation regex: `^\d{7,8}[0-9K]$`
- All prices in CLP (no decimal places)
