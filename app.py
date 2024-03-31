from flask import Flask, render_template, request, g
from collections import namedtuple
from datetime import datetime
import qrcode
from io import BytesIO
import base64
import sqlite3

app = Flask(__name__)

Doctor = namedtuple('Doctor', ['name', 'speciality', 'availability'])

doctors = [
    Doctor("Dr. Smith", "Cardiologist", "Monday, Wednesday, Friday"),
    Doctor("Dr. Johnson", "Dermatologist", "Tuesday, Thursday")
]

DATABASE = 'appointments.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        doctor_name = request.form['doctor']
        patient_name = request.form['patient']
        date = request.form['date']
        time = request.form['time']
        message, qr_code_data = book_appointment(doctor_name, patient_name, date, time)
        return render_template('index.html', doctors=doctors, message=message, qr_code_data=qr_code_data)
    return render_template('index.html', doctors=doctors)

def book_appointment(doctor_name, patient_name, date, time):
    doctor = next((doc for doc in doctors if doc.name == doctor_name), None)
    if doctor:
        appointment_date = datetime.strptime(date, "%Y-%m-%d").date()
        conn = get_db()
        c = conn.cursor()
        existing_appointments = c.execute('''SELECT * FROM appointments 
                                             WHERE doctor=? AND date=? AND time=?''', 
                                             (doctor_name, date, time)).fetchall()
        if existing_appointments:
            return "Appointment slot already booked. Available timings for this day.", None
        else:
            c.execute('''INSERT INTO appointments (doctor, patient, date, time) 
                         VALUES (?, ?, ?, ?)''', (doctor_name, patient_name, date, time))
            conn.commit()
            qr_code_data = generate_qr_code(patient_name, date, time)
            return "Appointment booked successfully!", qr_code_data
    else:
        return "Doctor not found.", None

def generate_qr_code(patient_name, date, time):
    data = f"Patient: {patient_name}\nDate: {date}\nTime: {time}"
    qr = qrcode.make(data)
    qr_bytes = BytesIO()
    qr.save(qr_bytes)
    qr_bytes.seek(0)
    qr_b64 = base64.b64encode(qr_bytes.read()).decode('utf-8')
    return qr_b64

if __name__ == "__main__":
    app.run(debug=True)
