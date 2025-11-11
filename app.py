# Import necessary modules
from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this to a secure key

# Database connection setup
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",      # change if your MySQL runs on another host
        user="root",           # your MySQL username
        password="",           # your MySQL password
        database="attendance_db"  # your database name
    )

# Database initialization (creates tables if not exist)
def init_db():
    conn = get_db_connection()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS students (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    sr_code VARCHAR(50) UNIQUE NOT NULL,
                    section VARCHAR(100) NOT NULL
                )''')

    c.execute('''CREATE TABLE IF NOT EXISTS attendance (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    student_id INT,
                    subject VARCHAR(255),
                    date DATE,
                    status VARCHAR(50),
                    time_in VARCHAR(20),
                    time_out VARCHAR(20),
                    FOREIGN KEY (student_id) REFERENCES students (id)
                )''')
    conn.commit()
    conn.close()

init_db()

# Helper functions
def is_duplicate_sr_code(sr_code):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM students WHERE sr_code = %s", (sr_code,))
    result = c.fetchone()
    conn.close()
    return result is not None

def is_duplicate_name(name):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM students WHERE name = %s", (name,))
    result = c.fetchone()
    conn.close()
    return result is not None

# Routes
@app.route('/')
def index():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == 'password123':
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT name, sr_code, section FROM students")
    students = c.fetchall()
    conn.close()
    return render_template('dashboard.html', students=students)

@app.route('/attendance', methods=['GET', 'POST'])
def attendance():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        sr_code = request.form['sr_code']
        subject = request.form['subject']
        date = request.form['date']
        status = request.form['status']
        time_in = request.form.get('time_in', '')
        time_out = request.form.get('time_out', '')

        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT id FROM students WHERE sr_code = %s", (sr_code,))
        student = c.fetchone()
        if student:
            student_id = student[0]
            c.execute("INSERT INTO attendance (student_id, subject, date, status, time_in, time_out) VALUES (%s, %s, %s, %s, %s, %s)",
                      (student_id, subject, date, status, time_in, time_out))
            conn.commit()
            flash('Attendance marked successfully')
        else:
            flash('Student not found')
        conn.close()
        return redirect(url_for('attendance'))

    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""SELECT s.name, s.sr_code, a.subject, a.date, a.status, a.time_in, a.time_out 
                 FROM attendance a 
                 JOIN students s ON a.student_id = s.id""")
    records = c.fetchall()
    conn.close()
    return render_template('attendance.html', records=records)

@app.route('/add_student', methods=['GET', 'POST'])
def add_student():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form['name']
        sr_code = request.form['sr_code']
        section = request.form['section']

        if is_duplicate_name(name):
            flash('Duplicate name')
            return redirect(url_for('add_student'))
        if is_duplicate_sr_code(sr_code):
            flash('Duplicate SR-Code')
            return redirect(url_for('add_student'))

        conn = get_db_connection()
        c = conn.cursor()
        c.execute("INSERT INTO students (name, sr_code, section) VALUES (%s, %s, %s)", (name, sr_code, section))
        conn.commit()
        conn.close()
        flash('Student added successfully')
        return redirect(url_for('dashboard'))
    return render_template('add_student.html')

@app.route('/settings')
def settings():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    return render_template('settings.html')

if __name__ == '__main__':
    app.run(debug=True)
