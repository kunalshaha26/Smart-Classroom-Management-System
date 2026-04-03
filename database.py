import sqlite3
import qrcode
import os
from datetime import datetime


# 🔹 Create Tables
def connect_db():
    conn = sqlite3.connect("scms.db")
    cursor = conn.cursor()

    # Students Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        class TEXT
    )
    """)

    # Attendance Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        date TEXT
    )
    """)

    print("Database & Tables Ready ✅")

    conn.commit()
    conn.close()


# 🔹 Generate QR Code
def generate_qr(student_id):
    folder = "qrcodes"

    if not os.path.exists(folder):
        os.makedirs(folder)

    data = str(student_id)

    img = qrcode.make(data)
    img.save(f"{folder}/student_{student_id}.png")


# 🔹 Add Student
def add_student(name, student_class):
    conn = sqlite3.connect("scms.db")
    cursor = conn.cursor()

    cursor.execute("INSERT INTO students (name, class) VALUES (?, ?)", (name, student_class))
    student_id = cursor.lastrowid

    conn.commit()
    conn.close()

    generate_qr(student_id)


# 🔹 Get All Students
def get_students():
    conn = sqlite3.connect("scms.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM students")
    data = cursor.fetchall()

    conn.close()
    return data


# 🔹 Mark Attendance
def mark_attendance(student_id):
    conn = sqlite3.connect("scms.db")
    cursor = conn.cursor()

    today = datetime.now().strftime("%Y-%m-%d")

    cursor.execute("SELECT * FROM attendance WHERE student_id=? AND date=?", (student_id, today))
    result = cursor.fetchone()

    if not result:
        cursor.execute("INSERT INTO attendance (student_id, date) VALUES (?, ?)", (student_id, today))
        conn.commit()

    conn.close()


# 🔹 Attendance Report (FIXED POSITION ✅)
def get_attendance_report():
    conn = sqlite3.connect("scms.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT students.id, students.name,
           COUNT(attendance.id) as present_days
    FROM students
    LEFT JOIN attendance
    ON students.id = attendance.student_id
    GROUP BY students.id
    """)

    data = cursor.fetchall()

    # 🔥 Get total days
    cursor.execute("SELECT COUNT(DISTINCT date) FROM attendance")
    total_days = cursor.fetchone()[0]

    conn.close()

    return data, total_days
def delete_student(student_id):
    conn = sqlite3.connect("scms.db")
    cursor = conn.cursor()

    # 🔥 Delete attendance first (important)
    cursor.execute("DELETE FROM attendance WHERE student_id=?", (student_id,))

    # 🔥 Delete student
    cursor.execute("DELETE FROM students WHERE id=?", (student_id,))

    conn.commit()
    conn.close()

    # 🔥 Delete QR file
    qr_path = f"qrcodes/student_{student_id}.png"
    if os.path.exists(qr_path):
        os.remove(qr_path)