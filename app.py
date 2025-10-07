import os
import psycopg2
from flask import Flask, request
import requests
from datetime import datetime
from dotenv import load_dotenv, find_dotenv

# Load environment variables
load_dotenv(find_dotenv())
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
FROM_EMAIL = os.getenv("EMAIL_ADDRESS")
DATABASE_URL = os.getenv("DATABASE_URL")

print(f"Loaded sender: {FROM_EMAIL}")  # Debug check

app = Flask(__name__)

# Send confirmation to customer (only date and time)
def send_customer_confirmation(email, date, time):
    subject = "Your Appointment Confirmation"
    body = f"""Hi! Your appointment is confirmed for:\n\nDate: {date}\nTime: {time}\n\nThanks for booking with CollectibleTags!"""
    send_email(email, subject, body)

# Send full notification to business inbox
def send_business_notification(name, customer_email, date, time, notes):
    subject = f"New Appointment: {name}"
    body = f"""New appointment received:\n\nName: {name}\nEmail: {customer_email}\nDate: {date}\nTime: {time}\nNotes: {notes}\n\nThis appointment has been logged in the database."""
    send_email(FROM_EMAIL, subject, body)

# Core SendGrid email function
def send_email(to_address, subject, body):
    url = "https://api.sendgrid.com/v3/mail/send"
    headers = {
        "Authorization": f"Bearer {SENDGRID_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "personalizations": [
            {
                "to": [{"email": to_address}],
                "subject": subject
            }
        ],
        "from": {"email": FROM_EMAIL},
        "content": [
            {
                "type": "text/plain",
                "value": body
            }
        ]
    }
    response = requests.post(url, headers=headers, json=data)
    print(f"Email to {to_address}: {response.status_code}")

# Handle appointment form submission
@app.route('/submit', methods=['POST'])
def submit():
    first = request.form['first_name']
    last = request.form['last_name']
    name = f"{first} {last}"
    customer_email = request.form['email']
    date = request.form['date']
    time = request.form['time']
    notes = request.form.get('notes', '')
    timestamp = datetime.utcnow().isoformat()

    # Save to PostgreSQL
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    # Create table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id SERIAL PRIMARY KEY,
            name TEXT,
            email TEXT,
            date TEXT,
            time TEXT,
            notes TEXT,
            timestamp TEXT
        )
    ''')

    # Insert appointment
    cursor.execute('''
        INSERT INTO appointments (name, email, date, time, notes, timestamp)
        VALUES (%s, %s, %s, %s, %s, %s)
    ''', (name, customer_email, date, time, notes, timestamp))

    conn.commit()
    cursor.close()
    conn.close()

    # Send emails
    send_customer_confirmation(customer_email, date, time)
    send_business_notification(name, customer_email, date, time, notes)

    return 'Appointment submitted successfully! See you soon!'

# Start Flask app
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)




