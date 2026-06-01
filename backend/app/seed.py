from .models import Doctor, User
from .security import hash_password

async def seed_data():
    admin = await User.find_one(User.email == "admin@medibook.com")
    if not admin:
        new_admin = User(
            name="MediBook Admin",
            email="admin@medibook.com",
            phone="9999999999",
            password_hash=hash_password("admin123"),
            role="admin"
        )
        await new_admin.insert()

    doctor_count = await Doctor.find_all().count()
    if doctor_count == 0:
        doctors = [
            ("Dr. Arjun Mehta", "Cardiologist", 12, 1200.0, "Heart specialist focused on preventive care and cardiac wellness."),
            ("Dr. Nisha Rao", "Dermatologist", 9, 900.0, "Skin, hair and cosmetic dermatology specialist."),
            ("Dr. Kabir Shah", "Neurologist", 14, 1500.0, "Neurology and chronic headache management expert."),
            ("Dr. Sana Iqbal", "Pediatrician", 8, 800.0, "Child health, vaccination and growth monitoring."),
            ("Dr. Vivek Menon", "General Physician", 11, 600.0, "Primary care physician for everyday health needs."),
            ("Dr. Rhea Kapoor", "Gynecologist", 10, 1100.0, "Women's health, routine consultation and wellness."),
        ]

        doctor_docs = [
            Doctor(name=n, specialization=s, experience=e, fee=f, bio=b, available=True)
            for n, s, e, f, b in doctors
        ]
        await Doctor.insert_many(doctor_docs)
