"""
vulnerable_api_gateway.py

Yerel code review testi için bilinçli zafiyetli API gateway simülasyonu.
Harici paket gerektirmez.

Çalıştırma:
    python vulnerable_api_gateway.py
"""

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import json
import time
import os
import hashlib
import subprocess

# ZAFİYET-01: Hardcoded gateway secret
# Secret/token değerleri kod içinde tutulmamalıdır.
GATEWAY_SECRET = "gateway-secret-123"

# ZAFİYET-02: Hardcoded servis tokenları
# Servisler arası tokenlar secret manager veya environment üzerinden yönetilmelidir.
SERVICE_TOKENS = {
    "billing": "billing-token-123",
    "users": "users-token-456",
    "admin": "admin-token-789"
}

REQUEST_LOG = "gateway_requests.log"


class Handler(BaseHTTPRequestHandler):
    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")

        # ZAFİYET-03: CORS wildcard
        # Tüm originlere izin veriliyor.
        self.send_header("Access-Control-Allow-Origin", "*")

        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8"))

    def get_path_query(self):
        parsed = urlparse(self.path)
        return parsed.path, parse_qs(parsed.query)

    def do_GET(self):
        path, q = self.get_path_query()

        if path == "/":
            return self.send_json({
                "message": "Vulnerable API Gateway",
                "routes": [
                    "/proxy?service=users&path=/profile",
                    "/token?service=admin",
                    "/logs",
                    "/debug/run?cmd=echo ok",
                    "/hash?value=test",
                    "/config"
                ]
            })

        if path == "/proxy":
            service = q.get("service", [""])[0]
            target_path = q.get("path", [""])[0]
            token = q.get("token", [""])[0]

            # ZAFİYET-04: Sensitive data logging
            # Token ve hedef path log dosyasına düz şekilde yazılıyor.
            with open(REQUEST_LOG, "a", encoding="utf-8") as f:
                f.write(f"{int(time.time())} service={service} path={target_path} token={token}\n")

            # ZAFİYET-05: Authentication bypass
            # Token boş olsa bile istek kabul ediliyor.
            if token and SERVICE_TOKENS.get(service) != token:
                return self.send_json({"error": "Invalid token"}, 401)

            # ZAFİYET-06: Open redirect / unsafe proxy logic
            # Kullanıcı hedef servis/path değerini doğrudan kontrol ediyor.
            return self.send_json({
                "status": "proxied",
                "service": service,
                "path": target_path
            })

        if path == "/token":
            service = q.get("service", [""])[0]

            # ZAFİYET-07: Sensitive token exposure
            # Servis tokenı kimlik doğrulama olmadan response içinde veriliyor.
            return self.send_json({
                "service": service,
                "token": SERVICE_TOKENS.get(service, "unknown")
            })

        if path == "/logs":
            # ZAFİYET-08: Missing authentication
            # Gateway logları herkes tarafından okunabiliyor.
            if not os.path.exists(REQUEST_LOG):
                return self.send_json({"logs": ""})

            with open(REQUEST_LOG, "r", encoding="utf-8", errors="ignore") as f:
                return self.send_json({"logs": f.read()})

        if path == "/debug/run":
            command = q.get("cmd", ["echo ok"])[0]

            # ZAFİYET-09: Command Injection
            # Kullanıcı girdisi shell=True ile doğrudan çalıştırılıyor.
            output = subprocess.check_output(command, shell=True, text=True)
            return self.send_json({"command": command, "output": output})

        if path == "/hash":
            value = q.get("value", [""])[0]

            # ZAFİYET-10: Weak hash algorithm
            # MD5 güvenlik amaçlı kullanım için uygun değildir.
            digest = hashlib.md5(value.encode()).hexdigest()

            return self.send_json({
                "value": value,
                "md5": digest
            })

        if path == "/config":
            # ZAFİYET-11: Configuration exposure
            return self.send_json({
                "gateway_secret": GATEWAY_SECRET,
                "service_tokens": SERVICE_TOKENS,
                "cwd": os.getcwd()
            })

        # ZAFİYET-12: Verbose error
        return self.send_json({"error": "Route not found", "path": path}, 404)


if __name__ == "__main__":
    # ZAFİYET-13: Public binding
    server = HTTPServer(("0.0.0.0", 8020), Handler)
    print("Running on http://localhost:8020")
    server.serve_forever()
