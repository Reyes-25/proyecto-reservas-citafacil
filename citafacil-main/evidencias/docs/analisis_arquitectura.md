# Análisis de Arquitectura - Proyecto Citafacil

**Fecha:** 27/10/2026
**Herramienta de IA:** GitHub Copilot Chat
**Objetivo:** Comprender la estructura del proyecto antes de modificarlo.

## 1. Estructura de Carpetas

- **`backend/app/`**: Aplicación FastAPI.
  - `main.py`: Crea la app y registra los routers.
  - `models.py`: Define las tablas (Service, Appointment) con SQLAlchemy.
  - `availability.py`: Calcula horarios disponibles y verifica conflictos.
  - `routers/public.py`: Endpoints públicos (reservar, consultar disponibilidad).
  - `routers/admin.py`: Endpoints administrativos.
- **`frontend/`**: HTML + JS sin framework.
  - `index.html`: Página de clientes (reserva).
  - `admin.html`: Panel de administración.
- **`backend/tests/`**: Pruebas con `TestClient`.

## 2. Base de Datos

- **ORM:** SQLAlchemy (`database.py`).
- **Motor:** SQLite por defecto (`DATABASE_URL`), configurable a PostgreSQL.
- **Modelos principales:**
  - `Service`: id, nombre, duración, precio, activo.
  - `Appointment`: id, cliente, service_id, inicio, fin, estado.
- **Creación de tablas:** `Base.metadata.create_all` en el arranque.

## 3. Punto de Entrada para el Calendario Dinámico

- **Endpoint existente:** `GET /api/availability` en `backend/app/routers/public.py`.
- **Lógica:** Delegada a `generate_slots` en `availability.py`.
- **Para el calendario dinámico:**
  - Modificar `public.py` para agregar un endpoint de disponibilidad por rango de fechas (ej. `/api/availability/range`).
  - Ampliar `availability.py` para calcular varios días.
  - Integrar el consumo en `frontend/index.html`.
  - Añadir pruebas en `backend/tests/test_booking.py`.

**Decisión del equipo:** El análisis es correcto y coincide con la estructura observada. Aceptamos el plan de acción.