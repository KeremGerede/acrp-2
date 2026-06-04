"""
vulnerable_auth_session_api.py

Yerel code review testi için bilinçli zafiyetli auth/session API.
Harici paket gerektirmez.

Çalıştırma:
    python vulnerable_auth_session_api.py
"""

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import json
import sqlite3
import hashlib
import random
import time
import os

DB_NAME = "vulnerable_auth.db"

# ZAFİYET-01: Hardcoded secret
# Secret/token değerleri kod içine yazılmamalıdır.
SESSION_SECRET = "auth-session-secret-123"

# ZAFİYET-02: Varsayılan admin bilgisi
# Tahmin edilebilir admin hesabı gerçek sistemlerde güvenlik riski oluşturur.
DEFAULT_ADMIN = {
    "username": "admin",
    "password": "admin123"
}


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, password TEXT, role TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS sessions (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, token TEXT, created_at INTEGER)")

    cur.execute("DELETE FROM users")
    cur.execute("DELETE FROM sessions")

    # ZAFİYET-03: Plain text password
    # Parolalar düz metin saklanıyor. bcrypt/argon2 gibi güçlü algoritmalar kullanılmalıdır.
    cur.execute("INSERT INTO users (username, password, role) VALUES ('admin', 'admin123', 'admin')")
    cur.execute("INSERT INTO users (username, password, role) VALUES ('kerem', '123456', 'user')")

    conn.commit()
    conn.close()


def create_session(username):
    # ZAFİYET-04: Predictable token generation
    # random.seed ile tahmin edilebilir token oluşturuluyor. secrets modülü tercih edilmelidir.
    random.seed(username)
    token_raw = f"{username}-{random.randint(1000, 9999)}-{SESSION_SECRET}"
    token = hashlib.md5(token_raw.encode()).hexdigest()  # ZAFİYET-05: Weak hash algorithm

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(f"INSERT INTO sessions (username, token, created_at) VALUES ('{username}', '{token}', {int(time.time())})")
    conn.commit()
    conn.close()

    return token


class Handler(BaseHTTPRequestHandler):
    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")

        # ZAFİYET-06: Security header eksikliği
        # CSP, X-Content-Type-Options gibi headerlar bulunmuyor.
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8"))

    def get_path_query(self):
        parsed = urlparse(self.path)
        return parsed.path, parse_qs(parsed.query)

    def do_GET(self):
        path, q = self.get_path_query()

        if path == "/":
            return self.send_json({
                "message": "Vulnerable Auth Session API",
                "routes": [
                    "/login?username=admin&password=admin123",
                    "/me?token=...",
                    "/sessions",
                    "/change-password?username=kerem&new_password=123",
                    "/admin/user?id=1",
                    "/config"
                ]
            })

        if path == "/login":
            username = q.get("username", [""])[0]
            password = q.get("password", [""])[0]

            # ZAFİYET-07: Credentials in URL
            # Kullanıcı adı/parola query string içinde taşınıyor.

            # ZAFİYET-08: Sensitive data logging
            # Parola log dosyasına yazılıyor.
            with open("auth_login.log", "a", encoding="utf-8") as f:
                f.write(f"username={username}, password={password}\n")

            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()

            # ZAFİYET-09: SQL Injection
            # Kullanıcı girdileri doğrudan SQL sorgusuna ekleniyor.
            sql = f"SELECT username, role FROM users WHERE username = '{username}' AND password = '{password}'"
            cur.execute(sql)
            user = cur.fetchone()
            conn.close()

            if not user:
                return self.send_json({"error": "Invalid credentials"}, 401)

            token = create_session(user[0])

            return self.send_json({
                "status": "success",
                "username": user[0],
                "role": user[1],
                "token": token
            })

        if path == "/me":
            token = q.get("token", [""])[0]

            # ZAFİYET-10: Token in URL
            # Session token query string içinde taşınıyor.
            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()

            # ZAFİYET-11: SQL Injection
            # Token doğrudan SQL içine ekleniyor.
            cur.execute(f"SELECT username FROM sessions WHERE token = '{token}'")
            session = cur.fetchone()

            if not session:
                conn.close()
                return self.send_json({"error": "Invalid session"}, 401)

            cur.execute(f"SELECT id, username, role, password FROM users WHERE username = '{session[0]}'")
            user = cur.fetchone()
            conn.close()

            return self.send_json({
                "id": user[0],
                "username": user[1],
                "role": user[2],

                # ZAFİYET-12: Sensitive data exposure
                # Kullanıcı parolası response içinde dönülüyor.
                "password": user[3]
            })

        if path == "/sessions":
            # ZAFİYET-13: Missing authentication
            # Tüm session kayıtları kimlik doğrulama olmadan listeleniyor.
            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()
            cur.execute("SELECT username, token, created_at FROM sessions")
            rows = cur.fetchall()
            conn.close()

            return self.send_json({
                "sessions": [{"username": r[0], "token": r[1], "created_at": r[2]} for r in rows]
            })

        if path == "/change-password":
            username = q.get("username", [""])[0]
            new_password = q.get("new_password", [""])[0]

            # ZAFİYET-14: Missing authorization
            # Parola değiştirme için mevcut parola, token veya rol kontrolü yok.
            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()

            # ZAFİYET-15: SQL Injection
            cur.execute(f"UPDATE users SET password = '{new_password}' WHERE username = '{username}'")
            conn.commit()
            conn.close()

            return self.send_json({"status": "password_changed", "username": username})

        if path == "/admin/user":
            user_id = q.get("id", ["0"])[0]

            # ZAFİYET-16: Broken Access Control / IDOR
            # Admin endpointi kimlik doğrulama olmadan kullanıcı detaylarını gösteriyor.
            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()
            cur.execute(f"SELECT id, username, password, role FROM users WHERE id = {user_id}")
            row = cur.fetchone()
            conn.close()

            if not row:
                return self.send_json({"error": "User not found"}, 404)

            return self.send_json({
                "id": row[0],
                "username": row[1],
                "password": row[2],
                "role": row[3]
            })

        if path == "/config":
            # ZAFİYET-17: Configuration exposure
            return self.send_json({
                "session_secret": SESSION_SECRET,
                "db_name": DB_NAME,
                "cwd": os.getcwd()
            })

        # ZAFİYET-18: Verbose error
        return self.send_json({"error": "Route not found", "path": path}, 404)


if __name__ == "__main__":
    init_db()

    # ZAFİYET-19: Public binding
    server = HTTPServer(("0.0.0.0", 8030), Handler)
    print("Running on http://localhost:8030")
    server.serve_forever()
