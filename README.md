MediBook patch package

What is included
- frontend/css/style.css
  Shared professional UI theme with one uniform color system.
- frontend/js/api.js
  Safer API service with configurable API base and helper functions.
- backend/app/main.py
  FastAPI backend matching the API paths used by your uploaded frontend.
- backend/app/database.py
  SQLAlchemy database setup.
- backend/app/models.py
  User, Doctor, Appointment models.
- backend/app/schemas.py
  Request and response schemas.
- backend/app/security.py
  Password hashing and JWT handling.
- backend/app/seed.py
  Seeds admin account and doctor data.
- backend/requirements.txt
  Python dependencies.

Run backend
1. cd backend
2. python -m venv venv
3. source venv/bin/activate   or on Windows: venv\Scripts\activate
4. pip install -r requirements.txt
5. uvicorn app.main:app --reload --port 8000

Demo admin login
- email: admin@medibook.com
- password: admin123

Notes
- This is a starter backend built from the API calls present in your uploaded MediBook frontend pages.
- I did not overwrite your uploaded HTML pages because only a subset of the project was available in the upload set.
- If you upload the full project zip, the next pass can patch your exact file tree instead of giving you a compatible scaffold.
