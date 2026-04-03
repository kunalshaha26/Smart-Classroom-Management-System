import sys
import cv2
import matplotlib.pyplot as plt

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QMessageBox, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QFrame
)

from database import connect_db, add_student, get_students, mark_attendance, get_attendance_report, delete_student

connect_db()


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("SCMS Pro")
        self.setGeometry(100, 100, 400, 300)

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
        """)

        layout = QVBoxLayout()

        title = QLabel("⚡ Smart Classroom Pro")
        title.setStyleSheet("font-size:26px; font-weight:bold;")

        self.user = QLineEdit()
        self.user.setPlaceholderText("Username")

        self.password = QLineEdit()
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QLineEdit.Password)

        btn = QPushButton("Login")
        btn.clicked.connect(self.login)

        layout.addWidget(title)
        layout.addWidget(self.user)
        layout.addWidget(self.password)
        layout.addWidget(btn)

        self.setLayout(layout)

    def login(self):
        if self.user.text() == "admin" and self.password.text() == "1234":
            self.dashboard()
        else:
            QMessageBox.warning(self, "Error", "Invalid login")

    def dashboard(self):
        self.win = QWidget()
        self.win.setWindowTitle("Dashboard")
        self.win.setGeometry(100, 100, 1300, 700)

        main_layout = QHBoxLayout()

        # 🔥 SIDEBAR
        sidebar = QVBoxLayout()
        sidebar_widget = QFrame()
        sidebar_widget.setLayout(sidebar)

        def side_btn(text):
            btn = QPushButton(text)
            return btn

        btn_add = side_btn("➕ Add Student")
        btn_scan = side_btn("📷 Scan QR")
        btn_report = side_btn("📊 Report")
        btn_graph = side_btn("📈 Graph")

        sidebar.addWidget(btn_add)
        sidebar.addWidget(btn_scan)
        sidebar.addWidget(btn_report)
        sidebar.addWidget(btn_graph)
        sidebar.addStretch()

        btn_add.clicked.connect(self.add_student_ui)
        btn_scan.clicked.connect(self.scan_qr)
        btn_report.clicked.connect(self.show_report)
        btn_graph.clicked.connect(self.show_graph)

        # 🔥 MAIN CONTENT
        content = QVBoxLayout()

        header = QLabel("Dashboard Overview")
        header.setStyleSheet("font-size:22px; font-weight:bold;")

        # FORM
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

        # TABLE
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", "Name", "Class"])

        # DELETE BUTTON ✅
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
        self.close()

    def save_student(self):
        add_student(self.input_name.text(), self.input_class.text())
        self.load_students()

    def load_students(self):
        data = get_students()
        self.table.setRowCount(len(data))

        for r, row in enumerate(data):
            for c, val in enumerate(row):
                self.table.setItem(r, c, QTableWidgetItem(str(val)))

    def delete_selected_student(self):
        selected = self.table.currentRow()

        if selected == -1:
            QMessageBox.warning(self, "Error", "Select a student first ❌")
            return

        student_id = self.table.item(selected, 0).text()

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this student?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            delete_student(student_id)
            QMessageBox.information(self, "Success", "Student deleted ✅")
            self.load_students()

    def add_student_ui(self):
        QMessageBox.information(self, "Info", "Use form")

    def scan_qr(self):
        cap = cv2.VideoCapture(0)
        detector = cv2.QRCodeDetector()

        while True:
            _, frame = cap.read()
            data, _, _ = detector.detectAndDecode(frame)

            if data:
                mark_attendance(data)
                QMessageBox.information(self, "Done", f"{data}")
                break

            cv2.imshow("Scan", frame)
            if cv2.waitKey(1) == 27:
                break

        cap.release()
        cv2.destroyAllWindows()

    def show_report(self):
        data, total = get_attendance_report()
        text = ""

        for _, name, present in data:
            percent = (present / total * 100) if total else 0
            text += f"{name}: {percent:.2f}%\n"

        QMessageBox.information(self, "Report", text)

    def show_graph(self):
        data, total = get_attendance_report()

        names = []
        perc = []

        for _, name, present in data:
            percent = (present / total * 100) if total else 0
            names.append(name)
            perc.append(percent)

        plt.bar(names, perc)
        plt.show()


app = QApplication(sys.argv)
window = LoginWindow()
window.show()
sys.exit(app.exec_())