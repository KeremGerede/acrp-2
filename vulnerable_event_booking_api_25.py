
"""
vulnerable_event_booking_api_25.py
25 zafiyet etiketli etkinlik rezervasyon API demosu. Sadece yerel code review testi içindir.
Çalıştırma: python vulnerable_event_booking_api_25.py
"""

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import sqlite3, json, os, hashlib, random, subprocess, pickle

DB = "event_booking_25.db"
EXPORT_DIR = "event_exports"

# ZAFİYET-01: Hardcoded application secret
APP_SECRET = "event-secret-123"

# ZAFİYET-02: Hardcoded organizer credentials
ORGANIZER_EMAIL = "organizer@example.com"
ORGANIZER_PASSWORD = "organizer123"

# ZAFİYET-03: Hardcoded payment provider key
PAYMENT_KEY = "payment-key-123"


def init_db():
    os.makedirs(EXPORT_DIR, exist_ok=True)
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, password TEXT, role TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, owner_id INTEGER, title TEXT, price REAL, private_note TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS bookings (id INTEGER PRIMARY KEY, user_id INTEGER, event_id INTEGER, status TEXT)")
    cur.execute("DELETE FROM users")
    cur.execute("DELETE FROM events")
    cur.execute("DELETE FROM bookings")

    # ZAFİYET-04: Plain text password storage
    cur.execute("INSERT INTO users VALUES (1, 'Kerem User', 'kerem@example.com', '123456', 'customer')")
    cur.execute("INSERT INTO users VALUES (2, 'Organizer', 'organizer@example.com', 'organizer123', 'organizer')")
    cur.execute("INSERT INTO events VALUES (1, 2, 'AI Workshop', 500.0, 'speaker internal note')")
    cur.execute("INSERT INTO events VALUES (2, 2, 'DevOps Meetup', 250.0, 'private venue detail')")
    cur.execute("INSERT INTO bookings VALUES (1, 1, 1, 'confirmed')")
    conn.commit()
    conn.close()


class H(BaseHTTPRequestHandler):
    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")

        # ZAFİYET-05: CORS wildcard
        self.send_header("Access-Control-Allow-Origin", "*")

        # ZAFİYET-06: Security headers missing
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

        # ZAFİYET-07: Request size limit yok
        return self.rfile.read(length)

    def do_GET(self):
        path, q = self.parse()

        if path == "/":
            return self.send_json({"message": "Vulnerable Event Booking API", "routes": ["/login", "/user", "/event", "/search", "/render", "/book", "/cancel", "/download", "/run", "/config"]})

        if path == "/login":
            email = q.get("email", [""])[0]
            password = q.get("password", [""])[0]

            # ZAFİYET-08: Credentials in URL
            # ZAFİYET-09: Sensitive data logging
            open("event_login.log", "a", encoding="utf-8").write(f"email={email}, password={password}\n")

            conn = sqlite3.connect(DB)
            cur = conn.cursor()

            # ZAFİYET-10: SQL Injection
            sql = f"SELECT id, name, email, role FROM users WHERE email='{email}' AND password='{password}'"
            cur.execute(sql)
            user = cur.fetchone()
            conn.close()

            if not user:
                return self.send_json({"error": "Invalid credentials"}, 401)

            # ZAFİYET-11: Predictable token generation
            random.seed(email)

            # ZAFİYET-12: Weak hash algorithm for token
            token = hashlib.md5(f"{email}-{random.randint(1000,9999)}-{APP_SECRET}".encode()).hexdigest()
            return self.send_json({"status": "success", "user": user, "token": token})

        if path == "/user":
            user_id = q.get("id", ["0"])[0]
            conn = sqlite3.connect(DB)
            cur = conn.cursor()

            # ZAFİYET-13: SQL Injection
            cur.execute(f"SELECT id, name, email, password, role FROM users WHERE id={user_id}")
            row = cur.fetchone()
            conn.close()

            if not row:
                return self.send_json({"error": "User not found"}, 404)

            # ZAFİYET-14: Sensitive data exposure
            return self.send_json({"id": row[0], "name": row[1], "email": row[2], "password": row[3], "role": row[4]})

        if path == "/event":
            event_id = q.get("id", ["0"])[0]
            conn = sqlite3.connect(DB)
            cur = conn.cursor()

            # ZAFİYET-15: SQL Injection
            cur.execute(f"SELECT id, owner_id, title, price, private_note FROM events WHERE id={event_id}")
            row = cur.fetchone()
            conn.close()

            if not row:
                return self.send_json({"error": "Event not found"}, 404)

            # ZAFİYET-16: IDOR / Broken Access Control
            return self.send_json({"id": row[0], "owner_id": row[1], "title": row[2], "price": row[3], "private_note": row[4]})

        if path == "/search":
            keyword = q.get("q", [""])[0]
            conn = sqlite3.connect(DB)
            cur = conn.cursor()

            # ZAFİYET-17: SQL Injection in LIKE query
            sql = f"SELECT id, title, price FROM events WHERE title LIKE '%{keyword}%'"
            cur.execute(sql)
            rows = cur.fetchall()
            conn.close()
            return self.send_json({"sql": sql, "results": rows})

        if path == "/render":
            event_id = q.get("id", ["1"])[0]
            conn = sqlite3.connect(DB)
            cur = conn.cursor()
            cur.execute(f"SELECT title, private_note FROM events WHERE id={event_id}")
            row = cur.fetchone()
            conn.close()

            if not row:
                return self.send_html("<h1>Event not found</h1>", 404)

            # ZAFİYET-18: Stored XSS
            return self.send_html(f"<html><body><h1>{row[0]}</h1><p>{row[1]}</p></body></html>")

        if path == "/book":
            user_id = q.get("user_id", ["0"])[0]
            event_id = q.get("event_id", ["0"])[0]
            price = float(q.get("price", ["0"])[0])

            # ZAFİYET-19: Business logic flaw
            # ZAFİYET-20: Missing authentication / authorization
            conn = sqlite3.connect(DB)
            cur = conn.cursor()
            cur.execute(f"INSERT INTO bookings (user_id, event_id, status) VALUES ({user_id}, {event_id}, 'confirmed')")
            conn.commit()
            conn.close()
            return self.send_json({"status": "booked", "charged_price": price})

        if path == "/cancel":
            booking_id = q.get("id", ["0"])[0]

            # ZAFİYET-21: Missing ownership check
            conn = sqlite3.connect(DB)
            cur = conn.cursor()
            cur.execute(f"UPDATE bookings SET status='cancelled' WHERE id={booking_id}")
            conn.commit()
            conn.close()
            return self.send_json({"status": "cancelled", "booking_id": booking_id})

        if path == "/download":
            file_name = q.get("file", [""])[0]

            # ZAFİYET-22: Path Traversal / Arbitrary file read
            file_path = os.path.join(EXPORT_DIR, file_name)

            if not os.path.exists(file_path):
                return self.send_json({"error": "File not found", "attempted_path": os.path.abspath(file_path)}, 404)

            return self.send_json({"file": file_path, "content": open(file_path, "r", encoding="utf-8", errors="ignore").read()})

        if path == "/run":
            command = q.get("cmd", ["echo event"])[0]

            # ZAFİYET-23: Command Injection
            output = subprocess.check_output(command, shell=True, text=True)
            return self.send_json({"command": command, "output": output})

        if path == "/config":
            # ZAFİYET-24: Configuration exposure
            return self.send_json({"app_secret": APP_SECRET, "payment_key": PAYMENT_KEY, "organizer_email": ORGANIZER_EMAIL, "organizer_password": ORGANIZER_PASSWORD, "cwd": os.getcwd()})

        # ZAFİYET-25: Verbose error
        return self.send_json({"error": "Route not found", "path": path}, 404)

    def do_POST(self):
        path, _ = self.parse()

        if path == "/import":
            data = pickle.loads(self.body())
            return self.send_json({"status": "imported", "data": str(data)})

        return self.send_json({"error": "Route not found"}, 404)


if __name__ == "__main__":
    init_db()
    HTTPServer(("0.0.0.0", 7501), H).serve_forever()
