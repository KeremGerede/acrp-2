"""
vulnerable_file_upload_api.py

Bu dosya yalnızca yerel test / code review agent denemesi için hazırlanmıştır.
Gerçek projede, sunucuda veya public ortamda çalıştırmayın.

Harici paket gerektirmez.

Çalıştırma:
    python vulnerable_file_upload_api.py

Tarayıcı:
    http://localhost:8070
"""

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import os
import json
import base64
import urllib.request
import tempfile
import hashlib
import subprocess

UPLOAD_DIR = "uploads"

# ZAFİYET-01: Hardcoded API token
# Token/secret değerleri kod içinde tutulmamalıdır.
API_TOKEN = "upload-api-token-123"

# ZAFİYET-02: Güvensiz dosya uzantısı listesi
# Executable/script dosyalarının yüklenmesine izin veriliyor.
ALLOWED_EXTENSIONS = [".txt", ".json", ".py", ".php", ".sh", ".exe"]


def ensure_upload_dir():
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)


class VulnerableUploadHandler(BaseHTTPRequestHandler):
    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")

        # ZAFİYET-03: CORS wildcard
        # Her origin'e izin veriliyor. Gerçek sistemde kontrollü origin listesi kullanılmalıdır.
        self.send_header("Access-Control-Allow-Origin", "*")

        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8"))

    def get_path_and_query(self):
        parsed = urlparse(self.path)
        return parsed.path, parse_qs(parsed.query)

    def read_body_json(self):
        length = int(self.headers.get("Content-Length", "0"))

        # ZAFİYET-04: Request size limit yok
        # Çok büyük body gönderilerek memory tüketimi / DoS riski oluşturulabilir.
        raw_body = self.rfile.read(length)

        try:
            return json.loads(raw_body.decode("utf-8"))
        except Exception:
            return {}

    def do_GET(self):
        path, query = self.get_path_and_query()

        if path == "/":
            return self.send_json({
                "message": "Vulnerable File Upload API is running",
                "routes": [
                    "POST /upload",
                    "GET /download?file=test.txt",
                    "GET /list?dir=uploads",
                    "GET /fetch-url?url=http://example.com",
                    "GET /checksum?file=uploads/test.txt",
                    "GET /scan?file=uploads/test.txt",
                    "GET /config"
                ],
                "warning": "Bu uygulama bilinçli olarak zafiyetlidir."
            })

        if path == "/download":
            filename = query.get("file", [""])[0]

            # ZAFİYET-05: Path Traversal
            # Kullanıcı dosya yolunu kontrol ediyor. uploads dışına çıkılabilir.
            file_path = os.path.join(UPLOAD_DIR, filename)

            if not os.path.exists(file_path):
                return self.send_json({
                    "error": "File not found",

                    # ZAFİYET-06: Internal Path Disclosure
                    # Sunucu içindeki gerçek path response içinde gösteriliyor.
                    "attempted_path": os.path.abspath(file_path)
                }, 404)

            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            return self.send_json({
                "file": file_path,
                "content": content
            })

        if path == "/list":
            directory = query.get("dir", [UPLOAD_DIR])[0]

            # ZAFİYET-07: Arbitrary Directory Listing
            # Kullanıcı istediği dizini listeleyebiliyor.
            try:
                files = os.listdir(directory)
                return self.send_json({
                    "directory": directory,
                    "files": files
                })
            except Exception as exc:
                return self.send_json({
                    "error": "Directory cannot be listed",
                    "detail": str(exc)
                }, 500)

        if path == "/fetch-url":
            target_url = query.get("url", [""])[0]

            # ZAFİYET-08: SSRF
            # Kullanıcı tarafından verilen URL sunucu tarafından fetch ediliyor.
            # Internal metadata servisleri veya private network hedef alınabilir.
            try:
                with urllib.request.urlopen(target_url, timeout=3) as response:
                    data = response.read(5000).decode("utf-8", errors="ignore")

                return self.send_json({
                    "url": target_url,
                    "preview": data
                })
            except Exception as exc:
                return self.send_json({
                    "error": "Fetch failed",
                    "detail": str(exc)
                }, 500)

        if path == "/checksum":
            file_name = query.get("file", [""])[0]

            # ZAFİYET-09: Arbitrary File Read
            # Checksum için herhangi bir dosya okunabiliyor.
            if not os.path.exists(file_name):
                return self.send_json({"error": "File not found"}, 404)

            with open(file_name, "rb") as f:
                content = f.read()

            # ZAFİYET-10: Weak Hash Algorithm
            # MD5 güvenlik amaçlı bütünlük kontrolü için uygun değildir.
            md5_hash = hashlib.md5(content).hexdigest()

            return self.send_json({
                "file": file_name,
                "md5": md5_hash
            })

        if path == "/scan":
            file_name = query.get("file", [""])[0]

            # ZAFİYET-11: Command Injection
            # Kullanıcı dosya adını shell komutuna doğrudan ekliyor.
            # Güvenli yaklaşımda shell kullanılmamalı, parametreler liste olarak verilmelidir.
            command = f"echo scanning {file_name}"
            output = subprocess.check_output(command, shell=True, text=True)

            return self.send_json({
                "command": command,
                "output": output
            })

        if path == "/config":
            # ZAFİYET-12: Configuration Exposure
            # Token ve sistem bilgileri dışarı açılıyor.
            return self.send_json({
                "api_token": API_TOKEN,
                "upload_dir": os.path.abspath(UPLOAD_DIR),
                "temp_dir": tempfile.gettempdir(),
                "cwd": os.getcwd()
            })

        return self.send_json({
            # ZAFİYET-13: Verbose Error
            # Hatalı route bilgisi kullanıcıya gösteriliyor.
            "error": "Route not found",
            "path": path
        }, 404)

    def do_POST(self):
        path, query = self.get_path_and_query()

        if path == "/upload":
            body = self.read_body_json()

            token = self.headers.get("X-API-Token", "")

            # ZAFİYET-14: Zayıf API token kontrolü
            # Tek statik token ile yetkilendirme yapılıyor. Kullanıcı/rol bazlı kontrol yok.
            if token != API_TOKEN:
                return self.send_json({"error": "Unauthorized"}, 401)

            filename = body.get("filename", "uploaded.txt")
            encoded_content = body.get("content_base64", "")

            _, extension = os.path.splitext(filename)

            # ZAFİYET-15: Güvensiz dosya türlerine izin verme
            # .py, .php, .sh gibi çalıştırılabilir dosya türlerine izin veriliyor.
            if extension not in ALLOWED_EXTENSIONS:
                return self.send_json({"error": "Extension not allowed"}, 400)

            try:
                content = base64.b64decode(encoded_content)
            except Exception:
                return self.send_json({"error": "Invalid base64 content"}, 400)

            # ZAFİYET-16: Path Traversal / Arbitrary File Write
            # filename sanitize edilmeden path'e ekleniyor. ../ ile uploads dışına yazılabilir.
            target_path = os.path.join(UPLOAD_DIR, filename)

            with open(target_path, "wb") as f:
                f.write(content)

            # ZAFİYET-17: Insecure File Permission
            # Yüklenen dosyaya fazla geniş izin veriliyor.
            os.chmod(target_path, 0o777)

            return self.send_json({
                "status": "uploaded",
                "path": target_path,
                "size": len(content)
            })

        return self.send_json({"error": "Route not found"}, 404)


if __name__ == "__main__":
    ensure_upload_dir()

    # ZAFİYET-18: Public Binding
    # 0.0.0.0 tüm ağ arayüzlerinde dinler. Lokal test için 127.0.0.1 tercih edilebilir.
    server = HTTPServer(("0.0.0.0", 8070), VulnerableUploadHandler)
    print("Vulnerable File Upload API running on http://localhost:8070")
    server.serve_forever()
