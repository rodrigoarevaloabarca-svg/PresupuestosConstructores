# Constructor Express — Documentación de API REST

**Base URL:** `https://constructorexpress.cl/api/v1`  
**Autenticación:** JWT Bearer token en header `Authorization: Bearer <token>`  
**Formato:** JSON  
**Throttling:** 1 000 req/hora por usuario autenticado · 100 req/hora anónimo  
**Paginación:** `?page=N` — 20 resultados por página  

> **Swagger UI interactivo:** `/api/v1/docs/`  
> **Schema OpenAPI (JSON):** `/api/v1/schema/`

---

## Autenticación JWT

### Obtener tokens

```
POST /api/v1/auth/token/
```

**Body:**
```json
{
  "email": "demo@constructorexpress.cl",
  "password": "Demo1234!"
}
```

**Respuesta 200:**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "contractor_id": 1,
  "email": "demo@constructorexpress.cl",
  "is_pro": false
}
```

El token `access` expira en **1 hora**. El `refresh` en **7 días**.

---

### Renovar access token

```
POST /api/v1/auth/refresh/
```

```json
{ "refresh": "<refresh_token>" }
```

**Respuesta 200:** `{ "access": "<nuevo_access_token>" }`

---

### Revocar (blacklist) refresh token

```
POST /api/v1/auth/blacklist/
```

```json
{ "refresh": "<refresh_token>" }
```

**Respuesta 200:** `{}`

---

## Dashboard

### Estadísticas generales

```
GET /api/v1/stats/
```

**Respuesta 200:**
```json
{
  "total_clients": 8,
  "total_products": 15,
  "total_budgets": 23,
  "budgets_this_month": 4,
  "accepted_budgets": 14,
  "pending_budgets": 5,
  "total_revenue": 4850000,
  "pending_revenue": 980000,
  "conversion_rate": 60.9
}
```

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `total_revenue` | int (CLP) | Ingresos de presupuestos aceptados |
| `pending_revenue` | int (CLP) | Monto en presupuestos enviados |
| `conversion_rate` | float (%) | aceptados / total × 100 |

---

## Presupuestos

### Listar presupuestos

```
GET /api/v1/presupuestos/
GET /api/v1/presupuestos/?status=enviado
```

**Parámetros de query:**

| Param | Valores | Descripción |
|-------|---------|-------------|
| `status` | `borrador` `enviado` `aceptado` `rechazado` `vencido` | Filtrar por estado |
| `page` | int | Página de resultados |

**Respuesta 200:**
```json
{
  "count": 23,
  "next": "https://…/api/v1/presupuestos/?page=2",
  "previous": null,
  "results": [
    {
      "id": 7,
      "number": 7,
      "title": "Reparación baño — Las Rosas",
      "client_name": "María González",
      "status": "enviado",
      "status_display": "Enviado al Cliente",
      "total": 252700,
      "created_at": "2026-04-10T14:32:00Z"
    }
  ]
}
```

---

### Detalle de presupuesto (lectura)

```
GET /api/v1/presupuestos/{id}/
```

**Respuesta 200:**
```json
{
  "id": 7,
  "number": 7,
  "version": 1,
  "title": "Reparación baño — Las Rosas",
  "client_name": "María González",
  "status": "enviado",
  "status_display": "Enviado al Cliente",
  "tax_percent": "19.00",
  "subtotal_materials": 122700,
  "subtotal_labor": 130000,
  "tax_amount": 47823,
  "total": 300523,
  "valid_until": "2026-04-25",
  "created_at": "2026-04-10T14:32:00Z",
  "material_items": [
    {
      "id": 12,
      "name": "Grifería mezcladora",
      "unit": "un",
      "unit_display": "Unidad",
      "quantity": "1.00",
      "unit_price": 45000,
      "total": 45000
    }
  ],
  "labor_items": [
    {
      "id": 8,
      "name": "Instalación completa de baño",
      "unit": "gl",
      "unit_display": "Global",
      "quantity": "1.00",
      "unit_price": 130000,
      "total": 130000
    }
  ]
}
```

---

### CRUD completo de presupuestos (write)

El ViewSet de escritura permite crear y modificar presupuestos **incluyendo sus ítems** en una sola request.

#### Listar / crear

```
GET  /api/v1/presupuestos/write/
POST /api/v1/presupuestos/write/
```

#### Detalle / actualizar / eliminar

```
GET    /api/v1/presupuestos/write/{id}/
PUT    /api/v1/presupuestos/write/{id}/
PATCH  /api/v1/presupuestos/write/{id}/
DELETE /api/v1/presupuestos/write/{id}/
```

**Body de creación (POST):**
```json
{
  "client": 3,
  "title": "Instalación eléctrica bodega",
  "tax_percent": "19.00",
  "validity_days": 15,
  "payment_terms": "50% anticipo, 50% a la entrega",
  "notes": "Incluye materiales",
  "material_items": [
    {
      "name": "Cable 2.5mm THHN",
      "unit": "ml",
      "quantity": "50.00",
      "unit_price": 890
    }
  ],
  "labor_items": [
    {
      "name": "Mano de obra eléctrica",
      "unit": "gl",
      "quantity": "1.00",
      "unit_price": 180000
    }
  ]
}
```

**Respuesta 201:** el presupuesto creado en formato detalle.

> El campo `number` se asigna automáticamente (secuencial por contratista). No incluirlo en el body.

---

**Errores comunes:**

| Código | Motivo |
|--------|--------|
| `400` | Datos inválidos (cliente no existe, precio negativo, etc.) |
| `403` | Sin permisos o límite de plan gratuito alcanzado |
| `404` | Presupuesto no existe o pertenece a otro contratista |

---

## Clientes

### Listar / crear

```
GET  /api/v1/clientes/
POST /api/v1/clientes/
```

**Body (POST):**
```json
{
  "name": "Pedro Soto Construcciones",
  "rut": "12.345.678-9",
  "phone": "+56912345678",
  "email": "pedro@soto.cl",
  "address": "Av. Apoquindo 1234, Las Condes",
  "city": "Santiago",
  "notes": "Referido por María González"
}
```

**Respuesta 201:**
```json
{
  "id": 9,
  "name": "Pedro Soto Construcciones",
  "rut": "12.345.678-9",
  "phone": "+56912345678",
  "email": "pedro@soto.cl",
  "address": "Av. Apoquindo 1234, Las Condes",
  "city": "Santiago",
  "notes": "Referido por María González",
  "budget_count": 0,
  "created_at": "2026-04-18T10:00:00Z"
}
```

**403** si el plan gratuito ya tiene 10 clientes.

---

### Detalle / editar / eliminar

```
GET    /api/v1/clientes/{id}/
PUT    /api/v1/clientes/{id}/
PATCH  /api/v1/clientes/{id}/
DELETE /api/v1/clientes/{id}/
```

---

## Productos (catálogo propio)

### Listar / crear

```
GET  /api/v1/productos/
GET  /api/v1/productos/?q=cemento
POST /api/v1/productos/
```

**Parámetros de query:**

| Param | Descripción |
|-------|-------------|
| `q` | Búsqueda por nombre (icontains) |

**Body (POST):**
```json
{
  "name": "Cemento Portland 25kg",
  "description": "Bolsa de 25kg marca Melón",
  "category": "materiales",
  "unit": "bls",
  "cost_price": 4200,
  "sale_price": 5500,
  "sku": "CEM-025"
}
```

**Categorías disponibles:** `materiales` `herramientas` `electricidad` `gasfiteria` `ceramica` `pintura` `madera` `otro`

**Unidades disponibles:** `un` `m2` `m3` `ml` `kg` `lt` `hr` `gl` `bls` `pk`

**403** si el plan gratuito ya tiene 20 productos.

---

### Detalle / editar / eliminar

```
GET    /api/v1/productos/{id}/
PUT    /api/v1/productos/{id}/
PATCH  /api/v1/productos/{id}/
DELETE /api/v1/productos/{id}/
```

---

## Sugerencias de productos (ferreterías)

Endpoint de autocompletado que combina el catálogo propio del contratista con precios en tiempo real de ferreterías externas (Sodimac, Easy, Imperial).

```
GET /api/v1/productos/sugerencias/?q=cemento
GET /api/v1/productos/sugerencias/?q=cemento&limit=8
```

**Throttle:** 60 req/min por usuario.

**Parámetros de query:**

| Param | Tipo | Default | Descripción |
|-------|------|---------|-------------|
| `q` | string | — | Término de búsqueda (mín. 3 caracteres) |
| `limit` | int | 10 | Máximo de resultados (tope: 20) |

**Respuesta 200:** Si `q` tiene ≤ 2 caracteres retorna `[]`.

```json
[
  {
    "source": "catalog",
    "name": "Cemento Especial 25kg",
    "price": 4800,
    "unit": "bls"
  },
  {
    "source": "sodimac",
    "name": "Cemento Portland 25kg Melón",
    "price": 4990,
    "url": "https://www.sodimac.com/sodimac-cl/product/..."
  },
  {
    "source": "easy",
    "name": "Cemento Melón 25kg",
    "price": 5290,
    "url": "https://www.easy.cl/..."
  },
  {
    "source": "imperial",
    "name": "Cemento 25kg Imperial",
    "price": 4750,
    "url": "https://www.imperial.cl/..."
  }
]
```

**Campos por fuente:**

| Campo | `catalog` | `sodimac` / `easy` / `imperial` |
|-------|-----------|----------------------------------|
| `source` | `"catalog"` | nombre del retailer |
| `name` | ✅ | ✅ |
| `price` | precio venta (CLP) | precio de referencia (CLP) |
| `unit` | ✅ | ❌ |
| `url` | ❌ | ✅ |

> Los precios de ferretería son de **referencia** — el maestro debe ajustar su margen antes de usar en el presupuesto.

---

## Webhooks

### MercadoPago

```
POST /api/webhooks/mercadopago/
```

Endpoint para recibir notificaciones de pago de MercadoPago. Valida firma HMAC con `MP_WEBHOOK_SECRET`. No requiere autenticación JWT.

---

## Códigos de estado

| Código | Significado |
|--------|-------------|
| `200` | OK |
| `201` | Recurso creado |
| `204` | Eliminado sin contenido |
| `400` | Request inválida (ver campo `detail` o errores por campo) |
| `401` | No autenticado — token faltante o expirado |
| `403` | Sin permisos o límite de plan alcanzado |
| `404` | Recurso no encontrado o de otro contratista |
| `429` | Throttle excedido |

---

## Multi-tenancy

Todos los recursos están **aislados por contratista**. Un token JWT solo permite ver y modificar los datos del contratista que se autenticó. El backend filtra siempre por `contractor=request.user` — no existe forma de acceder a datos de otro usuario.

---

## Versionado de presupuestos

Cuando se edita un presupuesto en estado `enviado`, `aceptado` o `rechazado`, el sistema **crea automáticamente una nueva versión** (v2, v3…) en estado `borrador`, preservando la versión original intacta.

Los campos relevantes en la respuesta:

```json
{
  "id": 12,
  "number": 7,
  "version": 2,
  "parent": 7,
  ...
}
```

`number` identifica el presupuesto; `version` identifica la revisión.

---

## Firma digital

El cliente puede aceptar un presupuesto firmando en la vista pública. La firma se almacena como PNG + hash SHA-256 + IP + user-agent. No hay endpoint REST para esto — ocurre en la vista pública HTML (`/presupuestos/ver/<token>/firmar/`).

---

## Clientes SDK recomendados

```python
# Python
import httpx

BASE = "https://constructorexpress.cl/api/v1"

def get_token(email, password):
    r = httpx.post(f"{BASE}/auth/token/", json={"email": email, "password": password})
    return r.json()["access"]

token = get_token("demo@constructorexpress.cl", "Demo1234!")
headers = {"Authorization": f"Bearer {token}"}

# Listar presupuestos
presupuestos = httpx.get(f"{BASE}/presupuestos/", headers=headers).json()
```

```javascript
// JavaScript / Node
const BASE = 'https://constructorexpress.cl/api/v1';

async function getToken(email, password) {
  const res = await fetch(`${BASE}/auth/token/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  return (await res.json()).access;
}

const token = await getToken('demo@constructorexpress.cl', 'Demo1234!');
const headers = { Authorization: `Bearer ${token}` };

// Sugerencias de productos
const sugerencias = await fetch(
  `${BASE}/productos/sugerencias/?q=cemento`, { headers }
).then(r => r.json());
```
