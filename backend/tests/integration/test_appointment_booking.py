import pytest
from app.models import Doctor, Appointment
from beanie import PydanticObjectId

@pytest.mark.asyncio
async def test_create_appointment_unauthorized(client):
    fake_id = str(PydanticObjectId())
    response = await client.post(
        "/api/appointments/",
        json={"doctor_id": fake_id, "date": "2024-01-01", "time_slot": "09:00 AM"}
    )
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_create_appointment_invalid_token(client):
    fake_id = str(PydanticObjectId())
    response = await client.post(
        "/api/appointments/",
        json={"doctor_id": fake_id, "date": "2024-01-01", "time_slot": "09:00 AM"},
        headers={"Authorization": "Bearer invalidtoken"}
    )
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_create_appointment_invalid_doctor(client, test_user):
    token = test_user["token"]
    fake_id = str(PydanticObjectId())
    response = await client.post(
        "/api/appointments/",
        json={"doctor_id": fake_id, "date": "2024-01-01", "time_slot": "09:00 AM"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_create_appointment_success(client, test_user):
    token = test_user["token"]
    doctor = Doctor(name="Dr. Appt", specialization="GP", fee=50.0)
    await doctor.insert()

    response = await client.post(
        "/api/appointments/",
        json={"doctor_id": str(doctor.id), "date": "2024-01-01", "time_slot": "09:00 AM"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert "id" in response.json()
    assert response.json()["message"] == "Appointment booked successfully"

@pytest.mark.asyncio
async def test_create_appointment_slot_taken(client, test_user):
    token = test_user["token"]
    doctor = Doctor(name="Dr. Taken", specialization="GP", fee=50.0)
    await doctor.insert()

    # Book first time
    first_res = await client.post(
        "/api/appointments/",
        json={"doctor_id": str(doctor.id), "date": "2024-01-01", "time_slot": "10:00 AM"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert first_res.status_code == 200

    # Book again
    response = await client.post(
        "/api/appointments/",
        json={"doctor_id": str(doctor.id), "date": "2024-01-01", "time_slot": "10:00 AM"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Selected slot is no longer available"

@pytest.mark.asyncio
async def test_get_my_appointments(client, test_user):
    token = test_user["token"]
    doctor = Doctor(name="Dr. My Appt", specialization="GP", fee=50.0)
    await doctor.insert()

    await client.post(
        "/api/appointments/",
        json={"doctor_id": str(doctor.id), "date": "2024-01-01", "time_slot": "11:30 AM"},
        headers={"Authorization": f"Bearer {token}"}
    )

    response = await client.get("/api/appointments/my", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    appts = response.json()
    assert len(appts) >= 1
    assert appts[0]["doctor_name"] == "Dr. My Appt"
    assert appts[0]["status"] == "pending"

@pytest.mark.asyncio
async def test_cancel_appointment(client, test_user):
    token = test_user["token"]
    doctor = Doctor(name="Dr. Cancel", specialization="GP", fee=50.0)
    await doctor.insert()

    book_res = await client.post(
        "/api/appointments/",
        json={"doctor_id": str(doctor.id), "date": "2024-01-01", "time_slot": "01:00 PM"},
        headers={"Authorization": f"Bearer {token}"}
    )
    appt_id = book_res.json()["id"]

    cancel_res = await client.delete(
        f"/api/appointments/{appt_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert cancel_res.status_code == 200

    my_appts = (await client.get("/api/appointments/my", headers={"Authorization": f"Bearer {token}"})).json()
    cancelled_appt = next((a for a in my_appts if a["id"] == appt_id), None)
    assert cancelled_appt is not None
    assert cancelled_appt["status"] == "cancelled"

@pytest.mark.asyncio
async def test_cancel_appointment_invalid(client, test_user):
    token = test_user["token"]
    fake_id = str(PydanticObjectId())
    response = await client.delete(f"/api/appointments/{fake_id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404
