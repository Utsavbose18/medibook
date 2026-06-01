from datetime import date
from pydantic import BaseModel, EmailStr
from beanie import PydanticObjectId

class UserOut(BaseModel):
    id: PydanticObjectId
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
    id: PydanticObjectId
    name: str
    specialization: str
    experience: int
    fee: float
    bio: str | None = None
    available: bool

    class Config:
        from_attributes = True


class AppointmentCreate(BaseModel):
    doctor_id: PydanticObjectId
    date: date
    time_slot: str
    reason: str | None = None


class AppointmentAdminUpdate(BaseModel):
    status: str


class AppointmentOut(BaseModel):
    id: PydanticObjectId
    doctor_id: PydanticObjectId
    doctor_name: str
    specialization: str
    fee: float
    date: date
    time_slot: str
    reason: str | None = None
    status: str

    class Config:
        from_attributes = True


class AppointmentAdminOut(BaseModel):
    id: PydanticObjectId
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
