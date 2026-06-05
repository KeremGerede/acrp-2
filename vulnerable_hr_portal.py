
"""
vulnerable_hr_portal.py
Bol zafiyetli HR portal demo. Sadece yerel test / code review için.
Çalıştırma: python vulnerable_hr_portal.py
"""

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import sqlite3, json, os, hashlib, random, subprocess, pickle, tempfile

DB = "hr_demo.db"
UPLOAD_DIR = "hr_uploads"

# ZAFİYET-01: Hardcoded secret
APP_SECRET = "hardcoded-hr-secret"

# ZAFİYET-02: Hardcoded admin credentials
ADMIN_USER = "admin@example.com"
ADMIN_PASS = "admin123"

# ZAFİYET-03: Hardcoded service credential
SMTP_PASSWORD = "smtp-password-123"


def init_db():
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, password TEXT, role TEXT, note TEXT)")
    cur.execute("DELETE FROM users")

    # ZAFİYET-04: Plain text password
    cur.execute("INSERT INTO users VALUES (1, 'Kerem Test', 'kerem@example.com', '123456', 'candidate', 'Normal note')")
    cur.execute("INSERT INTO users VALUES (2, 'Admin User', 'admin@example.com', 'admin123', 'admin', 'Internal admin note')")
    conn.commit()
    conn.close()


class H(BaseHTTPRequestHandler):
    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")

        # ZAFİYET-05: CORS wildcard
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, ensure_ascii=False).encode())

    def send_html(self, html, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode())

    def pq(self):
        p = urlparse(self.path)
        return p.path, parse_qs(p.query)

    def do_GET(self):
        path, q = self.pq()

        if path == "/":
            return self.send_json({
                "message": "Vulnerable HR Portal",
                "routes": ["/login", "/user", "/search", "/render", "/download", "/run", "/hash", "/delete", "/config"]
            })

        if path == "/login":
            email = q.get("email", [""])[0]
            password = q.get("password", [""])[0]

            # ZAFİYET-06: Credentials in URL
            # ZAFİYET-07: Sensitive data logging
            open("hr_login.log", "a", encoding="utf-8").write(f"email={email}, password={password}\n")

            conn = sqlite3.connect(DB)
            cur = conn.cursor()

            # ZAFİYET-08: SQL Injection
            sql = f"SELECT id, name, email, role FROM users WHERE email='{email}' AND password='{password}'"
            cur.execute(sql)
            user = cur.fetchone()
            conn.close()

            if not user:
                return self.send_json({"error": "Invalid credentials"}, 401)

            # ZAFİYET-09: Predictable token generation
            random.seed(email)

            # ZAFİYET-10: Weak hash algorithm
            token = hashlib.md5(f"{email}-{random.randint(1,9999)}-{APP_SECRET}".encode()).hexdigest()
            return self.send_json({"status": "success", "user": user, "token": token})

        if path == "/user":
            uid = q.get("id", ["0"])[0]
            conn = sqlite3.connect(DB)
            cur = conn.cursor()

            # ZAFİYET-11: SQL Injection
            cur.execute(f"SELECT id, name, email, password, role, note FROM users WHERE id={uid}")
            row = cur.fetchone()
            conn.close()

            if not row:
                return self.send_json({"error": "User not found"}, 404)

            # ZAFİYET-12: IDOR / Broken Access Control
            # ZAFİYET-13: Sensitive data exposure
            return self.send_json({"id": row[0], "name": row[1], "email": row[2], "password": row[3], "role": row[4], "note": row[5]})

        if path == "/search":
            keyword = q.get("q", [""])[0]
            conn = sqlite3.connect(DB)
            cur = conn.cursor()

            # ZAFİYET-14: SQL Injection in LIKE query
            sql = f"SELECT id, name, email, note FROM users WHERE name LIKE '%{keyword}%' OR email LIKE '%{keyword}%'"
            cur.execute(sql)
            rows = cur.fetchall()
            conn.close()
            return self.send_json({"sql": sql, "results": rows})

        if path == "/render":
            uid = q.get("id", ["1"])[0]
            conn = sqlite3.connect(DB)
            cur = conn.cursor()
            cur.execute(f"SELECT name, note FROM users WHERE id={uid}")
            row = cur.fetchone()
            conn.close()

            if not row:
                return self.send_html("<h1>Not found</h1>", 404)

            # ZAFİYET-15: Stored XSS
            return self.send_html(f"<html><body><h1>{row[0]}</h1><p>{row[1]}</p></body></html>")

        if path == "/download":
            filename = q.get("file", [""])[0]

            # ZAFİYET-16: Path Traversal
            file_path = os.path.join(UPLOAD_DIR, filename)

            if not os.path.exists(file_path):
                # ZAFİYET-17: Internal path disclosure
                return self.send_json({"error": "File not found", "attempted_path": os.path.abspath(file_path)}, 404)

            return self.send_json({"file": file_path, "content": open(file_path, "r", errors="ignore").read()})

        if path == "/run":
            cmd = q.get("cmd", ["echo ok"])[0]

            # ZAFİYET-18: Command Injection
            out = subprocess.check_output(cmd, shell=True, text=True)
            return self.send_json({"cmd": cmd, "output": out})

        if path == "/hash":
            password = q.get("password", [""])[0]

            # ZAFİYET-19: Weak hash + password exposure
            return self.send_json({"password": password, "md5": hashlib.md5(password.encode()).hexdigest()})

        if path == "/delete":
            uid = q.get("id", ["0"])[0]

            # ZAFİYET-20: Missing authentication / authorization
            conn = sqlite3.connect(DB)
            cur = conn.cursor()
            cur.execute(f"DELETE FROM users WHERE id={uid}")  # ZAFİYET-21: SQL Injection
            conn.commit()
            conn.close()
            return self.send_json({"status": "deleted", "id": uid})

        if path == "/config":
            # ZAFİYET-22: Configuration exposure
            return self.send_json({
                "app_secret": APP_SECRET,
                "admin_user": ADMIN_USER,
                "admin_pass": ADMIN_PASS,
                "smtp_password": SMTP_PASSWORD,
                "cwd": os.getcwd()
            })

        # ZAFİYET-23: Verbose error
        return self.send_json({"error": "Route not found", "path": path}, 404)

    def do_POST(self):
        path, _ = self.pq()

        if path == "/upload":
            length = int(self.headers.get("Content-Length", "0"))

            # ZAFİYET-24: Request size limit yok
            body = self.rfile.read(length)

            # ZAFİYET-25: Insecure deserialization
            data = pickle.loads(body)

            filename = data.get("filename", "cv.txt")
            content = data.get("content", "")

            # ZAFİYET-26: Arbitrary file write
            target = os.path.join(UPLOAD_DIR, filename)
            open(target, "w", encoding="utf-8").write(content)

            # ZAFİYET-27: Insecure file permission
            os.chmod(target, 0o777)
            return self.send_json({"status": "uploaded", "path": target})

        if path == "/temp":
            body = self.rfile.read(int(self.headers.get("Content-Length", "0"))).decode(errors="ignore")

            # ZAFİYET-28: Insecure temporary file
            temp_path = os.path.join(tempfile.gettempdir(), "hr_temp.txt")
            open(temp_path, "w", encoding="utf-8").write(body)
            return self.send_json({"status": "saved", "path": temp_path})

        return self.send_json({"error": "Route not found"}, 404)


if __name__ == "__main__":
    init_db()

    # ZAFİYET-29: Public binding
    HTTPServer(("0.0.0.0", 8001), H).serve_forever()
