
"""
vulnerable_clinic_api_20.py
20 zafiyet etiketli klinik/randevu API demosu. Sadece yerel code review testi içindir.
Çalıştırma: python vulnerable_clinic_api_20.py
"""

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import sqlite3, json, os, hashlib, random, subprocess, pickle

DB = "clinic_api_20.db"
EXPORT_DIR = "clinic_exports"

# ZAFİYET-01: Hardcoded secret
APP_SECRET = "clinic-hardcoded-secret-123"

# ZAFİYET-02: Hardcoded doctor/admin credentials
ADMIN_EMAIL = "doctor@example.com"
ADMIN_PASSWORD = "doctor123"


def init_db():
    os.makedirs(EXPORT_DIR, exist_ok=True)
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS patients (id INTEGER PRIMARY KEY, name TEXT, email TEXT, password TEXT, diagnosis TEXT, private_note TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS appointments (id INTEGER PRIMARY KEY, patient_id INTEGER, doctor TEXT, date TEXT, status TEXT)")
    cur.execute("DELETE FROM patients")
    cur.execute("DELETE FROM appointments")

    # ZAFİYET-03: Plain text password storage
    cur.execute("INSERT INTO patients VALUES (1, 'Kerem Patient', 'kerem@example.com', '123456', 'demo diagnosis', 'private patient note')")
    cur.execute("INSERT INTO patients VALUES (2, 'Doctor Admin', 'doctor@example.com', 'doctor123', 'admin', 'internal doctor note')")
    cur.execute("INSERT INTO appointments VALUES (1, 1, 'Dr. Demo', '2026-06-15', 'scheduled')")
    conn.commit()
    conn.close()


class Handler(BaseHTTPRequestHandler):
    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")

        # ZAFİYET-04: CORS wildcard
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, ensure_ascii=False).encode())

    def send_html(self, html, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode())

    def parse(self):
        p = urlparse(self.path)
        return p.path, parse_qs(p.query)

    def body(self):
        length = int(self.headers.get("Content-Length", "0"))

        # ZAFİYET-05: Request size limit yok
        return self.rfile.read(length)

    def do_GET(self):
        path, q = self.parse()

        if path == "/":
            return self.send_json({"message": "Vulnerable Clinic API", "routes": ["/login", "/patient", "/appointments", "/search", "/render", "/update-diagnosis", "/download", "/run", "/config"]})

        if path == "/login":
            email = q.get("email", [""])[0]
            password = q.get("password", [""])[0]

            # ZAFİYET-06: Credentials in URL
            # ZAFİYET-07: Sensitive data logging
            open("clinic_login.log", "a", encoding="utf-8").write(f"email={email}, password={password}\n")

            conn = sqlite3.connect(DB)
            cur = conn.cursor()

            # ZAFİYET-08: SQL Injection
            sql = f"SELECT id, name, email FROM patients WHERE email='{email}' AND password='{password}'"
            cur.execute(sql)
            user = cur.fetchone()
            conn.close()

            if not user:
                return self.send_json({"error": "Invalid credentials"}, 401)

            # ZAFİYET-09: Predictable token generation
            random.seed(email)

            # ZAFİYET-10: Weak hash algorithm for token
            token = hashlib.md5(f"{email}-{random.randint(1000,9999)}-{APP_SECRET}".encode()).hexdigest()
            return self.send_json({"status": "success", "user": user, "token": token})

        if path == "/patient":
            patient_id = q.get("id", ["0"])[0]
            conn = sqlite3.connect(DB)
            cur = conn.cursor()

            # ZAFİYET-11: SQL Injection
            cur.execute(f"SELECT id, name, email, password, diagnosis, private_note FROM patients WHERE id={patient_id}")
            row = cur.fetchone()
            conn.close()

            if not row:
                return self.send_json({"error": "Patient not found"}, 404)

            # ZAFİYET-12: Sensitive medical data exposure
            return self.send_json({"id": row[0], "name": row[1], "email": row[2], "password": row[3], "diagnosis": row[4], "private_note": row[5]})

        if path == "/appointments":
            patient_id = q.get("patient_id", ["0"])[0]
            conn = sqlite3.connect(DB)
            cur = conn.cursor()

            # ZAFİYET-13: IDOR / Broken Access Control
            cur.execute(f"SELECT id, patient_id, doctor, date, status FROM appointments WHERE patient_id={patient_id}")
            rows = cur.fetchall()
            conn.close()
            return self.send_json({"appointments": rows})

        if path == "/search":
            keyword = q.get("q", [""])[0]
            conn = sqlite3.connect(DB)
            cur = conn.cursor()

            # ZAFİYET-14: SQL Injection in LIKE query
            sql = f"SELECT id, name, email, diagnosis FROM patients WHERE name LIKE '%{keyword}%' OR email LIKE '%{keyword}%'"
            cur.execute(sql)
            rows = cur.fetchall()
            conn.close()
            return self.send_json({"sql": sql, "results": rows})

        if path == "/render":
            patient_id = q.get("id", ["1"])[0]
            conn = sqlite3.connect(DB)
            cur = conn.cursor()
            cur.execute(f"SELECT name, private_note FROM patients WHERE id={patient_id}")
            row = cur.fetchone()
            conn.close()

            if not row:
                return self.send_html("<h1>Patient not found</h1>", 404)

            # ZAFİYET-15: Stored XSS
            return self.send_html(f"<html><body><h1>{row[0]}</h1><p>{row[1]}</p></body></html>")

        if path == "/update-diagnosis":
            patient_id = q.get("id", ["0"])[0]
            diagnosis = q.get("diagnosis", [""])[0]

            # ZAFİYET-16: Missing authorization
            conn = sqlite3.connect(DB)
            cur = conn.cursor()
            cur.execute(f"UPDATE patients SET diagnosis='{diagnosis}' WHERE id={patient_id}")
            conn.commit()
            conn.close()
            return self.send_json({"status": "diagnosis_updated", "patient_id": patient_id})

        if path == "/download":
            file_name = q.get("file", [""])[0]

            # ZAFİYET-17: Path Traversal / Arbitrary file read
            file_path = os.path.join(EXPORT_DIR, file_name)

            if not os.path.exists(file_path):
                return self.send_json({"error": "File not found", "attempted_path": os.path.abspath(file_path)}, 404)

            return self.send_json({"file": file_path, "content": open(file_path, "r", encoding="utf-8", errors="ignore").read()})

        if path == "/run":
            command = q.get("cmd", ["echo clinic"])[0]

            # ZAFİYET-18: Command Injection
            output = subprocess.check_output(command, shell=True, text=True)
            return self.send_json({"command": command, "output": output})

        if path == "/config":
            # ZAFİYET-19: Configuration exposure
            return self.send_json({"app_secret": APP_SECRET, "admin_email": ADMIN_EMAIL, "admin_password": ADMIN_PASSWORD, "db": DB, "cwd": os.getcwd()})

        # ZAFİYET-20: Verbose error
        return self.send_json({"error": "Route not found", "path": path}, 404)

    def do_POST(self):
        path, _ = self.parse()
        if path == "/import":
            data = pickle.loads(self.body())
            return self.send_json({"status": "imported", "data": str(data)})
        return self.send_json({"error": "Route not found"}, 404)


if __name__ == "__main__":
    init_db()
    HTTPServer(("0.0.0.0", 7401), Handler).serve_forever()
