"""
vulnerable_mini_crm_30.py
Yerel code review testi için bilinçli olarak 30 zafiyet içerir.
Çalıştırma: python vulnerable_mini_crm_30.py
"""

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import sqlite3, json, os, hashlib, random, subprocess, pickle, tempfile, zipfile, urllib.request

DB = "mini_crm_30.db"
FILES = "crm_files"

# ZAFİYET-01: Hardcoded secret; secret değerleri kod içinde tutulmamalıdır.
APP_SECRET = "crm-hardcoded-secret"
# ZAFİYET-02: Hardcoded admin credentials; admin bilgileri kod içinde tutulmamalıdır.
ADMIN_USER = "admin"
ADMIN_PASS = "admin123"
# ZAFİYET-03: Hardcoded external service key; API key secret manager ile yönetilmelidir.
MAIL_API_KEY = "mail-api-key-123"


def init_db():
    os.makedirs(FILES, exist_ok=True)
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS customers (id INTEGER PRIMARY KEY, name TEXT, email TEXT, password TEXT, role TEXT, note TEXT)")
    cur.execute("DELETE FROM customers")
    # ZAFİYET-04: Plain text password storage; parolalar düz metin saklanıyor.
    cur.execute("INSERT INTO customers VALUES (1,'Kerem','kerem@example.com','123456','user','normal customer')")
    cur.execute("INSERT INTO customers VALUES (2,'Admin','admin@example.com','admin123','admin','internal admin note')")
    con.commit(); con.close()


class H(BaseHTTPRequestHandler):
    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        # ZAFİYET-05: CORS wildcard; tüm originlere izin veriliyor.
        self.send_header("Access-Control-Allow-Origin", "*")
        # ZAFİYET-06: Security headers missing; CSP ve X-Content-Type-Options gibi headerlar yok.
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, ensure_ascii=False).encode())

    def send_html(self, html, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers(); self.wfile.write(html.encode())

    def pq(self):
        p = urlparse(self.path)
        return p.path, parse_qs(p.query)

    def body(self):
        n = int(self.headers.get("Content-Length", "0"))
        # ZAFİYET-07: Request size limit yok; büyük body ile DoS riski oluşabilir.
        return self.rfile.read(n)

    def do_GET(self):
        path, q = self.pq()
        if path == "/":
            return self.send_json({"routes": ["/login", "/customer", "/search", "/render", "/update", "/delete", "/download", "/fetch", "/run", "/hash", "/extract", "/config"]})

        if path == "/login":
            user = q.get("user", [""])[0]
            pwd = q.get("password", [""])[0]
            # ZAFİYET-08: Credentials in URL; kullanıcı adı/parola query string içinde taşınıyor.
            # ZAFİYET-09: Sensitive logging; parola düz metin loglanıyor.
            open("crm_login.log", "a", encoding="utf-8").write(f"user={user}, password={pwd}\n")
            con = sqlite3.connect(DB); cur = con.cursor()
            # ZAFİYET-10: SQL Injection; kullanıcı girdileri doğrudan SQL'e ekleniyor.
            sql = f"SELECT id,name,email,role FROM customers WHERE name='{user}' AND password='{pwd}'"
            cur.execute(sql); row = cur.fetchone(); con.close()
            if not row: return self.send_json({"error": "invalid"}, 401)
            # ZAFİYET-11: Predictable token generation; random.seed ile tahmin edilebilir token üretiliyor.
            random.seed(user)
            # ZAFİYET-12: Weak hash for token; MD5 güvenli token üretimi için uygun değildir.
            token = hashlib.md5(f"{user}-{random.randint(1,9999)}-{APP_SECRET}".encode()).hexdigest()
            return self.send_json({"status": "ok", "user": row, "token": token})

        if path == "/customer":
            cid = q.get("id", ["0"])[0]
            con = sqlite3.connect(DB); cur = con.cursor()
            # ZAFİYET-13: SQL Injection; id doğrudan sorguya ekleniyor.
            cur.execute(f"SELECT id,name,email,password,role,note FROM customers WHERE id={cid}")
            row = cur.fetchone(); con.close()
            if not row: return self.send_json({"error": "not found"}, 404)
            # ZAFİYET-14: IDOR; başka kullanıcının kaydı yetki kontrolü olmadan okunabiliyor.
            # ZAFİYET-15: Sensitive data exposure; parola ve internal note response içinde dönüyor.
            return self.send_json({"customer": row})

        if path == "/search":
            term = q.get("q", [""])[0]
            con = sqlite3.connect(DB); cur = con.cursor()
            # ZAFİYET-16: SQL Injection in LIKE; arama sorgusu parametreli değil.
            sql = f"SELECT id,name,email,note FROM customers WHERE name LIKE '%{term}%' OR email LIKE '%{term}%'"
            cur.execute(sql); rows = cur.fetchall(); con.close()
            return self.send_json({"sql": sql, "results": rows})

        if path == "/render":
            cid = q.get("id", ["1"])[0]
            con = sqlite3.connect(DB); cur = con.cursor()
            cur.execute(f"SELECT name,note FROM customers WHERE id={cid}")
            row = cur.fetchone(); con.close()
            if not row: return self.send_html("<h1>not found</h1>", 404)
            # ZAFİYET-17: Stored XSS; DB verisi escape edilmeden HTML'e yazılıyor.
            return self.send_html(f"<h1>{row[0]}</h1><p>{row[1]}</p>")

        if path == "/update":
            cid = q.get("id", ["0"])[0]
            note = q.get("note", [""])[0]
            # ZAFİYET-18: Missing authorization; kayıt güncelleme için token/rol kontrolü yok.
            con = sqlite3.connect(DB); cur = con.cursor()
            # ZAFİYET-19: SQL Injection in UPDATE; note ve id parametreleri doğrudan kullanılıyor.
            cur.execute(f"UPDATE customers SET note='{note}' WHERE id={cid}")
            con.commit(); con.close()
            return self.send_json({"status": "updated"})

        if path == "/delete":
            cid = q.get("id", ["0"])[0]
            # ZAFİYET-20: Missing admin authorization; silme işlemi korumasız.
            con = sqlite3.connect(DB); cur = con.cursor()
            cur.execute(f"DELETE FROM customers WHERE id={cid}")
            con.commit(); con.close()
            return self.send_json({"status": "deleted", "id": cid})

        if path == "/download":
            file = q.get("file", [""])[0]
            # ZAFİYET-21: Path Traversal; kullanıcı dosya yolunu kontrol ediyor.
            fp = os.path.join(FILES, file)
            if not os.path.exists(fp):
                # ZAFİYET-22: Internal path disclosure; gerçek path response içinde veriliyor.
                return self.send_json({"error": "not found", "path": os.path.abspath(fp)}, 404)
            return self.send_json({"file": fp, "content": open(fp, "r", errors="ignore").read()})

        if path == "/fetch":
            url = q.get("url", [""])[0]
            # ZAFİYET-23: SSRF; sunucu kullanıcı tarafından verilen URL'i fetch ediyor.
            data = urllib.request.urlopen(url, timeout=3).read(2000).decode(errors="ignore")
            return self.send_json({"url": url, "preview": data})

        if path == "/run":
            cmd = q.get("cmd", ["echo ok"])[0]
            # ZAFİYET-24: Command Injection; kullanıcı girdisi shell=True ile çalıştırılıyor.
            out = subprocess.check_output(cmd, shell=True, text=True)
            return self.send_json({"cmd": cmd, "output": out})

        if path == "/hash":
            value = q.get("value", [""])[0]
            # ZAFİYET-25: Weak hash algorithm; MD5 güvenlik amaçlı kullanılmamalıdır.
            return self.send_json({"value": value, "md5": hashlib.md5(value.encode()).hexdigest()})

        if path == "/extract":
            file = q.get("file", [""])[0]
            dest = q.get("dest", ["crm_extract"])[0]
            # ZAFİYET-26: Zip Slip; ZIP içi pathler doğrulanmadan extract ediliyor.
            zipfile.ZipFile(file).extractall(dest)
            return self.send_json({"status": "extracted", "dest": dest})

        if path == "/config":
            # ZAFİYET-27: Configuration exposure; secret ve credential bilgileri dışarı açılıyor.
            return self.send_json({"secret": APP_SECRET, "admin": ADMIN_USER, "admin_pass": ADMIN_PASS, "mail_key": MAIL_API_KEY, "cwd": os.getcwd()})

        # ZAFİYET-28: Verbose error; bilinmeyen route bilgisi response içinde dönüyor.
        return self.send_json({"error": "route not found", "path": path}, 404)

    def do_POST(self):
        path, _ = self.pq()
        if path == "/import":
            # ZAFİYET-29: Insecure deserialization; pickle güvenilmeyen veriyle kullanılmamalıdır.
            obj = pickle.loads(self.body())
            return self.send_json({"imported": str(obj)})
        if path == "/temp":
            # ZAFİYET-30: Insecure temporary file; tahmin edilebilir temp dosya adı kullanılıyor.
            fp = os.path.join(tempfile.gettempdir(), "crm_temp.txt")
            open(fp, "wb").write(self.body())
            return self.send_json({"saved": fp})
        return self.send_json({"error": "route not found"}, 404)

if __name__ == "__main__":
    init_db()
    HTTPServer(("0.0.0.0", 7901), H).serve_forever()
