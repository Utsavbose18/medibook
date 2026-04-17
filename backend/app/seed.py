from sqlalchemy.orm import Session
from .models import Doctor, User
from .security import hash_password


def seed_data(db: Session):
    if not db.query(User).filter(User.email == "admin@medibook.com").first():
        db.add(User(name="MediBook Admin", email="admin@medibook.com", phone="9999999999", password_hash=hash_password("admin123"), role="admin"))

    if db.query(Doctor).count() == 0:
        doctors = [
            ("Dr. Arjun Mehta", "Cardiologist", 12, 1200, "Heart specialist focused on preventive care and cardiac wellness."),
            ("Dr. Nisha Rao", "Dermatologist", 9, 900, "Skin, hair and cosmetic dermatology specialist."),
            ("Dr. Kabir Shah", "Neurologist", 14, 1500, "Neurology and chronic headache management expert."),
            ("Dr. Sana Iqbal", "Pediatrician", 8, 800, "Child health, vaccination and growth monitoring."),
            ("Dr. Vivek Menon", "General Physician", 11, 600, "Primary care physician for everyday health needs."),
            ("Dr. Rhea Kapoor", "Gynecologist", 10, 1100, "Women's health, routine consultation and wellness."),
        ]
        db.add_all([Doctor(name=n, specialization=s, experience=e, fee=f, bio=b, available=True) for n, s, e, f, b in doctors])

    db.commit()
