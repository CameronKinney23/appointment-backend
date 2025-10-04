import sqlite3
from flask import Flask, request
import smtplib
from email.message import EmailMessage

app = Flask(__name__)

# Email notification function
def send_email_notification(name, email, date, time, notes):
    msg = EmailMessage()
    msg['Subject'] = 'New Appointment Received'
    msg['From'] = 'camkin123@gmail.com'  # Replace with your Gmail address
    msg['To'] = 'ofwgkta666247@gmail.com'    # Replace with your Gmail address or recipient
    msg.set_content(f'''
    New appointment booked:

    Name: {name}
    Email: {email}
    Date: {date}
    Time: {time}
    Notes: {notes}
    ''')

    # Gmail SMTP configuration
    with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
        smtp.starttls()
        smtp.login('camkin123@gmail.com', 'kihmpojpzmuykcgj'  # Replace with your Gmail and app password
        smtp.send_message(msg)

# Submit route
@app.route('/submit', methods=['POST'])
def submit():
    name = request.form['name']
    email = request.form['email']
    date = request.form['date']
    time = request.form['time']
    notes = request.form.get('notes', '')

    conn = sqlite3.connect('appointments.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO appointments (name, email, date, time, notes) VALUES (?, ?, ?, ?, ?)',
                   (name, email, date, time, notes))
    conn.commit()
    conn.close()

    send_email_notification(name, email, date, time, notes)

    return 'Appointment submitted successfully! See you soon!'

if __name__ == '__main__':
    app.run(debug=True)

