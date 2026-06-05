
"""
vulnerable_student_portal_20.py

Yerel code review testi için bilinçli olarak 20 zafiyet içeren öğrenci portalı demosu.
Gerçek ortamda veya public sunucuda kullanılmamalıdır.

Çalıştırma:
    python vulnerable_student_portal_20.py

Tarayıcı:
    http://localhost:7701
"""

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import sqlite3
import json
import os
import hashlib
import random
import subprocess
import pickle

DB_NAME = "student_portal_20.db"
EXPORT_DIR = "student_exports"

# ZAFİYET-01: Hardcoded secret
APP_SECRET = "student-portal-secret-123"

# ZAFİYET-02: Hardcoded admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"


def init_db():
    os.makedirs(EXPORT_DIR, exist_ok=True)

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("CREATE TABLE IF NOT EXISTS students (id INTEGER PRIMARY KEY, name TEXT, email TEXT, password TEXT, grade TEXT, private_note TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS assignments (id INTEGER PRIMARY KEY, student_id INTEGER, title TEXT, score INTEGER, feedback TEXT)")

    cur.execute("DELETE FROM students")
    cur.execute("DELETE FROM assignments")

    # ZAFİYET-03: Plain text password storage
    cur.execute("INSERT INTO students VALUES (1, 'Kerem Student', 'kerem@example.com', '123456', 'A', 'internal advisor note')")
    cur.execute("INSERT INTO students VALUES (2, 'Admin User', 'admin@example.com', 'admin123', 'ADMIN', 'admin private note')")
    cur.execute("INSERT INTO assignments VALUES (1, 1, 'Security Homework', 85, 'good work')")
    cur.execute("INSERT INTO assignments VALUES (2, 1, 'Database Homework', 70, 'needs improvement')")

    conn.commit()
    conn.close()


class StudentHandler(BaseHTTPRequestHandler):
    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")

        # ZAFİYET-04: CORS wildcard
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8"))

    def send_html(self, html, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def parse_request(self):
        parsed = urlparse(self.path)
        return parsed.path, parse_qs(parsed.query)

    def read_body(self):
        length = int(self.headers.get("Content-Length", "0"))

        # ZAFİYET-05: Request size limit yok
        return self.rfile.read(length)

    def do_GET(self):
        path, q = self.parse_request()

        if path == "/":
            return self.send_json({
                "message": "Vulnerable Student Portal - 20 vulnerabilities",
                "routes": ["/login", "/student", "/assignments", "/search", "/render", "/update-grade", "/export", "/download", "/run", "/config"]
            })

        if path == "/login":
            email = q.get("email", [""])[0]
            password = q.get("password", [""])[0]

            # ZAFİYET-06: Credentials in URL
            # ZAFİYET-07: Sensitive data logging
            with open("student_login.log", "a", encoding="utf-8") as f:
                f.write(f"email={email}, password={password}\n")

            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()

            # ZAFİYET-08: SQL Injection
            sql = f"SELECT id, name, email, grade FROM students WHERE email = '{email}' AND password = '{password}'"
            cur.execute(sql)
            student = cur.fetchone()
            conn.close()

            if not student:
                return self.send_json({"error": "Invalid credentials"}, 401)

            # ZAFİYET-09: Predictable token generation
            random.seed(email)

            # ZAFİYET-10: Weak hash algorithm for token
            token = hashlib.md5(f"{email}-{random.randint(1000,9999)}-{APP_SECRET}".encode()).hexdigest()
            return self.send_json({"status": "success", "student": student, "token": token})

        if path == "/student":
            student_id = q.get("id", ["0"])[0]

            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()

            # ZAFİYET-11: SQL Injection
            cur.execute(f"SELECT id, name, email, password, grade, private_note FROM students WHERE id = {student_id}")
            row = cur.fetchone()
            conn.close()

            if not row:
                return self.send_json({"error": "Student not found"}, 404)

            # ZAFİYET-12: Sensitive data exposure
            return self.send_json({
                "id": row[0],
                "name": row[1],
                "email": row[2],
                "password": row[3],
                "grade": row[4],
                "private_note": row[5]
            })

        if path == "/assignments":
            student_id = q.get("student_id", ["0"])[0]

            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()

            # ZAFİYET-13: IDOR / Broken Access Control
            # Başka öğrencinin ödevleri yetki kontrolü olmadan okunabiliyor.
            cur.execute(f"SELECT id, student_id, title, score, feedback FROM assignments WHERE student_id = {student_id}")
            rows = cur.fetchall()
            conn.close()

            return self.send_json({"assignments": rows})

        if path == "/search":
            keyword = q.get("q", [""])[0]

            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()

            # ZAFİYET-14: SQL Injection in LIKE query
            sql = f"SELECT id, name, email FROM students WHERE name LIKE '%{keyword}%' OR email LIKE '%{keyword}%'"
            cur.execute(sql)
            rows = cur.fetchall()
            conn.close()

            return self.send_json({"sql": sql, "results": rows})

        if path == "/render":
            student_id = q.get("id", ["1"])[0]

            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()
            cur.execute(f"SELECT name, private_note FROM students WHERE id = {student_id}")
            row = cur.fetchone()
            conn.close()

            if not row:
                return self.send_html("<h1>Student not found</h1>", 404)

            # ZAFİYET-15: Stored XSS
            return self.send_html(f"<html><body><h1>{row[0]}</h1><p>{row[1]}</p></body></html>")

        if path == "/update-grade":
            student_id = q.get("id", ["0"])[0]
            grade = q.get("grade", [""])[0]

            # ZAFİYET-16: Missing authorization
            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()
            cur.execute(f"UPDATE students SET grade = '{grade}' WHERE id = {student_id}")
            conn.commit()
            conn.close()

            return self.send_json({"status": "grade_updated", "student_id": student_id, "grade": grade})

        if path == "/download":
            file_name = q.get("file", [""])[0]

            # ZAFİYET-17: Path Traversal / Arbitrary file read
            file_path = os.path.join(EXPORT_DIR, file_name)

            if not os.path.exists(file_path):
                return self.send_json({"error": "File not found", "attempted_path": os.path.abspath(file_path)}, 404)

            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return self.send_json({"file": file_path, "content": f.read()})

        if path == "/run":
            command = q.get("cmd", ["echo student"])[0]

            # ZAFİYET-18: Command Injection
            output = subprocess.check_output(command, shell=True, text=True)
            return self.send_json({"command": command, "output": output})

        if path == "/config":
            # ZAFİYET-19: Configuration exposure
            return self.send_json({
                "app_secret": APP_SECRET,
                "admin_username": ADMIN_USERNAME,
                "admin_password": ADMIN_PASSWORD,
                "db_name": DB_NAME,
                "cwd": os.getcwd()
            })

        # ZAFİYET-20: Verbose error
        return self.send_json({"error": "Route not found", "path": path}, 404)

    def do_POST(self):
        path, _ = self.parse_request()

        if path == "/import":
            body = self.read_body()
            data = pickle.loads(body)
            return self.send_json({"status": "imported", "data": str(data)})

        return self.send_json({"error": "Route not found"}, 404)


if __name__ == "__main__":
    init_db()
    HTTPServer(("0.0.0.0", 7701), StudentHandler).serve_forever()
