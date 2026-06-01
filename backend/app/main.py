import contextlib
from datetime import date as dt_date
from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from beanie import PydanticObjectId

from .database import init_db
from .models import Appointment, Doctor, User
from .schemas import (
    AppointmentAdminOut,
    AppointmentAdminUpdate,
    AppointmentCreate,
    AppointmentOut,
    AuthLogin,
    AuthRegister,
    AuthResponse,
    DoctorOut,
    StatsOut,
    UserOut,
)
from .security import create_access_token, decode_token, hash_password, verify_password
from .seed import seed_data


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup Beanie & MongoDB connection
    await init_db()
    # Seed data
    await seed_data()
    yield

app = FastAPI(title="MediBook API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def get_current_user(authorization: str | None = Header(default=None)) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_token(token)
        user_id = payload["sub"]
        obj_id = PydanticObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = await User.get(obj_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


async def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


@app.get("/api/health")
async def health():
    return {"ok": True}


@app.post("/api/auth/register", response_model=AuthResponse)
async def register(payload: AuthRegister):
    import re
    safe_email = re.escape(payload.email)
    existing = await User.find_one({"email": {"$regex": f"^{safe_email}$", "$options": "i"}})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        name=payload.name,
        email=payload.email.lower(),
        phone=payload.phone,
        password_hash=hash_password(payload.password),
        role="patient",
    )
    await user.insert()
    token = create_access_token(str(user.id), user.role)
    return {"token": token, "user": UserOut.model_validate(user)}


@app.post("/api/auth/login", response_model=AuthResponse)
async def login(payload: AuthLogin):
    import re
    safe_email = re.escape(payload.email)
    user = await User.find_one({"email": {"$regex": f"^{safe_email}$", "$options": "i"}})
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token(str(user.id), user.role)
    return {"token": token, "user": UserOut.model_validate(user)}


@app.get("/api/doctors/", response_model=list[DoctorOut])
async def list_doctors():
    doctors = await Doctor.find().sort("-available", "name").to_list()
    return doctors


@app.get("/api/appointments/slots/{doctor_id}")
async def get_slots(doctor_id: PydanticObjectId, date: dt_date = Query(...)):
    doctor = await Doctor.find_one(Doctor.id == doctor_id, Doctor.available == True)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    master_slots = ["09:00 AM", "10:00 AM", "11:30 AM", "01:00 PM", "03:00 PM", "05:00 PM"]
    date_datetime = dt_date(date.year, date.month, date.day)
    appointments = await Appointment.find(
        Appointment.doctor_id == doctor_id,
        Appointment.date == date_datetime,
        Appointment.status != "cancelled"
    ).to_list()

    booked = {a.time_slot for a in appointments}
    return {"slots": [slot for slot in master_slots if slot not in booked]}


@app.post("/api/appointments/")
async def create_appointment(payload: AppointmentCreate, user: User = Depends(get_current_user)):
    doctor = await Doctor.find_one(Doctor.id == payload.doctor_id, Doctor.available == True)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    date_datetime = dt_date(payload.date.year, payload.date.month, payload.date.day)

    exists = await Appointment.find_one(
        Appointment.doctor_id == payload.doctor_id,
        Appointment.date == date_datetime,
        Appointment.time_slot == payload.time_slot,
        Appointment.status != "cancelled"
    )

    if exists:
        raise HTTPException(status_code=400, detail="Selected slot is no longer available")

    appt = Appointment(
        patient_id=user.id,
        doctor_id=doctor.id,
        date=date_datetime,
        time_slot=payload.time_slot,
        reason=payload.reason,
        status="pending",
    )
    await appt.insert()
    return {"message": "Appointment booked successfully", "id": str(appt.id)}


@app.get("/api/appointments/my", response_model=list[AppointmentOut])
async def my_appointments(user: User = Depends(get_current_user)):
    appointments = await Appointment.find(Appointment.patient_id == user.id).sort("-date").to_list()

    doctor_ids = list({a.doctor_id for a in appointments})
    doctors = await Doctor.find({"_id": {"$in": doctor_ids}}).to_list()
    doctor_map = {d.id: d for d in doctors}

    return [
        AppointmentOut(
            id=a.id,
            doctor_id=a.doctor_id,
            doctor_name=doctor_map[a.doctor_id].name,
            specialization=doctor_map[a.doctor_id].specialization,
            fee=doctor_map[a.doctor_id].fee,
            date=a.date,
            time_slot=a.time_slot,
            reason=a.reason,
            status=a.status,
        ) for a in appointments if a.doctor_id in doctor_map
    ]


@app.delete("/api/appointments/{appointment_id}")
async def cancel_my_appointment(appointment_id: PydanticObjectId, user: User = Depends(get_current_user)):
    appt = await Appointment.get(appointment_id)
    if not appt or appt.patient_id != user.id:
        raise HTTPException(status_code=404, detail="Appointment not found")
    appt.status = "cancelled"
    await appt.save()
    return {"message": "Appointment cancelled"}


@app.get("/api/admin/stats", response_model=StatsOut)
async def admin_stats(admin: User = Depends(require_admin)):
    return {
        "patients": await User.find(User.role == "patient").count(),
        "doctors": await Doctor.find_all().count(),
        "total_appointments": await Appointment.find_all().count(),
        "pending_appointments": await Appointment.find(Appointment.status == "pending").count(),
    }


@app.get("/api/admin/appointments", response_model=list[AppointmentAdminOut])
async def admin_appointments(admin: User = Depends(require_admin)):
    appointments = await Appointment.find_all().sort("-date").to_list()

    patient_ids = list({a.patient_id for a in appointments})
    doctor_ids = list({a.doctor_id for a in appointments})

    patients = await User.find({"_id": {"$in": patient_ids}}).to_list()
    doctors = await Doctor.find({"_id": {"$in": doctor_ids}}).to_list()

    patient_map = {p.id: p for p in patients}
    doctor_map = {d.id: d for d in doctors}

    return [
        AppointmentAdminOut(
            id=a.id,
            patient_name=patient_map[a.patient_id].name,
            patient_email=patient_map[a.patient_id].email,
            doctor_name=doctor_map[a.doctor_id].name,
            specialization=doctor_map[a.doctor_id].specialization,
            fee=doctor_map[a.doctor_id].fee,
            date=a.date,
            time_slot=a.time_slot,
            reason=a.reason,
            status=a.status,
        ) for a in appointments if a.patient_id in patient_map and a.doctor_id in doctor_map
    ]


@app.put("/api/admin/appointments/{appointment_id}")
async def admin_update_appointment(appointment_id: PydanticObjectId, payload: AppointmentAdminUpdate, admin: User = Depends(require_admin)):
    appt = await Appointment.get(appointment_id)
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    appt.status = payload.status.lower()
    await appt.save()
    return {"message": "Appointment updated"}


@app.get("/api/admin/doctors")
async def admin_doctors(admin: User = Depends(require_admin)):
    return await Doctor.find_all().sort("name").to_list()


@app.put("/api/admin/doctors/{doctor_id}/toggle")
async def admin_toggle_doctor(doctor_id: PydanticObjectId, admin: User = Depends(require_admin)):
    doctor = await Doctor.get(doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    doctor.available = not doctor.available
    await doctor.save()
    return {"message": "Doctor updated", "available": doctor.available}


@app.get("/api/admin/patients")
async def admin_patients(admin: User = Depends(require_admin)):
    patients = await User.find(User.role == "patient").sort("-created_at").to_list()
    return [
        {
            "id": str(p.id),
            "name": p.name,
            "email": p.email,
            "phone": p.phone,
            "created_at": p.created_at.date().isoformat(),
        }
        for p in patients
    ]
