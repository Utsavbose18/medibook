import pytest
from app.models import Doctor

def test_list_doctors_empty(client):
    response = client.get("/api/doctors/")
    assert response.status_code == 200
    assert response.json() == []

def test_list_doctors(client, db_session):
    doctor1 = Doctor(name="Dr. Smith", specialization="Cardiology", fee=100.0)
    doctor2 = Doctor(name="Dr. Jones", specialization="Pediatrics", fee=80.0, available=False)
    db_session.add_all([doctor1, doctor2])
    db_session.commit()

    response = client.get("/api/doctors/")
    assert response.status_code == 200
    doctors = response.json()
    assert len(doctors) == 2
    # Ensure available doctor comes first (since ordered by available desc)
    assert doctors[0]["name"] == "Dr. Smith"
    assert doctors[1]["name"] == "Dr. Jones"

def test_get_slots_invalid_doctor(client):
    response = client.get("/api/appointments/slots/999?date=2024-01-01")
    assert response.status_code == 404

def test_get_slots_unavailable_doctor(client, db_session):
    doctor = Doctor(name="Dr. Unavailable", specialization="GP", fee=50.0, available=False)
    db_session.add(doctor)
    db_session.commit()

    response = client.get(f"/api/appointments/slots/{doctor.id}?date=2024-01-01")
    assert response.status_code == 404

def test_get_slots_all_available(client, db_session):
    doctor = Doctor(name="Dr. Available", specialization="GP", fee=50.0)
    db_session.add(doctor)
    db_session.commit()

    response = client.get(f"/api/appointments/slots/{doctor.id}?date=2024-01-01")
    assert response.status_code == 200
    slots = response.json()["slots"]
    assert len(slots) == 6
    assert "09:00 AM" in slots
