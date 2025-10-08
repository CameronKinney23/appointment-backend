from flask import Flask, request, jsonify
import os
import psycopg2
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

# --- DB URL (Render Postgres) ---
DB_URL = os.getenv("DATABASE_URL", "")
if DB_URL.startswith("postgres://"):
    DB_URL = DB_URL.replace("postgres://", "postgresql://", 1)

# --- Health route (fast and independent of DB) ---
@app.get("/")
def health():
    return "ok", 200

# --- Email: send to BOTH business + customer ---
def send_email(name, email, date, time, notes):
    SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
    FROM_EMAIL = os.getenv("FROM_EMAIL")                      # must be verified in SendGrid
    COMPANY_EMAIL = os.getenv("COMPANY_EMAIL", "camkin123@gmail.com")

    subject = "New Appointment Submission"
    body = (
        "A new appointment has been booked:\n\n"
        f"Name: {name}\nEmail: {email}\nDate: {date}\n"
        f"Time: {time}\nNotes: {notes}\n"
    )

    data = {
        "personalizations": [{
            "to": [{"email": COMPANY_EMAIL}, {"email": email}],
            "subject": subject
        }],
        "from": {"email": FROM_EMAIL},
        "reply_to": {"email": email},
        "content": [{"type": "text/plain", "value": body}]
    }

    r = requests.post(
        "https://api.sendgrid.com/v3/mail/send",
        headers={"Authorization": f"Bearer {SENDGRID_API_KEY}", "Content-Type": "application/json"},
        json=data
    )
    if r.status_code != 202:
        app.logger.error(f"SendGrid error {r.status_code}: {r.text}")
    return r.status_code

@app.post("/submit")
def submit_appointment():
    try:
        data = request.get_json(silent=True) or {}
        name = data.get("name")
        customer_email = data.get("email")
        date = data.get("date")
        time_ = data.get("time")
        notes = data.get("notes", "")

        # basic validation
        for k, v in {"name": name, "email": customer_email, "date": date, "time": time_}.items():
            if not v:
                return jsonify({"error": f"Missing field: {k}"}), 400

        # Lazy DB work: short timeout, create table if needed, then insert
        with psycopg2.connect(DB_URL, sslmode="require", connect_timeout=5) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS appointments (
                        id SERIAL PRIMARY KEY,
                        name TEXT NOT NULL,
                        email TEXT NOT NULL,
                        date TEXT NOT NULL,
                        time TEXT NOT NULL,
                        notes TEXT,
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    );
                """)
                cur.execute("""
                    INSERT INTO appointments (name, email, date, time, notes)
                    VALUES (%s, %s, %s, %s, %s)
                """, (name, customer_email, date, time_, notes))

        # email business + customer
        send_email(name, customer_email, date, time_, notes)

        return jsonify({"message": "Appointment submitted successfully! See you soon!"}), 200

    except Exception as e:
        app.logger.exception("Error submitting appointment")
        return jsonify({"error": "Internal server error"}), 500
