import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import Base, engine


@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ac01_solicitud_valida_y_calculo_saldo():
    # Crear ADMIN_RRHH (primer empleado, tabla vacía, sin header)
    admin_payload = {
        "nombre": "Admin",
        "email": "admin@talentcore.com",
        "rol": "ADMIN_RRHH",
        "anios_antiguedad": 5
    }
    response = client.post("/api/v1/empleados", json=admin_payload)
    assert response.status_code == 201
    admin_id = response.json()["id"]
    assert admin_id == 1

    # Crear MANAGER (id=2)
    manager_payload = {
        "nombre": "Manager",
        "email": "manager@talentcore.com",
        "rol": "MANAGER",
        "anios_antiguedad": 3
    }
    response = client.post(
        "/api/v1/empleados",
        json=manager_payload,
        headers={"X-User-Id": "1"}
    )
    assert response.status_code == 201
    manager_id = response.json()["id"]
    assert manager_id == 2

    # Crear EMPLEADO (id=3, anios_antiguedad=3, manager_id=2)
    empleado_payload = {
        "nombre": "Empleado",
        "email": "empleado@talentcore.com",
        "rol": "EMPLEADO",
        "anios_antiguedad": 3,
        "manager_id": 2
    }
    response = client.post(
        "/api/v1/empleados",
        json=empleado_payload,
        headers={"X-User-Id": "1"}
    )
    assert response.status_code == 201
    empleado_id = response.json()["id"]
    assert empleado_id == 3

    # Verificar saldo inicial: dias_totales = min(12 + 2*(3-1), 20) = 16
    response = client.get(f"/api/v1/vacaciones/saldo/{empleado_id}")
    assert response.status_code == 200
    saldo_data = response.json()
    assert saldo_data["dias_totales"] == 16
    assert saldo_data["saldo_disponible"] == 16

    # Solicitar 5 días
    solicitud_payload = {
        "empleado_id": empleado_id,
        "dias_solicitados": 5,
        "motivo": "Vacaciones"
    }
    response = client.post(
        "/api/v1/vacaciones/solicitar",
        json=solicitud_payload,
        headers={"X-User-Id": "3"},
    )
    assert response.status_code == 201
    solicitud_data = response.json()
    assert solicitud_data["estado"] == "PENDING"
    solicitud_id = solicitud_data["id"]
    assert solicitud_id == 1

    # Manager aprueba la solicitud
    revision_payload = {"accion": "APPROVE"}
    response = client.post(
        f"/api/v1/vacaciones/{solicitud_id}/revisar",
        json=revision_payload,
        headers={"X-User-Id": "2"}
    )
    assert response.status_code == 200
    revision_data = response.json()
    assert revision_data["estado"] == "APPROVED"

    # Verificar nuevo saldo disponible: 16 - 5 = 11
    response = client.get(f"/api/v1/vacaciones/saldo/{empleado_id}")
    assert response.status_code == 200
    saldo_data = response.json()
    assert saldo_data["saldo_disponible"] == 11


def test_ac02_saldo_insuficiente():
    # Crear ADMIN_RRHH (id=1)
    admin_payload = {
        "nombre": "Admin",
        "email": "admin@talentcore.com",
        "rol": "ADMIN_RRHH",
        "anios_antiguedad": 5
    }
    response = client.post("/api/v1/empleados", json=admin_payload)
    assert response.status_code == 201

    # Crear EMPLEADO (id=2, anios_antiguedad=1 -> 12 días)
    empleado_payload = {
        "nombre": "Empleado",
        "email": "empleado@talentcore.com",
        "rol": "EMPLEADO",
        "anios_antiguedad": 1
    }
    response = client.post(
        "/api/v1/empleados",
        json=empleado_payload,
        headers={"X-User-Id": "1"}
    )
    assert response.status_code == 201
    empleado_id = response.json()["id"]
    assert empleado_id == 2

    # Intentar solicitar 15 días (excede el saldo de 12)
    solicitud_payload = {
        "empleado_id": empleado_id,
        "dias_solicitados": 15,
        "motivo": "Vacaciones largas"
    }
    response = client.post(
    "/api/v1/vacaciones/solicitar",
    json=solicitud_payload,
    headers={"X-User-Id": str(empleado_id)}
)
    assert response.status_code == 400
    assert response.json()["detail"] == "Insufficient vacation balance"


def test_ac03_manager_no_autorizado():
    # Crear ADMIN_RRHH (id=1)
    admin_payload = {
        "nombre": "Admin",
        "email": "admin@talentcore.com",
        "rol": "ADMIN_RRHH",
        "anios_antiguedad": 5
    }
    response = client.post("/api/v1/empleados", json=admin_payload)
    assert response.status_code == 201

    # Crear MANAGER A (id=2)
    manager_a_payload = {
        "nombre": "Manager A",
        "email": "manager_a@talentcore.com",
        "rol": "MANAGER",
        "anios_antiguedad": 3
    }
    response = client.post(
        "/api/v1/empleados",
        json=manager_a_payload,
        headers={"X-User-Id": "1"}
    )
    assert response.status_code == 201
    manager_a_id = response.json()["id"]
    assert manager_a_id == 2

    # Crear MANAGER B (id=3)
    manager_b_payload = {
        "nombre": "Manager B",
        "email": "manager_b@talentcore.com",
        "rol": "MANAGER",
        "anios_antiguedad": 3
    }
    response = client.post(
        "/api/v1/empleados",
        json=manager_b_payload,
        headers={"X-User-Id": "1"}
    )
    assert response.status_code == 201
    manager_b_id = response.json()["id"]
    assert manager_b_id == 3

    # Crear EMPLEADO (id=4, manager_id=2)
    empleado_payload = {
        "nombre": "Empleado",
        "email": "empleado@talentcore.com",
        "rol": "EMPLEADO",
        "anios_antiguedad": 2,
        "manager_id": 2
    }
    response = client.post(
        "/api/v1/empleados",
        json=empleado_payload,
        headers={"X-User-Id": "1"}
    )
    assert response.status_code == 201
    empleado_id = response.json()["id"]
    assert empleado_id == 4

    # Empleado 4 solicita 3 días
    solicitud_payload = {
        "empleado_id": empleado_id,
        "dias_solicitados": 3,
        "motivo": "Vacaciones"
    }
    response = client.post(
        "/api/v1/vacaciones/solicitar",
        json=solicitud_payload,
        headers={"X-User-Id": str(empleado_id)}
    )
    assert response.status_code == 201
    solicitud_id = response.json()["id"]
    assert solicitud_id == 1

    # MANAGER B (id=3) intenta aprobar, pero NO es su jefe directo
    revision_payload = {"accion": "APPROVE"}
    response = client.post(
        f"/api/v1/vacaciones/{solicitud_id}/revisar",
        json=revision_payload,
        headers={"X-User-Id": "3"}
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Unauthorized: Not the direct manager"
