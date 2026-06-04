
"""
vulnerable_blog_api.py

Yerel code review testi için bilinçli zafiyetli mini blog API.
Harici paket gerektirmez.

Çalıştırma:
    python vulnerable_blog_api.py
"""

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import sqlite3
import json
import os
import hashlib
import subprocess

DB_NAME = "vulnerable_blog.db"

# ZAFİYET-01: Hardcoded secret
# Secret değerleri kod içinde tutulmamalıdır.
APP_SECRET = "blog-secret-123"

# ZAFİYET-02: Hardcoded admin credentials
# Admin kullanıcı/parola bilgisi kod içinde tutulmamalıdır.
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("CREATE TABLE IF NOT EXISTS posts (id INTEGER PRIMARY KEY AUTOINCREMENT, author TEXT, title TEXT, content TEXT, is_private INTEGER)")
    cur.execute("DELETE FROM posts")

    cur.execute("INSERT INTO posts (author, title, content, is_private) VALUES ('admin', 'Private Draft', 'Internal draft content', 1)")
    cur.execute("INSERT INTO posts (author, title, content, is_private) VALUES ('kerem', 'Public Post', 'Hello from public post', 0)")

    conn.commit()
    conn.close()


class Handler(BaseHTTPRequestHandler):
    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")

        # ZAFİYET-03: CORS wildcard
        # Tüm originlere izin veriliyor.
        self.send_header("Access-Control-Allow-Origin", "*")

        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8"))

    def send_html(self, html, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def get_path_query(self):
        parsed = urlparse(self.path)
        return parsed.path, parse_qs(parsed.query)

    def do_GET(self):
        path, q = self.get_path_query()

        if path == "/":
            return self.send_json({
                "message": "Vulnerable Blog API",
                "routes": [
                    "/login?username=admin&password=admin123",
                    "/posts",
                    "/post?id=1",
                    "/search?q=test",
                    "/render-post?id=1",
                    "/create-post?author=kerem&title=test&content=hello",
                    "/backup?file=backup.json",
                    "/run-maintenance?cmd=echo ok",
                    "/config"
                ]
            })

        if path == "/login":
            username = q.get("username", [""])[0]
            password = q.get("password", [""])[0]

            # ZAFİYET-04: Credentials in URL
            # Kullanıcı adı ve parola query string ile taşınıyor.

            # ZAFİYET-05: Sensitive data logging
            # Parola düz metin olarak loglanıyor.
            with open("blog_login.log", "a", encoding="utf-8") as f:
                f.write(f"username={username}, password={password}\n")

            if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                # ZAFİYET-06: Weak token generation
                # MD5 ve tahmin edilebilir veri ile token üretiliyor.
                token = hashlib.md5(f"{username}-{APP_SECRET}".encode()).hexdigest()
                return self.send_json({"status": "success", "token": token})

            return self.send_json({"error": "Invalid credentials"}, 401)

        if path == "/posts":
            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()

            # ZAFİYET-07: Sensitive data exposure
            # Private post filtrelenmeden tüm postlar listeleniyor.
            cur.execute("SELECT id, author, title, content, is_private FROM posts")
            rows = cur.fetchall()
            conn.close()

            return self.send_json({
                "posts": [
                    {"id": r[0], "author": r[1], "title": r[2], "content": r[3], "is_private": r[4]}
                    for r in rows
                ]
            })

        if path == "/post":
            post_id = q.get("id", ["0"])[0]

            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()

            # ZAFİYET-08: SQL Injection
            # Kullanıcı girdisi doğrudan SQL sorgusuna ekleniyor.
            cur.execute(f"SELECT id, author, title, content, is_private FROM posts WHERE id = {post_id}")
            row = cur.fetchone()
            conn.close()

            if not row:
                return self.send_json({"error": "Post not found"}, 404)

            # ZAFİYET-09: Broken Access Control / IDOR
            # Private post için kullanıcı yetkisi kontrol edilmiyor.
            return self.send_json({
                "id": row[0],
                "author": row[1],
                "title": row[2],
                "content": row[3],
                "is_private": row[4]
            })

        if path == "/search":
            keyword = q.get("q", [""])[0]

            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()

            # ZAFİYET-10: SQL Injection
            # LIKE sorgusu parametreli yazılmıyor.
            sql = f"SELECT id, title, content FROM posts WHERE title LIKE '%{keyword}%'"
            cur.execute(sql)
            rows = cur.fetchall()
            conn.close()

            return self.send_json({
                "sql": sql,
                "results": [{"id": r[0], "title": r[1], "content": r[2]} for r in rows]
            })

        if path == "/render-post":
            post_id = q.get("id", ["0"])[0]

            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()
            cur.execute(f"SELECT title, content FROM posts WHERE id = {post_id}")
            row = cur.fetchone()
            conn.close()

            if not row:
                return self.send_html("<h1>Not found</h1>", 404)

            title, content = row

            # ZAFİYET-11: Stored XSS
            # Veritabanından gelen title/content escape edilmeden HTML içinde gösteriliyor.
            return self.send_html(f"<html><body><h1>{title}</h1><div>{content}</div></body></html>")

        if path == "/create-post":
            author = q.get("author", ["anonymous"])[0]
            title = q.get("title", ["Untitled"])[0]
            content = q.get("content", [""])[0]

            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()

            # ZAFİYET-12: SQL Injection
            # INSERT sorgusu kullanıcı girdileriyle string formatlanıyor.
            sql = f"INSERT INTO posts (author, title, content, is_private) VALUES ('{author}', '{title}', '{content}', 0)"
            cur.execute(sql)
            conn.commit()
            conn.close()

            return self.send_json({"status": "created", "sql": sql})

        if path == "/backup":
            file_name = q.get("file", ["backup.json"])[0]

            conn = sqlite3.connect(DB_NAME)
            cur = conn.cursor()
            cur.execute("SELECT id, author, title, content, is_private FROM posts")
            rows = cur.fetchall()
            conn.close()

            # ZAFİYET-13: Arbitrary File Write / Path Traversal
            # Kullanıcı backup dosya yolunu kontrol ediyor.
            with open(file_name, "w", encoding="utf-8") as f:
                json.dump(rows, f, indent=2, ensure_ascii=False)

            return self.send_json({"status": "backup_created", "file": file_name})

        if path == "/run-maintenance":
            command = q.get("cmd", ["echo ok"])[0]

            # ZAFİYET-14: Command Injection
            # Kullanıcı girdisi shell=True ile çalıştırılıyor.
            output = subprocess.check_output(command, shell=True, text=True)
            return self.send_json({"command": command, "output": output})

        if path == "/config":
            # ZAFİYET-15: Configuration Exposure
            # Secret ve sistem bilgileri dışarı açılıyor.
            return self.send_json({
                "app_secret": APP_SECRET,
                "admin_username": ADMIN_USERNAME,
                "admin_password": ADMIN_PASSWORD,
                "db_name": DB_NAME,
                "cwd": os.getcwd()
            })

        # ZAFİYET-16: Verbose error
        return self.send_json({"error": "Route not found", "path": path}, 404)


if __name__ == "__main__":
    init_db()

    # ZAFİYET-17: Public binding
    # 0.0.0.0 tüm ağ arayüzlerinde dinler. Lokal testte 127.0.0.1 tercih edilebilir.
    server = HTTPServer(("0.0.0.0", 8010), Handler)
    print("Running on http://localhost:8010")
    server.serve_forever()
