from flask import Flask, request, jsonify
import os
import psycopg2
import requests
from datetime import datetime

app = Flask(__name__)

# Email notification to business only
def send_business_notification(name, email, date, time, notes):
    SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
    FROM_EMAIL = os.getenv("EMAIL_ADDRESS")
    TO_EMAIL = "camkin123@gmail.com"

    subject = "New Appointment Submission"
    body = f"""
    A new appointment has been booked:

    Name: {name}
    Email: {email}
    Date: {date}
    Time: {time}
    Notes: {notes}
    """

    data = {
        "personalizations": [{
            "to": [{"email": TO_EMAIL}],
            "subject": subject
        }],
        "from": {"email": FROM_EMAIL},
        "content": [{
            "type": "text/plain",
            "value": body
        }]
    }

    response = requests.post(
        "https://api.sendgrid.com/v3/mail/send",
        headers={
            "Authorization": f"Bearer {SENDGRID_API_KEY}",
            "Content-Type": "application/json"
        },
        json=data
    )

    print("SendGrid response:", response.status_code, response.text)
    return response.status_code

@app.route('/submit', methods=['POST'])
def submit_appointment():
    try:
        data = request.json
        name = data.get("name")
        customer_email = data.get("email")
        date = data.get("date")
        time = data.get("time")
        notes = data.get("notes")
        timestamp = datetime.utcnow().isoformat()

        # Connect to PostgreSQL
        conn = psycopg2.connect(
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            host=os.getenv("POSTGRES_HOST"),
            port=os.getenv("POSTGRES_PORT")
        )

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

        # Send email to business only
        send_business_notification(name, customer_email, date, time, notes)

        return 'Appointment submitted successfully! See you soon!'

    except Exception as e:
        print("Error submitting appointment:", str(e))
        return 'Internal server error', 500

# Start Flask app
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
