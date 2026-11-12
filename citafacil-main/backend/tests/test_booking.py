"""Tests de la lógica de reservas y de la API."""
import os

# Usar una base de datos de prueba aislada ANTES de importar la app.
# (Se usa /tmp para evitar límites de E/S de sistemas de archivos de red.)
os.environ["DATABASE_URL"] = "sqlite:////tmp/citafacil_test.db"
os.environ["ADMIN_TOKEN"] = "test-token"

from datetime import timedelta  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app import models  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.utils import PhoneError, local_now, normalize_cl_phone  # noqa: E402

client = TestClient(app)


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    db.add(models.Service(name="Corte", duration_min=30, price=8000, active=True))
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)


def _next_open_day_at(hour: int):
    d = (local_now() + timedelta(days=1)).replace(hour=hour, minute=0, second=0, microsecond=0)
    while d.weekday() == 6:  # saltar domingo
        d += timedelta(days=1)
    return d


# ---------- Validación de teléfono ----------
def test_phone_valid_formats():
    assert normalize_cl_phone("+56 9 4291 6570") == "+56942916570"
    assert normalize_cl_phone("942916570") == "+56942916570"
    assert normalize_cl_phone("56942916570") == "+56942916570"
    assert normalize_cl_phone("4291 6570") == "+56942916570"  # 8 dígitos -> antepone 9


def test_phone_invalid():
    with pytest.raises(PhoneError):
        normalize_cl_phone("12345")


# ---------- Reservas ----------
def test_create_and_conflict():
    sid = client.get("/api/services").json()[0]["id"]
    start = _next_open_day_at(11)
    payload = {
        "customer_name": "Camila",
        "customer_phone": "+56 9 8765 4321",
        "service_id": sid,
        "start_at": start.isoformat(),
    }
    r = client.post("/api/appointments", json=payload)
    assert r.status_code == 201, r.text

    # mismo horario -> 409 (no doble-booking)
    r2 = client.post("/api/appointments", json={**payload, "customer_name": "Otro"})
    assert r2.status_code == 409


def test_availability_removes_booked_slot():
    sid = client.get("/api/services").json()[0]["id"]
    day = _next_open_day_at(11)
    date_str = day.date().isoformat()

    before = client.get(f"/api/availability?service_id={sid}&date={date_str}").json()
    assert "11:00" in before

    client.post(
        "/api/appointments",
        json={
            "customer_name": "Ana",
            "customer_phone": "942916570",
            "service_id": sid,
            "start_at": day.isoformat(),
        },
    )
    after = client.get(f"/api/availability?service_id={sid}&date={date_str}").json()
    assert "11:00" not in after


def test_reject_invalid_phone_on_booking():
    sid = client.get("/api/services").json()[0]["id"]
    start = _next_open_day_at(13)
    r = client.post(
        "/api/appointments",
        json={
            "customer_name": "Mal Tel",
            "customer_phone": "123",
            "service_id": sid,
            "start_at": start.isoformat(),
        },
    )
    assert r.status_code == 422  # falla validación de teléfono


def test_booking_with_email_sends_confirmation(monkeypatch):
    sent = {}

    def fake_send(to_email, subject, body):
        sent.update(to=to_email, subject=subject, body=body)
        return {"ok": True, "mode": "test"}

    monkeypatch.setattr("app.routers.public.send_email", fake_send)

    sid = client.get("/api/services").json()[0]["id"]
    start = _next_open_day_at(11)
    r = client.post(
        "/api/appointments",
        json={
            "customer_name": "Camila",
            "customer_phone": "942916570",
            "customer_email": "Camila@Example.COM",
            "service_id": sid,
            "start_at": start.isoformat(),
        },
    )
    assert r.status_code == 201, r.text
    assert r.json()["customer_email"] == "camila@example.com"
    assert sent["to"] == "camila@example.com"
    assert "Confirmación" in sent["subject"]
    assert "Corte" in sent["body"]


def test_reject_invalid_email():
    sid = client.get("/api/services").json()[0]["id"]
    start = _next_open_day_at(11)
    r = client.post(
        "/api/appointments",
        json={
            "customer_name": "Camila",
            "customer_phone": "942916570",
            "customer_email": "no-es-correo",
            "service_id": sid,
            "start_at": start.isoformat(),
        },
    )
    assert r.status_code == 422


def test_send_email_demo_mode():
    from app.notifications import send_email

    result = send_email("cliente@example.com", "Prueba", "Cuerpo")
    assert result["ok"] is True
    assert result["mode"] == "demo"



# ---------- Administración ----------
def test_admin_auth():
    assert client.get("/api/admin/appointments").status_code == 422  # falta cabecera
    assert client.get(
        "/api/admin/appointments", headers={"X-Admin-Token": "malo"}
    ).status_code == 401  # token incorrecto
    assert client.get(
        "/api/admin/appointments", headers={"X-Admin-Token": "test-token"}
    ).status_code == 200  # correcto


# ---------- Calendario ----------
def test_calendar_returns_daily_states():
    sid = client.get("/api/services").json()[0]["id"]
    day = _next_open_day_at(11).date()
    prev_day = day - timedelta(days=1)
    next_day = day + timedelta(days=1)

    r = client.get(
        "/api/calendar",
        params={
            "service_id": sid,
            "start_date": prev_day.isoformat(),
            "end_date": next_day.isoformat(),
        },
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert set(data) == {
        prev_day.isoformat(),
        day.isoformat(),
        next_day.isoformat(),
    }
    assert data[day.isoformat()] == "available"


def test_calendar_marks_closed_day():
    sid = client.get("/api/services").json()[0]["id"]
    day = local_now().date() + timedelta(days=1)
    while day.weekday() != 6:  # domingo
        day += timedelta(days=1)

    r = client.get(
        "/api/calendar",
        params={
            "service_id": sid,
            "start_date": day.isoformat(),
            "end_date": day.isoformat(),
        },
    )
    assert r.status_code == 200, r.text
    assert r.json()[day.isoformat()] == "closed"


def test_calendar_marks_day_without_slots_as_occupied():
    db = SessionLocal()
    service = models.Service(
        name="Jornada completa", duration_min=700, price=0, active=True
    )
    db.add(service)
    db.commit()
    db.refresh(service)
    service_id = service.id
    db.close()

    day = _next_open_day_at(11).date()
    r = client.get(
        "/api/calendar",
        params={
            "service_id": service_id,
            "start_date": day.isoformat(),
            "end_date": day.isoformat(),
        },
    )
    assert r.status_code == 200, r.text
    assert r.json()[day.isoformat()] == "occupied"


def test_calendar_rejects_unknown_service():
    r = client.get(
        "/api/calendar",
        params={
            "service_id": 99999,
            "start_date": "2026-11-11",
            "end_date": "2026-11-12",
        },
    )
    assert r.status_code == 404


def test_calendar_rejects_inverted_range():
    sid = client.get("/api/services").json()[0]["id"]
    r = client.get(
        "/api/calendar",
        params={
            "service_id": sid,
            "start_date": "2026-11-12",
            "end_date": "2026-11-11",
        },
    )
    assert r.status_code == 422


def test_calendar_rejects_ranges_over_limit():
    sid = client.get("/api/services").json()[0]["id"]
    start = local_now().date()
    end = start + timedelta(days=63)
    r = client.get(
        "/api/calendar",
        params={
            "service_id": sid,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
        },
    )
    assert r.status_code == 422


# ---------- Previsión de demanda ----------
def test_forecast_filters_by_service():
    headers = {"X-Admin-Token": "test-token"}
    service_1 = client.get("/api/services").json()[0]
    service_2 = client.post(
        "/api/admin/services",
        headers=headers,
        json={"name": "Barba", "duration_min": 30, "price": 5000},
    ).json()

    day = _next_open_day_at(11)
    common = {"customer_name": "Cliente", "customer_phone": "942916570"}
    r1 = client.post(
        "/api/appointments",
        json={
            **common,
            "service_id": service_1["id"],
            "start_at": day.isoformat(),
        },
    )
    assert r1.status_code == 201, r1.text
    r2 = client.post(
        "/api/appointments",
        json={
            **common,
            "service_id": service_2["id"],
            "start_at": day.replace(hour=12).isoformat(),
        },
    )
    assert r2.status_code == 201, r2.text

    params = {
        "start_date": day.date().isoformat(),
        "end_date": day.date().isoformat(),
    }
    all_data = client.get(
        "/api/admin/forecast", headers=headers, params=params
    ).json()
    only_service_1 = client.get(
        "/api/admin/forecast",
        headers=headers,
        params={**params, "service_id": service_1["id"]},
    ).json()
    only_service_2 = client.get(
        "/api/admin/forecast",
        headers=headers,
        params={**params, "service_id": service_2["id"]},
    ).json()

    assert all_data[0]["count"] == 2
    assert only_service_1[0]["count"] == 1
    assert only_service_2[0]["count"] == 1


# ---------- Métricas ----------
def test_admin_metrics_for_range():
    db = SessionLocal()
    service = db.query(models.Service).first()
    service_id, price = service.id, service.price
    now = local_now()
    start_at = now.replace(hour=10, minute=0, second=0, microsecond=0)
    db.add(
        models.Appointment(
            customer_name="Cliente Métricas",
            customer_phone="+56942916570",
            service_id=service_id,
            start_at=start_at,
            end_at=start_at + timedelta(minutes=service.duration_min),
            status=models.STATUS_PENDING,
            notes="",
        )
    )
    db.commit()
    db.close()

    today = now.date().isoformat()
    r = client.get(
        "/api/admin/metrics",
        headers={"X-Admin-Token": "test-token"},
        params={"start_date": today, "end_date": today},
    )
    assert r.status_code == 200, r.text
    assert r.json() == {
        "start_date": today,
        "end_date": today,
        "appointments": 1,
        "estimated_revenue": price,
        "today": 1,
        "week": 1,
    }


def test_admin_metrics_rejects_inverted_range():
    r = client.get(
        "/api/admin/metrics",
        headers={"X-Admin-Token": "test-token"},
        params={"start_date": "2026-11-12", "end_date": "2026-11-11"},
    )
    assert r.status_code == 422



