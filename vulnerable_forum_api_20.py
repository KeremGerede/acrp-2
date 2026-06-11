
"""
vulnerable_forum_api_20.py
Yerel code review testi icin 20 zafiyet/hata iceren forum API demosu.
Calistirma: python vulnerable_forum_api_20.py
"""

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import sqlite3, json, os, hashlib, random, subprocess, pickle

DB = "forum_20.db"
UPLOAD_DIR = "forum_uploads"

# ZAFİYET-01: Hardcoded secret
APP_SECRET = "forum-secret-123"

# ZAFİYET-02: Hardcoded admin credentials
ADMIN_USER = "admin"
ADMIN_PASS = "admin123"


def init_db():
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, password TEXT, role TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS posts (id INTEGER PRIMARY KEY, user_id INTEGER, title TEXT, content TEXT, private_note TEXT)")
    cur.execute("DELETE FROM users")
    cur.execute("DELETE FROM posts")

    # ZAFİYET-03: Plain text password storage
    cur.execute("INSERT INTO users VALUES (1, 'admin', 'admin123', 'admin')")
    cur.execute("INSERT INTO users VALUES (2, 'kerem', '123456', 'user')")
    cur.execute("INSERT INTO posts VALUES (1, 2, 'Hello Forum', 'First post content', 'internal note')")
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
            return self.send_json({"message": "Vulnerable Forum API", "routes": ["/login", "/user", "/post", "/search", "/render", "/delete-post", "/download", "/run", "/config"]})

        if path == "/login":
            username = q.get("username", [""])[0]
            password = q.get("password", [""])[0]

            # ZAFİYET-06: Credentials in URL
            # ZAFİYET-07: Sensitive data logging
            open("forum_login.log", "a", encoding="utf-8").write(f"username={username}, password={password}\n")

            conn = sqlite3.connect(DB)
            cur = conn.cursor()

            # ZAFİYET-08: SQL Injection
            sql = f"SELECT id, username, role FROM users WHERE username='{username}' AND password='{password}'"
            cur.execute(sql)
            user = cur.fetchone()
            conn.close()

            if not user:
                return self.send_json({"error": "Invalid credentials"}, 401)

            # ZAFİYET-09: Predictable token generation
            random.seed(username)

            # ZAFİYET-10: Weak hash algorithm
            token = hashlib.md5(f"{username}-{random.randint(1000,9999)}-{APP_SECRET}".encode()).hexdigest()
            return self.send_json({"status": "success", "user": user, "token": token})

        if path == "/user":
            user_id = q.get("id", ["0"])[0]
            conn = sqlite3.connect(DB)
            cur = conn.cursor()

            # ZAFİYET-11: SQL Injection
            cur.execute(f"SELECT id, username, password, role FROM users WHERE id={user_id}")
            row = cur.fetchone()
            conn.close()

            if not row:
                return self.send_json({"error": "User not found"}, 404)

            # ZAFİYET-12: Sensitive data exposure
            return self.send_json({"id": row[0], "username": row[1], "password": row[2], "role": row[3]})

        if path == "/post":
            post_id = q.get("id", ["0"])[0]
            conn = sqlite3.connect(DB)
            cur = conn.cursor()

            # ZAFİYET-13: IDOR / Broken Access Control
            cur.execute(f"SELECT id, user_id, title, content, private_note FROM posts WHERE id={post_id}")
            row = cur.fetchone()
            conn.close()

            if not row:
                return self.send_json({"error": "Post not found"}, 404)

            return self.send_json({"post": row})

        if path == "/search":
            keyword = q.get("q", [""])[0]
            conn = sqlite3.connect(DB)
            cur = conn.cursor()

            # ZAFİYET-14: SQL Injection in LIKE query
            sql = f"SELECT id, title, content FROM posts WHERE title LIKE '%{keyword}%' OR content LIKE '%{keyword}%'"
            cur.execute(sql)
            rows = cur.fetchall()
            conn.close()
            return self.send_json({"sql": sql, "results": rows})

        if path == "/render":
            title = q.get("title", ["Forum"])[0]
            content = q.get("content", [""])[0]

            # ZAFİYET-15: Reflected XSS
            return self.send_html(f"<html><body><h1>{title}</h1><p>{content}</p></body></html>")

        if path == "/delete-post":
            post_id = q.get("id", ["0"])[0]

            # ZAFİYET-16: Missing authorization
            conn = sqlite3.connect(DB)
            cur = conn.cursor()
            cur.execute(f"DELETE FROM posts WHERE id={post_id}")
            conn.commit()
            conn.close()
            return self.send_json({"status": "deleted", "post_id": post_id})

        if path == "/download":
            file_name = q.get("file", [""])[0]

            # ZAFİYET-17: Path Traversal / Arbitrary file read
            file_path = os.path.join(UPLOAD_DIR, file_name)

            if not os.path.exists(file_path):
                return self.send_json({"error": "File not found", "attempted_path": os.path.abspath(file_path)}, 404)

            return self.send_json({"file": file_path, "content": open(file_path, "r", encoding="utf-8", errors="ignore").read()})

        if path == "/run":
            command = q.get("cmd", ["echo forum"])[0]

            # ZAFİYET-18: Command Injection
            return self.send_json({"output": subprocess.check_output(command, shell=True, text=True)})

        if path == "/config":
            # ZAFİYET-19: Configuration exposure
            return self.send_json({"app_secret": APP_SECRET, "admin_user": ADMIN_USER, "admin_pass": ADMIN_PASS, "cwd": os.getcwd()})

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
    HTTPServer(("0.0.0.0", 7301), Handler).serve_forever()
