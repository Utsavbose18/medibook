import pytest
from app.models import Doctor, Appointment
from beanie import PydanticObjectId

@pytest.mark.asyncio
async def test_admin_stats_unauthorized(client):
    response = await client.get("/api/admin/stats")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_admin_stats_forbidden(client, test_user):
    token = test_user["token"]
    response = await client.get("/api/admin/stats", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_admin_stats_success(client, admin_user):
    token = admin_user["token"]
    response = await client.get("/api/admin/stats", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    stats = response.json()
    assert "patients" in stats
    assert "doctors" in stats
    assert "total_appointments" in stats
    assert "pending_appointments" in stats

@pytest.mark.asyncio
async def test_admin_get_doctors(client, admin_user):
    token = admin_user["token"]
    doctor = Doctor(name="Dr. Admin View", specialization="GP", fee=50.0)
    await doctor.insert()

    response = await client.get("/api/admin/doctors", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    doctors = response.json()
    assert len(doctors) >= 1
    assert any(d["name"] == "Dr. Admin View" for d in doctors)

@pytest.mark.asyncio
async def test_admin_toggle_doctor(client, admin_user):
    token = admin_user["token"]
    doctor = Doctor(name="Dr. Toggle", specialization="GP", fee=50.0, available=True)
    await doctor.insert()

    response = await client.put(f"/api/admin/doctors/{doctor.id}/toggle", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["available"] is False

@pytest.mark.asyncio
async def test_admin_toggle_doctor_not_found(client, admin_user):
    token = admin_user["token"]
    fake_id = str(PydanticObjectId())
    response = await client.put(f"/api/admin/doctors/{fake_id}/toggle", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_admin_get_patients(client, admin_user, test_user):
    token = admin_user["token"]
    response = await client.get("/api/admin/patients", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    patients = response.json()
    assert len(patients) >= 1

@pytest.mark.asyncio
async def test_admin_appointments(client, admin_user, test_user):
    token = admin_user["token"]
    doctor = Doctor(name="Dr. Admin Appts", specialization="GP", fee=50.0)
    await doctor.insert()

    # User creates appointment
    await client.post(
        "/api/appointments/",
        json={"doctor_id": str(doctor.id), "date": "2024-01-01", "time_slot": "09:00 AM"},
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )

    response = await client.get("/api/admin/appointments", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    appts = response.json()
    assert len(appts) >= 1
    assert any(a["doctor_name"] == "Dr. Admin Appts" for a in appts)

@pytest.mark.asyncio
async def test_admin_update_appointment(client, admin_user, test_user):
    token = admin_user["token"]
    doctor = Doctor(name="Dr. Admin Update", specialization="GP", fee=50.0)
    await doctor.insert()

    # User creates appointment
    book_res = await client.post(
        "/api/appointments/",
        json={"doctor_id": str(doctor.id), "date": "2024-01-01", "time_slot": "10:00 AM"},
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    appt_id = book_res.json()["id"]

    # Admin updates appointment status to confirmed
    update_res = await client.put(
        f"/api/admin/appointments/{appt_id}",
        json={"status": "confirmed"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert update_res.status_code == 200

    # Verify status changed
    appts = (await client.get("/api/admin/appointments", headers={"Authorization": f"Bearer {token}"})).json()
    updated_appt = next(a for a in appts if a["id"] == appt_id)
    assert updated_appt["status"] == "confirmed"

@pytest.mark.asyncio
async def test_admin_update_appointment_invalid(client, admin_user):
    token = admin_user["token"]
    fake_id = str(PydanticObjectId())
    response = await client.put(
        f"/api/admin/appointments/{fake_id}",
        json={"status": "confirmed"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404
