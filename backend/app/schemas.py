from datetime import date
from pydantic import BaseModel, EmailStr


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    phone: str | None = None
    role: str

    class Config:
        from_attributes = True


class AuthRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: str | None = None


class AuthLogin(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    token: str
    user: UserOut


class DoctorOut(BaseModel):
    id: int
    name: str
    specialization: str
    experience: int
    fee: float
    bio: str | None = None
    available: bool

    class Config:
        from_attributes = True


class AppointmentCreate(BaseModel):
    doctor_id: int
    date: date
    time_slot: str
    reason: str | None = None


class AppointmentAdminUpdate(BaseModel):
    status: str


class AppointmentOut(BaseModel):
    id: int
    doctor_id: int
    doctor_name: str
    specialization: str
    fee: float
    date: date
    time_slot: str
    reason: str | None = None
    status: str


class AppointmentAdminOut(BaseModel):
    id: int
    patient_name: str
    patient_email: str
    doctor_name: str
    specialization: str
    fee: float
    date: date
    time_slot: str
    reason: str | None = None
    status: str


class StatsOut(BaseModel):
    patients: int
    doctors: int
    total_appointments: int
    pending_appointments: int
