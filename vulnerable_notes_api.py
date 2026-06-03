"""
vulnerable_notes_api.py

Bu dosya yalnızca yerel test / code review agent denemesi için hazırlanmıştır.
Gerçek projede, sunucuda veya public ortamda çalıştırmayın.

Harici paket gerektirmez.

Çalıştırma:
    python vulnerable_notes_api.py

Tarayıcı:
    http://localhost:8090
"""

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import sqlite3
import json
import os
import pickle
import secrets
import subprocess

DB_NAME = "vulnerable_notes.db"

# ZAFİYET-01: Hardcoded admin token
# Admin token kod içine yazılmamalıdır. Secret manager veya environment variable kullanılmalıdır.
ADMIN_TOKEN = "admin-token-123"

# ZAFİYET-02: Güvenlik açısından zayıf varsayılan kullanıcı
# Demo kullanıcı varsayılan ve tahmin edilebilir parola ile oluşturuluyor.
DEFAULT_USER = {
    "username": "admin",
    "password": "admin"
}


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner TEXT,
            title TEXT,
            content TEXT,
            is_private INTEGER
        )
    """)

    cursor.execute("DELETE FROM notes")

    cursor.execute("""
        INSERT INTO notes (owner, title, content, is_private)
        VALUES ('admin', 'Admin Note', 'Internal admin note', 1)
    """)

    cursor.execute("""
        INSERT INTO notes (owner, title, content, is_private)
        VALUES ('kerem', 'Public Note', 'This is a public note', 0)
    """)

    conn.commit()
    conn.close()


class VulnerableNotesHandler(BaseHTTPRequestHandler):
    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")

        # ZAFİYET-03: Security header eksikliği
        # Content-Security-Policy, X-Content-Type-Options gibi headerlar yok.
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8"))

    def send_html(self, html, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def get_path_and_query(self):
        parsed = urlparse(self.path)
        return parsed.path, parse_qs(parsed.query)

    def do_GET(self):
        path, query = self.get_path_and_query()

        if path == "/":
            return self.send_json({
                "message": "Vulnerable Notes API is running",
                "routes": [
                    "/login?username=admin&password=admin",
                    "/notes?owner=kerem",
                    "/note?id=1",
                    "/render-note?id=1",
                    "/create-note?owner=kerem&title=test&content=hello",
                    "/backup?file=backup.pkl",
                    "/restore?file=backup.pkl",
                    "/export?path=notes.json",
                    "/admin/stats?token=admin-token-123",
                    "/system/check?cmd=echo ok"
                ],
                "warning": "Bu uygulama bilinçli olarak zafiyetlidir."
            })

        if path == "/login":
            username = query.get("username", [""])[0]
            password = query.get("password", [""])[0]

            # ZAFİYET-04: Credentials in URL
            # Kullanıcı adı/parola query string ile taşınıyor. Browser history ve loglara düşebilir.

            if username == DEFAULT_USER["username"] and password == DEFAULT_USER["password"]:
                # ZAFİYET-05: Zayıf session token üretimi
                # Token kullanıcı/parola gibi tahmin edilebilir verilerle oluşturuluyor.
                token = f"{username}-{password}-{secrets.randbelow(1000)}"

                return self.send_json({
                    "status": "success",
                    "token": token
                })

            return self.send_json({"error": "Invalid credentials"}, 401)

        if path == "/notes":
            owner = query.get("owner", [""])[0]

            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()

            # ZAFİYET-06: SQL Injection
            # Kullanıcı girdisi parametreli sorgu yerine doğrudan SQL içine ekleniyor.
            sql = f"SELECT id, owner, title, content, is_private FROM notes WHERE owner = '{owner}'"

            cursor.execute(sql)
            rows = cursor.fetchall()
            conn.close()

            return self.send_json({
                "query": sql,
                "notes": [
                    {
                        "id": row[0],
                        "owner": row[1],
                        "title": row[2],
                        "content": row[3],
                        "is_private": row[4]
                    }
                    for row in rows
                ]
            })

        if path == "/note":
            note_id = query.get("id", ["0"])[0]

            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()

            # ZAFİYET-07: SQL Injection
            # note_id doğrudan SQL sorgusuna ekleniyor.
            sql = f"SELECT id, owner, title, content, is_private FROM notes WHERE id = {note_id}"

            cursor.execute(sql)
            row = cursor.fetchone()
            conn.close()

            if not row:
                return self.send_json({"error": "Note not found"}, 404)

            # ZAFİYET-08: Broken Access Control / IDOR
            # Private note kontrolü ve kullanıcı yetki kontrolü yapılmadan not gösteriliyor.
            return self.send_json({
                "id": row[0],
                "owner": row[1],
                "title": row[2],
                "content": row[3],
                "is_private": row[4]
            })

        if path == "/render-note":
            note_id = query.get("id", ["0"])[0]

            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute(f"SELECT title, content FROM notes WHERE id = {note_id}")
            row = cursor.fetchone()
            conn.close()

            if not row:
                return self.send_html("<h1>Note not found</h1>", 404)

            title, content = row

            # ZAFİYET-09: Stored XSS
            # Veritabanından gelen title/content escape edilmeden HTML içinde gösteriliyor.
            html = f"""
            <html>
                <body>
                    <h1>{title}</h1>
                    <div>{content}</div>
                </body>
            </html>
            """

            return self.send_html(html)

        if path == "/create-note":
            owner = query.get("owner", ["anonymous"])[0]
            title = query.get("title", ["Untitled"])[0]
            content = query.get("content", [""])[0]

            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()

            # ZAFİYET-10: SQL Injection / Unsafe Insert
            # INSERT sorgusu kullanıcı girdileriyle string formatlanıyor.
            sql = f"""
                INSERT INTO notes (owner, title, content, is_private)
                VALUES ('{owner}', '{title}', '{content}', 0)
            """

            cursor.execute(sql)
            conn.commit()
            conn.close()

            return self.send_json({
                "status": "created",
                "sql": sql
            })

        if path == "/backup":
            filename = query.get("file", ["backup.pkl"])[0]

            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("SELECT id, owner, title, content, is_private FROM notes")
            rows = cursor.fetchall()
            conn.close()

            # ZAFİYET-11: Arbitrary File Write / Path Traversal
            # Kullanıcı backup dosya yolunu kontrol ediyor.
            with open(filename, "wb") as f:
                pickle.dump(rows, f)

            return self.send_json({
                "status": "backup_created",
                "file": filename
            })

        if path == "/restore":
            filename = query.get("file", ["backup.pkl"])[0]

            # ZAFİYET-12: Insecure Deserialization
            # pickle güvenilmeyen dosya içeriğiyle kullanılmamalıdır.
            with open(filename, "rb") as f:
                data = pickle.load(f)

            return self.send_json({
                "status": "restored_simulation",
                "items": len(data)
            })

        if path == "/export":
            export_path = query.get("path", ["notes.json"])[0]

            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("SELECT id, owner, title, content, is_private FROM notes")
            rows = cursor.fetchall()
            conn.close()

            # ZAFİYET-13: Arbitrary File Write
            # Kullanıcı export path değerini kontrol ediyor. Güvenli dizin sınırı yok.
            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(rows, f, indent=2, ensure_ascii=False)

            return self.send_json({
                "status": "exported",
                "path": export_path
            })

        if path == "/admin/stats":
            token = query.get("token", [""])[0]

            # ZAFİYET-14: Zayıf admin doğrulaması
            # Sadece query string token ile admin endpointi korunuyor.
            if token != ADMIN_TOKEN:
                return self.send_json({"error": "Unauthorized"}, 401)

            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM notes")
            count = cursor.fetchone()[0]
            conn.close()

            return self.send_json({
                "total_notes": count,
                "admin_token_used": token
            })

        if path == "/system/check":
            command = query.get("cmd", ["echo ok"])[0]

            # ZAFİYET-15: Command Injection
            # Kullanıcıdan gelen komut doğrudan shell=True ile çalıştırılıyor.
            output = subprocess.check_output(command, shell=True, text=True)

            return self.send_json({
                "command": command,
                "output": output
            })

        return self.send_json({
            # ZAFİYET-16: Verbose Error
            # Hatalı path bilgisi response içinde dışarı veriliyor.
            "error": "Route not found",
            "path": path
        }, 404)


if __name__ == "__main__":
    init_db()

    # ZAFİYET-17: Public Binding
    # 0.0.0.0 tüm ağ arayüzlerinde dinler. Lokal test için 127.0.0.1 tercih edilebilir.
    server = HTTPServer(("0.0.0.0", 8090), VulnerableNotesHandler)
    print("Vulnerable Notes API running on http://localhost:8090")
    server.serve_forever()
