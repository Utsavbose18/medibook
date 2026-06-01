from datetime import datetime, date as dt_date
from typing import Optional
from beanie import Document, Indexed, Link
from pydantic import Field

class User(Document):
    name: str
    email: Indexed(str, unique=True)
    phone: Optional[str] = None
    password_hash: str
    role: str = "patient"
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "users"


class Doctor(Document):
    name: str
    specialization: str
    experience: int = 1
    fee: float = 500.0
    bio: Optional[str] = None
    available: bool = True

    class Settings:
        name = "doctors"


from beanie import PydanticObjectId

class Appointment(Document):
    patient_id: PydanticObjectId
    doctor_id: PydanticObjectId
    date: dt_date
    time_slot: str
    reason: Optional[str] = None
    status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "appointments"
