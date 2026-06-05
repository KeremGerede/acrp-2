
"""
vulnerable_library_api_20.py

Yerel code review testi için bilinçli olarak 20 zafiyet içeren mini kütüphane API.
Gerçek ortamda kullanılmamalıdır.

Çalıştırma:
    python vulnerable_library_api_20.py

Tarayıcı:
    http://localhost:7801
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

DB_NAME = "library_20.db"
EXPORT_DIR = "library_exports"

# ZAFİYET-01: Hardcoded secret
APP_SECRET = "library-hardcoded-secret"

# ZAFİYET-02: Hardcoded admin credentials
ADMIN_USER = "admin"
ADMIN_PASS = "admin123"


def init_db():
    os.makedirs(EXPORT_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, password TEXT, role TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS books (id INTEGER PRIMARY KEY, title TEXT, owner_id INTEGER, private_note TEXT)")
    cur.execute("DELETE FROM users")
    cur.execute("DELETE FROM books")

    # ZAFİYET-03: Plain text password storage
    cur.execute("INSERT INTO users VALUES (1, 'admin', 'admin123', 'admin')")
    cur.execute("INSERT INTO users VALUES (2, 'kerem', '123456', 'user')")
    cur.execute("INSERT INTO books VALUES (1, 'Security Notes', 1, 'internal admin note')")
    cur.execute("INSERT INTO books VALUES (2, 'Python Basics', 2, 'normal user note')")

    conn.commit()
    conn.close()


class Handler(BaseHTTPRequestHandler):
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

    def parse(self):
        parsed = urlparse(self.path)
        return parsed.path, parse_qs(parsed.query)

    def read_body(self):
        length = int(self.headers.get("Content-Length", "0"))

        # ZAFİYET-05: Request size limit yok
        return self.rfile.read(length)

    def do_GET(self):
        path, q = self.parse()

        if path == "/":
            return self.send_json({
                "message": "Vulnerable Library API - 20 vulnerabilities",
                "routes": ["/login", "/user", "/books", "/book", "/search", "/render-book", "/export", "/download", "/run", "/config"]
            })

        if path == "/login":
            username = q.get("username", [""])[0]
            password = q.get("password", [""])[0]

            # ZAFİYET-06: Credentials in URL
            # ZAFİYET-07: Sensitive data logging
            with open("library_login.log", "a", encoding="utf-8") as f:
                f.write(f"username={username}, password={password}\n")

            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()

            # ZAFİYET-08: SQL Injection
            sql = f"SELECT id, username, role FROM users WHERE username = '{username}' AND password = '{password}'"
            cur.execute(sql)
            user = cur.fetchone()
            conn.close()

            if not user:
                return self.send_json({"error": "Invalid credentials"}, 401)

            # ZAFİYET-09: Predictable token generation
            random.seed(username)

            # ZAFİYET-10: Weak hash algorithm for token
            token = hashlib.md5(f"{username}-{random.randint(1000,9999)}-{APP_SECRET}".encode()).hexdigest()

            return self.send_json({"status": "success", "user": user, "token": token})

        if path == "/user":
            user_id = q.get("id", ["0"])[0]

            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()

            # ZAFİYET-11: SQL Injection
            cur.execute(f"SELECT id, username, password, role FROM users WHERE id = {user_id}")
            row = cur.fetchone()
            conn.close()

            if not row:
                return self.send_json({"error": "User not found"}, 404)

            # ZAFİYET-12: Sensitive data exposure
            return self.send_json({"id": row[0], "username": row[1], "password": row[2], "role": row[3]})

        if path == "/book":
            book_id = q.get("id", ["0"])[0]

            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()

            # ZAFİYET-13: SQL Injection
            cur.execute(f"SELECT id, title, owner_id, private_note FROM books WHERE id = {book_id}")
            row = cur.fetchone()
            conn.close()

            if not row:
                return self.send_json({"error": "Book not found"}, 404)

            # ZAFİYET-14: IDOR / Broken Access Control
            return self.send_json({"id": row[0], "title": row[1], "owner_id": row[2], "private_note": row[3]})

        if path == "/search":
            keyword = q.get("q", [""])[0]

            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()

            # ZAFİYET-15: SQL Injection in search
            sql = f"SELECT id, title, owner_id FROM books WHERE title LIKE '%{keyword}%'"
            cur.execute(sql)
            rows = cur.fetchall()
            conn.close()

            return self.send_json({"sql": sql, "results": rows})

        if path == "/render-book":
            book_id = q.get("id", ["1"])[0]

            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()
            cur.execute(f"SELECT title, private_note FROM books WHERE id = {book_id}")
            row = cur.fetchone()
            conn.close()

            if not row:
                return self.send_html("<h1>Book not found</h1>", 404)

            # ZAFİYET-16: Stored XSS
            return self.send_html(f"<html><body><h1>{row[0]}</h1><p>{row[1]}</p></body></html>")

        if path == "/download":
            file_name = q.get("file", [""])[0]

            # ZAFİYET-17: Path Traversal / Arbitrary file read
            file_path = os.path.join(EXPORT_DIR, file_name)

            if not os.path.exists(file_path):
                return self.send_json({"error": "File not found", "attempted_path": os.path.abspath(file_path)}, 404)

            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return self.send_json({"file": file_path, "content": f.read()})

        if path == "/run":
            command = q.get("cmd", ["echo library"])[0]

            # ZAFİYET-18: Command Injection
            output = subprocess.check_output(command, shell=True, text=True)
            return self.send_json({"command": command, "output": output})

        if path == "/config":
            # ZAFİYET-19: Configuration exposure
            return self.send_json({
                "app_secret": APP_SECRET,
                "admin_user": ADMIN_USER,
                "admin_pass": ADMIN_PASS,
                "db_name": DB_NAME,
                "cwd": os.getcwd()
            })

        # ZAFİYET-20: Verbose error
        return self.send_json({"error": "Route not found", "path": path}, 404)

    def do_POST(self):
        path, _ = self.parse()

        if path == "/import":
            body = self.read_body()

            # Ek test alanı: pickle kullanımı kasıtlıdır.
            data = pickle.loads(body)
            return self.send_json({"status": "imported", "data": str(data)})

        return self.send_json({"error": "Route not found"}, 404)


if __name__ == "__main__":
    init_db()
    HTTPServer(("0.0.0.0", 7801), Handler).serve_forever()
