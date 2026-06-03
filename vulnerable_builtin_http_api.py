"""
vulnerable_builtin_http_api.py

Bu dosya yalnızca yerel test / code review agent denemesi için hazırlanmıştır.
Harici paket gerektirmez. Sadece Python standart kütüphanesiyle çalışır.

Çalıştırma:
    python vulnerable_builtin_http_api.py

Sonra:
    http://localhost:8080
"""

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import json
import os
import hashlib
import subprocess
import base64

# ZAFİYET-01: Hardcoded secret
# Secret değerleri kod içine yazılmamalıdır.
API_SECRET = "python-http-hardcoded-secret"

# ZAFİYET-02: Plain text password
# Parolalar düz metin saklanıyor. Gerçek sistemde güçlü hash kullanılmalıdır.
USERS = [
    {
        "id": 1,
        "username": "admin",
        "password": "admin123",
        "role": "admin",
        "api_key": "ADMIN-API-KEY-123"
    },
    {
        "id": 2,
        "username": "kerem",
        "password": "123456",
        "role": "user",
        "api_key": "USER-API-KEY-456"
    }
]


class VulnerableHandler(BaseHTTPRequestHandler):
    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")

        # ZAFİYET-03: Security Header eksikliği
        # X-Content-Type-Options, Content-Security-Policy gibi headerlar yok.
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8"))

    def send_html(self, html, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def get_query(self):
        parsed = urlparse(self.path)
        return parsed.path, parse_qs(parsed.query)

    def do_GET(self):
        path, query = self.get_query()

        if path == "/":
            return self.send_json({
                "message": "Vulnerable built-in Python HTTP API is running",
                "routes": [
                    "/login?username=admin&password=admin123",
                    "/profile?id=1",
                    "/hello?name=Kerem",
                    "/read-file?file=notes.txt",
                    "/run?cmd=echo hello",
                    "/hash?password=123456",
                    "/config"
                ],
                "warning": "Bu uygulama bilinçli olarak zafiyetlidir."
            })

        if path == "/login":
            username = query.get("username", [""])[0]
            password = query.get("password", [""])[0]

            # ZAFİYET-04: Credentials in URL
            # Kullanıcı adı/parola GET query içinde taşınıyor. Loglarda ve browser history'de kalabilir.

            # ZAFİYET-05: Sensitive Data Logging
            # Parola log dosyasına yazılıyor.
            with open("http_login.log", "a", encoding="utf-8") as f:
                f.write(f"username={username}, password={password}\n")

            user = next(
                (u for u in USERS if u["username"] == username and u["password"] == password),
                None
            )

            if not user:
                return self.send_json({"error": "Invalid credentials"}, 401)

            # ZAFİYET-06: Zayıf token üretimi
            # Token sadece base64 ile encode ediliyor, gerçek imza/doğrulama yok.
            token_data = f"{user['id']}:{user['username']}:{user['role']}"
            token = base64.b64encode(token_data.encode()).decode()

            return self.send_json({
                "status": "success",
                "token": token,

                # ZAFİYET-07: Sensitive Data Exposure
                # API key response içinde dönülüyor.
                "api_key": user["api_key"]
            })

        if path == "/profile":
            user_id = int(query.get("id", ["0"])[0])

            # ZAFİYET-08: Broken Access Control / IDOR
            # Token veya kullanıcı yetkisi kontrol edilmeden istenen profil gösteriliyor.
            user = next((u for u in USERS if u["id"] == user_id), None)

            if not user:
                return self.send_json({"error": "User not found"}, 404)

            return self.send_json({
                "id": user["id"],
                "username": user["username"],
                "role": user["role"],

                # ZAFİYET-09: Sensitive Data Exposure
                # Hassas API key kullanıcıya gösteriliyor.
                "api_key": user["api_key"]
            })

        if path == "/hello":
            name = query.get("name", ["Guest"])[0]

            # ZAFİYET-10: Reflected XSS
            # Kullanıcı girdisi HTML içine escape edilmeden basılıyor.
            html = f"""
            <html>
                <body>
                    <h1>Hello {name}</h1>
                    <p>This endpoint is intentionally vulnerable.</p>
                </body>
            </html>
            """

            return self.send_html(html)

        if path == "/read-file":
            file_name = query.get("file", ["notes.txt"])[0]

            # ZAFİYET-11: Path Traversal / Arbitrary File Read
            # Kullanıcı dosya yolunu kontrol ediyor. Base directory kontrolü yok.
            file_path = os.path.join(os.getcwd(), file_name)

            if not os.path.exists(file_path):
                return self.send_json({
                    "error": "File not found",

                    # ZAFİYET-12: Internal Path Disclosure
                    # Sunucu içindeki path kullanıcıya gösteriliyor.
                    "attempted_path": file_path
                }, 404)

            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            return self.send_json({
                "file": file_path,
                "content": content
            })

        if path == "/run":
            command = query.get("cmd", ["echo hello"])[0]

            # ZAFİYET-13: Command Injection
            # Kullanıcıdan gelen komut doğrudan shell=True ile çalıştırılıyor.
            output = subprocess.check_output(command, shell=True, text=True)

            return self.send_json({
                "command": command,
                "output": output
            })

        if path == "/hash":
            password = query.get("password", [""])[0]

            # ZAFİYET-14: Weak Cryptographic Hash
            # MD5 güvenlik amaçlı kullanılmamalıdır.
            md5_hash = hashlib.md5(password.encode()).hexdigest()

            return self.send_json({
                # ZAFİYET-15: Sensitive Data Exposure
                # Parola response içinde döndürülüyor.
                "password": password,
                "md5_hash": md5_hash
            })

        if path == "/config":
            # ZAFİYET-16: Configuration Exposure
            # Secret ve sistem bilgileri dışarı açılıyor.
            return self.send_json({
                "api_secret": API_SECRET,
                "current_directory": os.getcwd(),
                "python_path": os.environ.get("PYTHONPATH", ""),
                "environment": os.environ.get("ENV", "development")
            })

        # ZAFİYET-17: Verbose Error
        # Hatalı route için path bilgisi dışarı veriliyor.
        return self.send_json({
            "error": "Route not found",
            "path": path
        }, 404)


if __name__ == "__main__":
    # ZAFİYET-18: Public Binding
    # 0.0.0.0 tüm ağ arayüzlerinde dinler. Lokal test için 127.0.0.1 tercih edilebilir.
    server = HTTPServer(("0.0.0.0", 8080), VulnerableHandler)
    print("Vulnerable HTTP API running on http://localhost:8080")
    server.serve_forever()
