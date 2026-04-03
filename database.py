import sqlite3
import qrcode
import os
from datetime import datetime


def connect_db():
    conn = sqlite3.connect("scms.db")
    cursor = conn.cursor()

    # USERS TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT
    )
    """)

    # STUDENTS TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        class TEXT,
        user_id INTEGER
    )
    """)

    # ✅ FIX OLD STUDENTS TABLE
    cursor.execute("PRAGMA table_info(students)")
    cols = [c[1] for c in cursor.fetchall()]
    if "user_id" not in cols:
        cursor.execute("ALTER TABLE students ADD COLUMN user_id INTEGER")

    # ATTENDANCE TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        date TEXT,
        status TEXT
    )
    """)

    # ✅ FIX OLD ATTENDANCE TABLE
    cursor.execute("PRAGMA table_info(attendance)")
    cols = [c[1] for c in cursor.fetchall()]
    if "status" not in cols:
        cursor.execute("ALTER TABLE attendance ADD COLUMN status TEXT DEFAULT 'Present'")

    # 📁 CREATE CREDENTIALS FOLDER
    if not os.path.exists("credentials"):
        os.makedirs("credentials")

    # DEFAULT ADMIN
    cursor.execute("SELECT * FROM users WHERE username=?", ("admin",))
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO users VALUES (NULL, ?, ?, ?)",
            ("admin", "admin123", "admin")
        )

    # SAVE ADMIN FILE (only once)
    if not os.path.exists("credentials/admin.txt"):
        with open("credentials/admin.txt", "w") as f:
            f.write("Role: Admin\nUsername: admin\nPassword: admin123")

    # DEFAULT TEACHER
    cursor.execute("SELECT * FROM users WHERE username=?", ("teacher",))
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO users VALUES (NULL, ?, ?, ?)",
            ("teacher", "teacher123", "teacher")
        )

    # SAVE TEACHER FILE (only once)
    if not os.path.exists("credentials/teacher.txt"):
        with open("credentials/teacher.txt", "w") as f:
            f.write("Role: Teacher\nUsername: teacher\nPassword: teacher123")

    conn.commit()
    conn.close()


# QR GENERATION
def generate_qr(student_id):
    if not os.path.exists("qrcodes"):
        os.makedirs("qrcodes")

    img = qrcode.make(str(student_id))
    img.save(f"qrcodes/student_{student_id}.png")


# ADD STUDENT
def add_student(name, student_class):
    conn = sqlite3.connect("scms.db")
    cursor = conn.cursor()

    username = name.lower().replace(" ", "") + datetime.now().strftime("%H%M%S")
    password = "1234"

    # CREATE USER
    cursor.execute(
        "INSERT INTO users VALUES (NULL, ?, ?, ?)",
        (username, password, "student")
    )

    user_id = cursor.lastrowid

    # CREATE STUDENT
    cursor.execute(
        "INSERT INTO students VALUES (NULL, ?, ?, ?)",
        (name, student_class, user_id)
    )

    student_id = cursor.lastrowid

    conn.commit()
    conn.close()

    generate_qr(student_id)

    # 📁 SAVE STUDENT CREDENTIALS
    if not os.path.exists("credentials"):
        os.makedirs("credentials")

    with open(f"credentials/{username}.txt", "w") as f:
        f.write(f"Role: Student\nUsername: {username}\nPassword: {password}")

    return username, password


# MARK ATTENDANCE
def mark_attendance(student_id):
    conn = sqlite3.connect("scms.db")
    cursor = conn.cursor()

    today = datetime.now().strftime("%Y-%m-%d")

    cursor.execute(
        "SELECT * FROM attendance WHERE student_id=? AND date=?",
        (student_id, today)
    )

    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO attendance VALUES (NULL, ?, ?, ?)",
            (student_id, today, "Present")
        )
        conn.commit()

    conn.close()


# GET REPORT
def get_attendance_report():
    conn = sqlite3.connect("scms.db")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(DISTINCT date) FROM attendance")
    total_days = cursor.fetchone()[0]

    cursor.execute("""
    SELECT students.id, students.name, COUNT(attendance.id)
    FROM students
    LEFT JOIN attendance ON students.id = attendance.student_id
    GROUP BY students.id
    """)

    data = cursor.fetchall()
    result = []

    for sid, name, attended in data:
        percent = (attended / total_days * 100) if total_days else 0
        result.append((sid, name, attended, total_days, round(percent, 2)))

    conn.close()
    return result


# DELETE STUDENT
def delete_student(student_id):
    conn = sqlite3.connect("scms.db")
    cursor = conn.cursor()

    cursor.execute("SELECT user_id FROM students WHERE id=?", (student_id,))
    res = cursor.fetchone()

    if res:
        uid = res[0]

        cursor.execute("DELETE FROM attendance WHERE student_id=?", (student_id,))
        cursor.execute("DELETE FROM students WHERE id=?", (student_id,))
        cursor.execute("DELETE FROM users WHERE id=?", (uid,))

    conn.commit()
    conn.close()

    # DELETE QR FILE
    qr_path = f"qrcodes/student_{student_id}.png"
    if os.path.exists(qr_path):
        os.remove(qr_path)
