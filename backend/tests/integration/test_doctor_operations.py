import pytest
from app.models import Doctor
from beanie import PydanticObjectId

@pytest.mark.asyncio
async def test_list_doctors_empty(client):
    response = await client.get("/api/doctors/")
    assert response.status_code == 200
    assert response.json() == []

@pytest.mark.asyncio
async def test_list_doctors(client):
    doctor1 = Doctor(name="Dr. Smith", specialization="Cardiology", fee=100.0)
    doctor2 = Doctor(name="Dr. Jones", specialization="Pediatrics", fee=80.0, available=False)
    await Doctor.insert_many([doctor1, doctor2])

    response = await client.get("/api/doctors/")
    assert response.status_code == 200
    doctors = response.json()
    assert len(doctors) == 2
    # Ensure available doctor comes first (since ordered by available desc)
    assert doctors[0]["name"] == "Dr. Smith"
    assert doctors[1]["name"] == "Dr. Jones"

@pytest.mark.asyncio
async def test_get_slots_invalid_doctor(client):
    fake_id = str(PydanticObjectId())
    response = await client.get(f"/api/appointments/slots/{fake_id}?date=2024-01-01")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_get_slots_unavailable_doctor(client):
    doctor = Doctor(name="Dr. Unavailable", specialization="GP", fee=50.0, available=False)
    await doctor.insert()

    response = await client.get(f"/api/appointments/slots/{doctor.id}?date=2024-01-01")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_get_slots_all_available(client):
    doctor = Doctor(name="Dr. Available", specialization="GP", fee=50.0)
    await doctor.insert()

    response = await client.get(f"/api/appointments/slots/{doctor.id}?date=2024-01-01")
    assert response.status_code == 200
    slots = response.json()["slots"]
    assert len(slots) == 6
    assert "09:00 AM" in slots
