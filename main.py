import sys
import cv2
import matplotlib.pyplot as plt
import sqlite3

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *

from database import connect_db, add_student, mark_attendance, get_attendance_report, delete_student

connect_db()


# 🔐 LOGIN FUNCTION
def login_user(username, password):
    conn = sqlite3.connect("scms.db")
    cursor = conn.cursor()

    cursor.execute("SELECT id, role FROM users WHERE username=? AND password=?", (username, password))
    result = cursor.fetchone()

    conn.close()
    return result


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("SCMS Pro")
        self.setGeometry(100, 100, 400, 350)

        self.setStyleSheet("""
        QWidget {
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
            stop:0 #0f172a, stop:1 #1e293b);
            color: white;
        }
        QLineEdit {
            padding: 12px;
            border-radius: 10px;
            background: rgba(255,255,255,0.08);
        }
        QPushButton {
            padding: 12px;
            border-radius: 12px;
            background: #6366f1;
        }
        QComboBox {
            padding: 10px;
            border-radius: 10px;
            background: rgba(255,255,255,0.08);
        }
        """)

        layout = QVBoxLayout()

        title = QLabel("⚡ Smart Classroom Pro")
        title.setStyleSheet("font-size:26px; font-weight:bold;")
        title.setAlignment(Qt.AlignCenter)

        self.role = QComboBox()
        self.role.addItems(["Select Role", "admin", "teacher", "student"])

        self.user = QLineEdit()
        self.user.setPlaceholderText("Username")

        self.password = QLineEdit()
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QLineEdit.Password)

        btn = QPushButton("Login")
        btn.clicked.connect(self.login)

        layout.addWidget(title)
        layout.addWidget(self.role)
        layout.addWidget(self.user)
        layout.addWidget(self.password)
        layout.addWidget(btn)

        self.setLayout(layout)

    # 🔐 LOGIN LOGIC
    def login(self):
        selected_role = self.role.currentText()

        if selected_role == "Select Role":
            QMessageBox.warning(self, "Error", "Please select role ❌")
            return

        if not self.user.text() or not self.password.text():
            QMessageBox.warning(self, "Error", "Enter username & password ❌")
            return

        result = login_user(self.user.text(), self.password.text())

        if result:
            user_id, role = result

            if role != selected_role:
                QMessageBox.warning(self, "Error", "Wrong role selected ❌")
                return

            if role in ["admin", "teacher"]:
                self.dashboard(role)
            else:
                self.student_dashboard(user_id)
        else:
            QMessageBox.warning(self, "Error", "Invalid login ❌")

    # 🔁 LOGOUT FUNCTION (NEW 🔥)
    def logout(self, window):
        reply = QMessageBox.question(
            window,
            "Logout",
            "Are you sure you want to logout?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            window.close()
            self.show()

    # 👨‍💼 DASHBOARD
    def dashboard(self, role):
        self.win = QWidget()
        self.win.setWindowTitle(f"{role.upper()} Dashboard")
        self.win.setGeometry(100, 100, 1200, 650)

        main_layout = QHBoxLayout()

        sidebar = QVBoxLayout()
        sidebar_widget = QFrame()
        sidebar_widget.setLayout(sidebar)

        def side_btn(text):
            return QPushButton(text)

        btn_add = side_btn("➕ Add Student")
        btn_scan = side_btn("📷 Scan QR")
        btn_report = side_btn("📊 Report")
        btn_graph = side_btn("📈 Graph")
        btn_logout = side_btn("🚪 Logout")  # 🔥 NEW

        sidebar.addWidget(btn_add)
        sidebar.addWidget(btn_scan)
        sidebar.addWidget(btn_report)
        sidebar.addWidget(btn_graph)
        sidebar.addStretch()
        sidebar.addWidget(btn_logout)  # 🔥 bottom logout

        if role == "teacher":
            btn_add.setDisabled(True)

        btn_add.clicked.connect(self.add_student_ui)
        btn_scan.clicked.connect(self.scan_qr)
        btn_report.clicked.connect(self.show_report)
        btn_graph.clicked.connect(self.show_graph)

        # 🔥 LOGOUT CONNECT
        btn_logout.clicked.connect(lambda: self.logout(self.win))

        content = QVBoxLayout()

        header = QLabel(f"{role.capitalize()} Dashboard")
        header.setStyleSheet("font-size:22px; font-weight:bold;")

        form = QHBoxLayout()

        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("Student Name")

        self.input_class = QLineEdit()
        self.input_class.setPlaceholderText("Class")

        save = QPushButton("Save")
        save.clicked.connect(self.save_student)

        form.addWidget(self.input_name)
        form.addWidget(self.input_class)
        form.addWidget(save)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Name", "Attended", "Total", "%"]
        )

        delete_btn = QPushButton("❌ Delete Student")
        delete_btn.clicked.connect(self.delete_selected_student)

        content.addWidget(header)
        content.addLayout(form)
        content.addWidget(self.table)
        content.addWidget(delete_btn)

        main_layout.addWidget(sidebar_widget, 1)
        main_layout.addLayout(content, 4)

        self.win.setLayout(main_layout)

        self.load_students()
        self.win.show()
        self.hide()  # 🔥 IMPORTANT (instead of close)

    # 🎓 STUDENT DASHBOARD
    def student_dashboard(self, user_id):
        self.win = QWidget()
        self.win.setWindowTitle("Student Dashboard")
        self.win.setGeometry(100, 100, 800, 500)

        layout = QVBoxLayout()

        title = QLabel("🎓 My Attendance")
        title.setStyleSheet("font-size:22px; font-weight:bold;")

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Date", "Status"])

        conn = sqlite3.connect("scms.db")
        cursor = conn.cursor()

        cursor.execute("""
        SELECT date, status FROM attendance 
        WHERE student_id = (
            SELECT id FROM students WHERE user_id=?
        )
        """, (user_id,))

        data = cursor.fetchall()
        conn.close()

        self.table.setRowCount(len(data))

        present = 0

        for i, row in enumerate(data):
            date, status = row

            self.table.setItem(i, 0, QTableWidgetItem(date))
            self.table.setItem(i, 1, QTableWidgetItem(status))

            if status == "Present":
                present += 1

        total = len(data)
        percent = (present / total * 100) if total > 0 else 0

        percent_label = QLabel(f"Attendance: {percent:.2f}%")
        percent_label.setStyleSheet("font-size:18px;")

        # 🔥 LOGOUT BUTTON (STUDENT)
        logout_btn = QPushButton("🚪 Logout")
        logout_btn.clicked.connect(lambda: self.logout(self.win))

        layout.addWidget(title)
        layout.addWidget(self.table)
        layout.addWidget(percent_label)
        layout.addWidget(logout_btn)

        self.win.setLayout(layout)
        self.win.show()
        self.hide()

    # ➕ SAVE STUDENT
    def save_student(self):
        name = self.input_name.text()
        student_class = self.input_class.text()

        if not name or not student_class:
            QMessageBox.warning(self, "Error", "Enter all fields ❌")
            return

        username, password = add_student(name, student_class)

        QMessageBox.information(
            self,
            "Student Created ✅",
            f"Username: {username}\nPassword: {password}"
        )

        self.input_name.clear()
        self.input_class.clear()
        self.load_students()

    # LOAD TABLE
    def load_students(self):
        data = get_attendance_report()
        self.table.setRowCount(len(data))

        for r, row in enumerate(data):
            for c, val in enumerate(row):
                self.table.setItem(r, c, QTableWidgetItem(str(val)))

    # DELETE
    def delete_selected_student(self):
        selected = self.table.currentRow()

        if selected == -1:
            QMessageBox.warning(self, "Error", "Select student ❌")
            return

        student_id = self.table.item(selected, 0).text()
        delete_student(student_id)
        self.load_students()

    def add_student_ui(self):
        QMessageBox.information(self, "Info", "Use form above")

    # 📷 QR
    def scan_qr(self):
        cap = cv2.VideoCapture(0)
        detector = cv2.QRCodeDetector()

        while True:
            _, frame = cap.read()
            data, _, _ = detector.detectAndDecode(frame)

            if data:
                try:
                    mark_attendance(int(data))
                    QMessageBox.information(self, "Success", f"Attendance marked ID: {data}")
                except:
                    QMessageBox.warning(self, "Error", "Invalid QR ❌")
                break

            cv2.imshow("Scan QR", frame)
            if cv2.waitKey(1) == 27:
                break

        cap.release()
        cv2.destroyAllWindows()
        self.load_students()

    def show_report(self):
        data = get_attendance_report()

        text = ""
        for _, name, attended, total, percent in data:
            text += f"{name} → {attended}/{total} ({percent}%)\n"

        QMessageBox.information(self, "Report", text)

    def show_graph(self):
        data = get_attendance_report()

        names = [x[1] for x in data]
        perc = [x[4] for x in data]

        plt.bar(names, perc)
        plt.title("Attendance %")
        plt.show()


app = QApplication(sys.argv)
window = LoginWindow()
window.show()
sys.exit(app.exec_())
