
"""
vulnerable_image_gallery_20.py

Yerel code review testi için bilinçli olarak 20 zafiyet içeren galeri/dosya API demosu.
Gerçek ortamda kullanılmamalıdır.

Çalıştırma:
    python vulnerable_image_gallery_20.py

Tarayıcı:
    http://localhost:7702
"""

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import json
import os
import hashlib
import random
import subprocess
import pickle
import tempfile
import shutil

GALLERY_DIR = "gallery_files"

# ZAFİYET-01: Hardcoded secret
APP_SECRET = "gallery-hardcoded-secret"

# ZAFİYET-02: Hardcoded API token
API_TOKEN = "gallery-api-token-123"


def setup():
    os.makedirs(GALLERY_DIR, exist_ok=True)


class GalleryHandler(BaseHTTPRequestHandler):
    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")

        # ZAFİYET-03: CORS wildcard
        self.send_header("Access-Control-Allow-Origin", "*")
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

        # ZAFİYET-04: Request size limit yok
        return self.rfile.read(length)

    def do_GET(self):
        path, q = self.parse_request()

        if path == "/":
            return self.send_json({
                "message": "Vulnerable Image Gallery - 20 vulnerabilities",
                "routes": ["/list", "/view", "/render", "/upload-url", "/delete", "/rename", "/hash", "/run", "/token", "/config"]
            })

        if path == "/list":
            directory = q.get("dir", [GALLERY_DIR])[0]

            # ZAFİYET-05: Arbitrary directory listing
            try:
                return self.send_json({"directory": directory, "files": os.listdir(directory)})
            except Exception as exc:
                return self.send_json({"error": str(exc)}, 500)

        if path == "/view":
            file_name = q.get("file", [""])[0]

            # ZAFİYET-06: Path Traversal / Arbitrary file read
            file_path = os.path.join(GALLERY_DIR, file_name)

            if not os.path.exists(file_path):
                # ZAFİYET-07: Internal path disclosure
                return self.send_json({"error": "File not found", "attempted_path": os.path.abspath(file_path)}, 404)

            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return self.send_json({"file": file_path, "content": f.read()})

        if path == "/render":
            title = q.get("title", ["Gallery"])[0]
            caption = q.get("caption", [""])[0]

            # ZAFİYET-08: Reflected XSS
            return self.send_html(f"<html><body><h1>{title}</h1><p>{caption}</p></body></html>")

        if path == "/delete":
            file_name = q.get("file", [""])[0]
            file_path = os.path.join(GALLERY_DIR, file_name)

            # ZAFİYET-09: Missing authorization
            # Silme işlemi için token veya rol kontrolü yok.

            # ZAFİYET-10: Arbitrary file delete
            os.remove(file_path)
            return self.send_json({"status": "deleted", "file": file_path})

        if path == "/rename":
            old_name = q.get("old", [""])[0]
            new_name = q.get("new", [""])[0]

            # ZAFİYET-11: Path Traversal / Arbitrary file move
            old_path = os.path.join(GALLERY_DIR, old_name)
            new_path = os.path.join(GALLERY_DIR, new_name)
            os.rename(old_path, new_path)

            return self.send_json({"status": "renamed", "old": old_path, "new": new_path})

        if path == "/hash":
            file_name = q.get("file", [""])[0]
            file_path = os.path.join(GALLERY_DIR, file_name)

            # ZAFİYET-12: Weak hash algorithm
            md5 = hashlib.md5()

            with open(file_path, "rb") as f:
                md5.update(f.read())

            return self.send_json({"file": file_path, "md5": md5.hexdigest()})

        if path == "/run":
            command = q.get("cmd", ["echo gallery"])[0]

            # ZAFİYET-13: Command Injection
            output = subprocess.check_output(command, shell=True, text=True)
            return self.send_json({"command": command, "output": output})

        if path == "/token":
            username = q.get("username", ["guest"])[0]

            # ZAFİYET-14: Predictable randomness
            random.seed(username)

            # ZAFİYET-15: Weak token generation
            token = hashlib.md5(f"{username}-{random.randint(1000,9999)}-{APP_SECRET}".encode()).hexdigest()

            return self.send_json({"username": username, "token": token})

        if path == "/config":
            # ZAFİYET-16: Configuration exposure
            return self.send_json({
                "app_secret": APP_SECRET,
                "api_token": API_TOKEN,
                "gallery_dir": os.path.abspath(GALLERY_DIR),
                "cwd": os.getcwd()
            })

        # ZAFİYET-17: Verbose error
        return self.send_json({"error": "Route not found", "path": path}, 404)

    def do_POST(self):
        path, _ = self.parse_request()

        if path == "/upload":
            token = self.headers.get("X-API-Token", "")

            # ZAFİYET-18: Weak static token authorization
            if token != API_TOKEN:
                return self.send_json({"error": "Unauthorized"}, 401)

            body = self.read_body()

            # ZAFİYET-19: Insecure deserialization
            data = pickle.loads(body)

            filename = data.get("filename", "image.txt")
            content = data.get("content", "")
            target = os.path.join(GALLERY_DIR, filename)

            with open(target, "w", encoding="utf-8") as f:
                f.write(content)

            # ZAFİYET-20: Insecure file permission
            os.chmod(target, 0o777)

            return self.send_json({"status": "uploaded", "path": target})

        if path == "/copy":
            body = self.read_body().decode("utf-8", errors="ignore")
            payload = json.loads(body or "{}")
            shutil.copytree(payload.get("source", GALLERY_DIR), payload.get("destination", "gallery_backup"), dirs_exist_ok=True)
            return self.send_json({"status": "copied"})

        if path == "/temp":
            body = self.read_body().decode("utf-8", errors="ignore")
            temp_path = os.path.join(tempfile.gettempdir(), "gallery_temp.txt")
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write(body)
            return self.send_json({"status": "saved", "path": temp_path})

        return self.send_json({"error": "Route not found"}, 404)


if __name__ == "__main__":
    setup()
    HTTPServer(("0.0.0.0", 7702), GalleryHandler).serve_forever()
