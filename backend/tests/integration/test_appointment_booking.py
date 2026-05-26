import pytest
from app.models import Doctor, Appointment

def test_create_appointment_unauthorized(client):
    response = client.post(
        "/api/appointments/",
        json={"doctor_id": 1, "date": "2024-01-01", "time_slot": "09:00 AM"}
    )
    assert response.status_code == 401

def test_create_appointment_invalid_token(client):
    response = client.post(
        "/api/appointments/",
        json={"doctor_id": 1, "date": "2024-01-01", "time_slot": "09:00 AM"},
        headers={"Authorization": "Bearer invalidtoken"}
    )
    assert response.status_code == 401

def test_create_appointment_invalid_doctor(client, test_user):
    token = test_user["token"]
    response = client.post(
        "/api/appointments/",
        json={"doctor_id": 999, "date": "2024-01-01", "time_slot": "09:00 AM"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404

def test_create_appointment_success(client, test_user, db_session):
    token = test_user["token"]
    doctor = Doctor(name="Dr. Appt", specialization="GP", fee=50.0)
    db_session.add(doctor)
    db_session.commit()

    response = client.post(
        "/api/appointments/",
        json={"doctor_id": doctor.id, "date": "2024-01-01", "time_slot": "09:00 AM"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert "id" in response.json()
    assert response.json()["message"] == "Appointment booked successfully"

def test_create_appointment_slot_taken(client, test_user, db_session):
    token = test_user["token"]
    doctor = Doctor(name="Dr. Taken", specialization="GP", fee=50.0)
    db_session.add(doctor)
    db_session.commit()

    # Book first time
    client.post(
        "/api/appointments/",
        json={"doctor_id": doctor.id, "date": "2024-01-01", "time_slot": "10:00 AM"},
        headers={"Authorization": f"Bearer {token}"}
    )

    # Book again
    response = client.post(
        "/api/appointments/",
        json={"doctor_id": doctor.id, "date": "2024-01-01", "time_slot": "10:00 AM"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Selected slot is no longer available"

def test_get_my_appointments(client, test_user, db_session):
    token = test_user["token"]
    doctor = Doctor(name="Dr. My Appt", specialization="GP", fee=50.0)
    db_session.add(doctor)
    db_session.commit()

    client.post(
        "/api/appointments/",
        json={"doctor_id": doctor.id, "date": "2024-01-01", "time_slot": "11:30 AM"},
        headers={"Authorization": f"Bearer {token}"}
    )

    response = client.get("/api/appointments/my", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    appts = response.json()
    assert len(appts) >= 1
    assert appts[0]["doctor_name"] == "Dr. My Appt"
    assert appts[0]["status"] == "pending"

def test_cancel_appointment(client, test_user, db_session):
    token = test_user["token"]
    doctor = Doctor(name="Dr. Cancel", specialization="GP", fee=50.0)
    db_session.add(doctor)
    db_session.commit()

    book_res = client.post(
        "/api/appointments/",
        json={"doctor_id": doctor.id, "date": "2024-01-01", "time_slot": "01:00 PM"},
        headers={"Authorization": f"Bearer {token}"}
    )
    appt_id = book_res.json()["id"]

    cancel_res = client.delete(
        f"/api/appointments/{appt_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert cancel_res.status_code == 200

    my_appts = client.get("/api/appointments/my", headers={"Authorization": f"Bearer {token}"}).json()
    cancelled_appt = next((a for a in my_appts if a["id"] == appt_id), None)
    assert cancelled_appt is not None
    assert cancelled_appt["status"] == "cancelled"

def test_cancel_appointment_invalid(client, test_user):
    token = test_user["token"]
    response = client.delete("/api/appointments/999", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404
