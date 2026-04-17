from datetime import date as dt_date
from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from .database import Base, engine, get_db
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

app = FastAPI(title="MediBook API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)
with next(get_db()) as seed_db:
    seed_data(seed_db)


def get_current_user(authorization: str | None = Header(default=None), db: Session = Depends(get_db)) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_token(token)
        user_id = int(payload["sub"])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


@app.get("/api/health")
def health():
    return {"ok": True}


@app.post("/api/auth/register", response_model=AuthResponse)
def register(payload: AuthRegister, db: Session = Depends(get_db)):
    existing = db.query(User).filter(func.lower(User.email) == payload.email.lower()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        name=payload.name,
        email=payload.email.lower(),
        phone=payload.phone,
        password_hash=hash_password(payload.password),
        role="patient",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(user.id, user.role)
    return {"token": token, "user": UserOut.model_validate(user)}


@app.post("/api/auth/login", response_model=AuthResponse)
def login(payload: AuthLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(func.lower(User.email) == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token(user.id, user.role)
    return {"token": token, "user": UserOut.model_validate(user)}


@app.get("/api/doctors/", response_model=list[DoctorOut])
def list_doctors(db: Session = Depends(get_db)):
    return db.query(Doctor).order_by(Doctor.available.desc(), Doctor.name.asc()).all()


@app.get("/api/appointments/slots/{doctor_id}")
def get_slots(doctor_id: int, date: dt_date = Query(...), db: Session = Depends(get_db)):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id, Doctor.available == True).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    master_slots = ["09:00 AM", "10:00 AM", "11:30 AM", "01:00 PM", "03:00 PM", "05:00 PM"]
    booked = {
        a.time_slot for a in db.query(Appointment).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.date == date,
            Appointment.status != "cancelled",
        ).all()
    }
    return {"slots": [slot for slot in master_slots if slot not in booked]}


@app.post("/api/appointments/")
def create_appointment(payload: AppointmentCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    doctor = db.query(Doctor).filter(Doctor.id == payload.doctor_id, Doctor.available == True).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    exists = db.query(Appointment).filter(
        Appointment.doctor_id == payload.doctor_id,
        Appointment.date == payload.date,
        Appointment.time_slot == payload.time_slot,
        Appointment.status != "cancelled",
    ).first()
    if exists:
        raise HTTPException(status_code=400, detail="Selected slot is no longer available")
    appt = Appointment(
        patient_id=user.id,
        doctor_id=payload.doctor_id,
        date=payload.date,
        time_slot=payload.time_slot,
        reason=payload.reason,
        status="pending",
    )
    db.add(appt)
    db.commit()
    db.refresh(appt)
    return {"message": "Appointment booked successfully", "id": appt.id}


@app.get("/api/appointments/my", response_model=list[AppointmentOut])
def my_appointments(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    appointments = db.query(Appointment).join(Doctor).filter(Appointment.patient_id == user.id).order_by(Appointment.date.desc()).all()
    return [
        AppointmentOut(
            id=a.id,
            doctor_id=a.doctor_id,
            doctor_name=a.doctor.name,
            specialization=a.doctor.specialization,
            fee=a.doctor.fee,
            date=a.date,
            time_slot=a.time_slot,
            reason=a.reason,
            status=a.status,
        ) for a in appointments
    ]


@app.delete("/api/appointments/{appointment_id}")
def cancel_my_appointment(appointment_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    appt = db.query(Appointment).filter(Appointment.id == appointment_id, Appointment.patient_id == user.id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    appt.status = "cancelled"
    db.commit()
    return {"message": "Appointment cancelled"}


@app.get("/api/admin/stats", response_model=StatsOut)
def admin_stats(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    return {
        "patients": db.query(User).filter(User.role == "patient").count(),
        "doctors": db.query(Doctor).count(),
        "total_appointments": db.query(Appointment).count(),
        "pending_appointments": db.query(Appointment).filter(Appointment.status == "pending").count(),
    }


@app.get("/api/admin/appointments", response_model=list[AppointmentAdminOut])
def admin_appointments(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    rows = db.query(Appointment).join(User, Appointment.patient_id == User.id).join(Doctor, Appointment.doctor_id == Doctor.id).order_by(Appointment.date.desc()).all()
    return [
        AppointmentAdminOut(
            id=a.id,
            patient_name=a.patient.name,
            patient_email=a.patient.email,
            doctor_name=a.doctor.name,
            specialization=a.doctor.specialization,
            fee=a.doctor.fee,
            date=a.date,
            time_slot=a.time_slot,
            reason=a.reason,
            status=a.status,
        ) for a in rows
    ]


@app.put("/api/admin/appointments/{appointment_id}")
def admin_update_appointment(appointment_id: int, payload: AppointmentAdminUpdate, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    appt.status = payload.status.lower()
    db.commit()
    return {"message": "Appointment updated"}


@app.get("/api/admin/doctors")
def admin_doctors(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    return db.query(Doctor).order_by(Doctor.name.asc()).all()


@app.put("/api/admin/doctors/{doctor_id}/toggle")
def admin_toggle_doctor(doctor_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    doctor.available = not doctor.available
    db.commit()
    return {"message": "Doctor updated", "available": doctor.available}


@app.get("/api/admin/patients")
def admin_patients(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    patients = db.query(User).filter(User.role == "patient").order_by(User.created_at.desc()).all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "email": p.email,
            "phone": p.phone,
            "created_at": p.created_at.date().isoformat(),
        }
        for p in patients
    ]
