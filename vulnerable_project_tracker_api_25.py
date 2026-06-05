
"""
vulnerable_project_tracker_api_25.py

Yerel code review testi için bilinçli olarak 25 zafiyet içeren proje takip API demosu.
Gerçek ortamda veya public sunucuda kullanılmamalıdır.

Çalıştırma:
    python vulnerable_project_tracker_api_25.py

Tarayıcı:
    http://localhost:7601
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
import tempfile

DB_NAME = "project_tracker_25.db"
EXPORT_DIR = "project_exports"

# ZAFİYET-01: Hardcoded application secret
APP_SECRET = "project-tracker-secret-123"

# ZAFİYET-02: Hardcoded admin credentials
ADMIN_EMAIL = "admin@project.local"
ADMIN_PASSWORD = "admin123"

# ZAFİYET-03: Hardcoded external integration token
INTEGRATION_TOKEN = "integration-token-123"


def init_db():
    os.makedirs(EXPORT_DIR, exist_ok=True)

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, password TEXT, role TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS projects (id INTEGER PRIMARY KEY, owner_id INTEGER, title TEXT, status TEXT, private_note TEXT)")

    cur.execute("DELETE FROM users")
    cur.execute("DELETE FROM projects")

    # ZAFİYET-04: Plain text password storage
    cur.execute("INSERT INTO users VALUES (1, 'Kerem User', 'kerem@example.com', '123456', 'developer')")
    cur.execute("INSERT INTO users VALUES (2, 'Admin User', 'admin@project.local', 'admin123', 'admin')")

    cur.execute("INSERT INTO projects VALUES (1, 1, 'Graduation Project', 'active', 'advisor internal note')")
    cur.execute("INSERT INTO projects VALUES (2, 2, 'Admin Project', 'secret', 'private admin roadmap')")

    conn.commit()
    conn.close()


class ProjectHandler(BaseHTTPRequestHandler):
    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")

        # ZAFİYET-05: CORS wildcard
        self.send_header("Access-Control-Allow-Origin", "*")

        # ZAFİYET-06: Security headers missing
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

        # ZAFİYET-07: Request size limit yok
        return self.rfile.read(length)

    def do_GET(self):
        path, q = self.parse_request()

        if path == "/":
            return self.send_json({
                "message": "Vulnerable Project Tracker API - 25 vulnerabilities",
                "routes": ["/login", "/user", "/project", "/projects", "/search", "/render", "/update-status", "/export", "/download", "/run", "/hash", "/config"]
            })

        if path == "/login":
            email = q.get("email", [""])[0]
            password = q.get("password", [""])[0]

            # ZAFİYET-08: Credentials in URL
            # E-posta/parola query string ile taşınıyor.

            # ZAFİYET-09: Sensitive data logging
            with open("project_login.log", "a", encoding="utf-8") as f:
                f.write(f"email={email}, password={password}\n")

            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()

            # ZAFİYET-10: SQL Injection
            sql = f"SELECT id, name, email, role FROM users WHERE email = '{email}' AND password = '{password}'"
            cur.execute(sql)
            user = cur.fetchone()
            conn.close()

            if not user:
                return self.send_json({"error": "Invalid credentials"}, 401)

            # ZAFİYET-11: Predictable token generation
            random.seed(email)

            # ZAFİYET-12: Weak hash algorithm for token
            token = hashlib.md5(f"{email}-{random.randint(1000,9999)}-{APP_SECRET}".encode()).hexdigest()
            return self.send_json({"status": "success", "user": user, "token": token})

        if path == "/user":
            user_id = q.get("id", ["0"])[0]

            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()

            # ZAFİYET-13: SQL Injection
            cur.execute(f"SELECT id, name, email, password, role FROM users WHERE id = {user_id}")
            row = cur.fetchone()
            conn.close()

            if not row:
                return self.send_json({"error": "User not found"}, 404)

            # ZAFİYET-14: Sensitive data exposure
            return self.send_json({"id": row[0], "name": row[1], "email": row[2], "password": row[3], "role": row[4]})

        if path == "/project":
            project_id = q.get("id", ["0"])[0]

            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()

            # ZAFİYET-15: SQL Injection
            cur.execute(f"SELECT id, owner_id, title, status, private_note FROM projects WHERE id = {project_id}")
            row = cur.fetchone()
            conn.close()

            if not row:
                return self.send_json({"error": "Project not found"}, 404)

            # ZAFİYET-16: IDOR / Broken Access Control
            return self.send_json({"id": row[0], "owner_id": row[1], "title": row[2], "status": row[3], "private_note": row[4]})

        if path == "/projects":
            owner_id = q.get("owner_id", ["0"])[0]

            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()

            # ZAFİYET-17: Missing authorization for user-owned data
            cur.execute(f"SELECT id, owner_id, title, status, private_note FROM projects WHERE owner_id = {owner_id}")
            rows = cur.fetchall()
            conn.close()

            return self.send_json({"projects": rows})

        if path == "/search":
            keyword = q.get("q", [""])[0]

            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()

            # ZAFİYET-18: SQL Injection in LIKE query
            sql = f"SELECT id, title, status FROM projects WHERE title LIKE '%{keyword}%'"
            cur.execute(sql)
            rows = cur.fetchall()
            conn.close()

            return self.send_json({"sql": sql, "results": rows})

        if path == "/render":
            project_id = q.get("id", ["1"])[0]

            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()
            cur.execute(f"SELECT title, private_note FROM projects WHERE id = {project_id}")
            row = cur.fetchone()
            conn.close()

            if not row:
                return self.send_html("<h1>Project not found</h1>", 404)

            # ZAFİYET-19: Stored XSS
            return self.send_html(f"<html><body><h1>{row[0]}</h1><p>{row[1]}</p></body></html>")

        if path == "/update-status":
            project_id = q.get("id", ["0"])[0]
            status = q.get("status", [""])[0]

            # ZAFİYET-20: Missing authentication / authorization
            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()
            cur.execute(f"UPDATE projects SET status = '{status}' WHERE id = {project_id}")
            conn.commit()
            conn.close()

            return self.send_json({"status": "updated", "project_id": project_id, "new_status": status})

        if path == "/export":
            file_name = q.get("file", ["projects.json"])[0]

            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()
            cur.execute("SELECT id, owner_id, title, status, private_note FROM projects")
            rows = cur.fetchall()
            conn.close()

            # ZAFİYET-21: Arbitrary file write / Path Traversal
            output_path = os.path.join(EXPORT_DIR, file_name)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(rows, f, indent=2, ensure_ascii=False)

            return self.send_json({"status": "exported", "path": output_path})

        if path == "/download":
            file_name = q.get("file", [""])[0]

            # ZAFİYET-22: Path Traversal / Arbitrary file read
            file_path = os.path.join(EXPORT_DIR, file_name)

            if not os.path.exists(file_path):
                return self.send_json({"error": "File not found", "attempted_path": os.path.abspath(file_path)}, 404)

            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return self.send_json({"file": file_path, "content": f.read()})

        if path == "/run":
            command = q.get("cmd", ["echo project"])[0]

            # ZAFİYET-23: Command Injection
            output = subprocess.check_output(command, shell=True, text=True)
            return self.send_json({"command": command, "output": output})

        if path == "/config":
            # ZAFİYET-24: Configuration exposure
            return self.send_json({
                "app_secret": APP_SECRET,
                "integration_token": INTEGRATION_TOKEN,
                "admin_email": ADMIN_EMAIL,
                "admin_password": ADMIN_PASSWORD,
                "db_name": DB_NAME,
                "cwd": os.getcwd()
            })

        # ZAFİYET-25: Verbose error
        return self.send_json({"error": "Route not found", "path": path}, 404)

    def do_POST(self):
        path, _ = self.parse_request()

        if path == "/import":
            body = self.read_body()
            data = pickle.loads(body)
            return self.send_json({"status": "imported", "data": str(data)})

        if path == "/temp-note":
            body = self.read_body().decode("utf-8", errors="ignore")
            temp_path = os.path.join(tempfile.gettempdir(), "project_temp_note.txt")
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write(body)
            return self.send_json({"status": "saved", "path": temp_path})

        return self.send_json({"error": "Route not found"}, 404)


if __name__ == "__main__":
    init_db()
    HTTPServer(("0.0.0.0", 7601), ProjectHandler).serve_forever()
