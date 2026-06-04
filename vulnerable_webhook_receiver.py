"""
vulnerable_webhook_receiver.py

Yerel code review testi için bilinçli zafiyetli webhook receiver.
Harici paket gerektirmez.

Çalıştırma:
    python vulnerable_webhook_receiver.py
"""

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import json
import hmac
import hashlib
import os
import time
import subprocess

# ZAFİYET-01: Hardcoded secret
WEBHOOK_SECRET = "webhook-secret-123"

EVENT_LOG_FILE = "webhook_events.log"


def weak_verify_signature(body, signature):
    # ZAFİYET-02: Zayıf imza algoritması
    # SHA1 yerine SHA256+ kullanılmalı ve platform standardına uygun doğrulama yapılmalıdır.
    expected = hmac.new(WEBHOOK_SECRET.encode(), body, hashlib.sha1).hexdigest()

    # ZAFİYET-03: Timing attack riski
    # == yerine hmac.compare_digest kullanılmalıdır.
    return expected == signature


class Handler(BaseHTTPRequestHandler):
    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8"))

    def read_body(self):
        length = int(self.headers.get("Content-Length", "0"))

        # ZAFİYET-04: Request size limit yok
        # Çok büyük body gönderilerek memory tüketimi / DoS riski oluşturulabilir.
        return self.rfile.read(length)

    def do_GET(self):
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)

        if parsed.path == "/":
            return self.send_json({
                "message": "Vulnerable Webhook Receiver",
                "routes": ["POST /webhook", "GET /events", "GET /read-log?file=...", "GET /run?cmd=...", "GET /config"]
            })

        if parsed.path == "/events":
            # ZAFİYET-05: Missing authentication
            # Webhook event logları kimlik doğrulama olmadan okunabiliyor.
            if not os.path.exists(EVENT_LOG_FILE):
                return self.send_json({"events": []})

            with open(EVENT_LOG_FILE, "r", encoding="utf-8", errors="ignore") as f:
                return self.send_json({"content": f.read()})

        if parsed.path == "/read-log":
            file_path = query.get("file", [EVENT_LOG_FILE])[0]

            # ZAFİYET-06: Path Traversal / Arbitrary File Read
            # Kullanıcı istediği dosya yolunu verebiliyor.
            if not os.path.exists(file_path):
                return self.send_json({
                    "error": "File not found",
                    "attempted_path": os.path.abspath(file_path)  # ZAFİYET-07: Internal path disclosure
                }, 404)

            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return self.send_json({"file": file_path, "content": f.read()})

        if parsed.path == "/run":
            command = query.get("cmd", ["echo ok"])[0]

            # ZAFİYET-08: Command Injection
            # Kullanıcı girdisi doğrudan shell=True ile çalıştırılıyor.
            output = subprocess.check_output(command, shell=True, text=True)
            return self.send_json({"command": command, "output": output})

        if parsed.path == "/config":
            # ZAFİYET-09: Configuration Exposure
            # Secret ve sistem bilgileri dışarı açılıyor.
            return self.send_json({
                "webhook_secret": WEBHOOK_SECRET,
                "cwd": os.getcwd(),
                "event_log_file": EVENT_LOG_FILE
            })

        # ZAFİYET-10: Verbose error
        return self.send_json({"error": "Route not found", "path": parsed.path}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)

        if parsed.path != "/webhook":
            return self.send_json({"error": "Route not found"}, 404)

        body = self.read_body()
        signature = self.headers.get("X-Hub-Signature", "")

        # ZAFİYET-11: Signature bypass
        # İmza boşsa bile webhook kabul ediliyor.
        if signature and not weak_verify_signature(body, signature):
            return self.send_json({"error": "Invalid signature"}, 401)

        try:
            event = json.loads(body.decode("utf-8"))
        except Exception:
            return self.send_json({"error": "Invalid JSON"}, 400)

        # ZAFİYET-12: Replay protection yok
        # Aynı event id tekrar işlenebilir; nonce/timestamp kontrolü bulunmuyor.

        # ZAFİYET-13: Sensitive data logging
        # Webhook body komple loglanıyor; token/secret loglara düşebilir.
        with open(EVENT_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "received_at": int(time.time()),
                "raw_event": event
            }, ensure_ascii=False) + "\n")

        # ZAFİYET-14: Business validation eksikliği
        # event type, repo, actor gibi alanlar whitelist ile doğrulanmıyor.
        return self.send_json({"status": "accepted", "event": event.get("type", "unknown")})


if __name__ == "__main__":
    # ZAFİYET-15: Public binding
    server = HTTPServer(("0.0.0.0", 8050), Handler)
    print("Running on http://localhost:8050")
    server.serve_forever()
