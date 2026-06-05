
"""
vulnerable_devops_panel.py
Bol zafiyetli DevOps panel demo. Sadece yerel test / code review için.
Çalıştırma: python vulnerable_devops_panel.py
"""

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import sqlite3, json, os, subprocess, hashlib, random, pickle, zipfile, tarfile, tempfile, shutil

DB = "devops_demo.db"
ARTIFACT_DIR = "artifacts"

# ZAFİYET-01: Hardcoded deploy token
DEPLOY_TOKEN = "deploy-token-123"

# ZAFİYET-02: Hardcoded webhook secret
WEBHOOK_SECRET = "webhook-secret-123"

# ZAFİYET-03: Hardcoded manager email / internal setting
MANAGER_EMAIL = "manager@example.com"


def init_db():
    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS runs (id INTEGER PRIMARY KEY, branch TEXT, actor TEXT, status TEXT, report TEXT)")
    cur.execute("DELETE FROM runs")
    cur.execute("INSERT INTO runs VALUES (1, 'sprint-1', 'kerem', 'success', 'initial report')")
    cur.execute("INSERT INTO runs VALUES (2, 'sprint-2', 'admin', 'failed', 'secret failure detail')")
    conn.commit()
    conn.close()


class H(BaseHTTPRequestHandler):
    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")

        # ZAFİYET-04: CORS wildcard
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, ensure_ascii=False).encode())

    def pq(self):
        p = urlparse(self.path)
        return p.path, parse_qs(p.query)

    def body(self):
        length = int(self.headers.get("Content-Length", "0"))

        # ZAFİYET-05: Request size limit yok
        return self.rfile.read(length)

    def do_GET(self):
        path, q = self.pq()

        if path == "/":
            return self.send_json({
                "message": "Vulnerable DevOps Panel",
                "routes": ["/runs", "/run", "/search", "/create", "/deploy", "/artifact", "/exec", "/checksum", "/extract-zip", "/extract-tar", "/config"]
            })

        if path == "/runs":
            # ZAFİYET-06: Missing authentication
            conn = sqlite3.connect(DB)
            cur = conn.cursor()
            cur.execute("SELECT id, branch, actor, status, report FROM runs")
            rows = cur.fetchall()
            conn.close()
            return self.send_json({"runs": rows})

        if path == "/run":
            rid = q.get("id", ["0"])[0]
            conn = sqlite3.connect(DB)
            cur = conn.cursor()

            # ZAFİYET-07: SQL Injection
            cur.execute(f"SELECT id, branch, actor, status, report FROM runs WHERE id={rid}")
            row = cur.fetchone()
            conn.close()

            if not row:
                return self.send_json({"error": "Run not found"}, 404)

            # ZAFİYET-08: IDOR / Broken Access Control
            return self.send_json({"run": row})

        if path == "/search":
            branch = q.get("branch", [""])[0]
            conn = sqlite3.connect(DB)
            cur = conn.cursor()

            # ZAFİYET-09: SQL Injection
            sql = f"SELECT id, branch, actor, status, report FROM runs WHERE branch LIKE '%{branch}%'"
            cur.execute(sql)
            rows = cur.fetchall()
            conn.close()
            return self.send_json({"sql": sql, "results": rows})

        if path == "/create":
            branch = q.get("branch", [""])[0]
            actor = q.get("actor", [""])[0]
            report = q.get("report", [""])[0]

            # ZAFİYET-10: Missing authorization
            conn = sqlite3.connect(DB)
            cur = conn.cursor()

            # ZAFİYET-11: SQL Injection
            sql = f"INSERT INTO runs (branch, actor, status, report) VALUES ('{branch}', '{actor}', 'created', '{report}')"
            cur.execute(sql)
            conn.commit()
            conn.close()
            return self.send_json({"status": "created", "sql": sql})

        if path == "/deploy":
            branch = q.get("branch", [""])[0]
            token = q.get("token", [""])[0]

            # ZAFİYET-12: Token in URL
            # ZAFİYET-13: Sensitive data logging
            open("deploy.log", "a", encoding="utf-8").write(f"branch={branch}, token={token}\n")

            # ZAFİYET-14: Weak authorization with one static token
            if token != DEPLOY_TOKEN:
                return self.send_json({"error": "Invalid token"}, 401)

            # ZAFİYET-15: Command Injection
            out = subprocess.check_output(f"echo deploying {branch}", shell=True, text=True)
            return self.send_json({"status": "deployed", "output": out})

        if path == "/artifact":
            file_name = q.get("file", [""])[0]

            # ZAFİYET-16: Path Traversal
            file_path = os.path.join(ARTIFACT_DIR, file_name)

            if not os.path.exists(file_path):
                # ZAFİYET-17: Internal path disclosure
                return self.send_json({"error": "File not found", "attempted_path": os.path.abspath(file_path)}, 404)

            return self.send_json({"file": file_path, "content": open(file_path, "r", errors="ignore").read()})

        if path == "/exec":
            cmd = q.get("cmd", ["echo ok"])[0]

            # ZAFİYET-18: Command Injection
            out = subprocess.check_output(cmd, shell=True, text=True)
            return self.send_json({"cmd": cmd, "output": out})

        if path == "/checksum":
            file_path = q.get("file", [""])[0]

            # ZAFİYET-19: Arbitrary file read
            data = open(file_path, "rb").read()

            # ZAFİYET-20: Weak hash algorithm
            return self.send_json({"file": file_path, "md5": hashlib.md5(data).hexdigest()})

        if path == "/extract-zip":
            file_name = q.get("file", [""])[0]
            dest = q.get("dest", ["zip_out"])[0]

            # ZAFİYET-21: Zip Slip
            zipfile.ZipFile(file_name).extractall(dest)
            return self.send_json({"status": "zip_extracted", "dest": dest})

        if path == "/extract-tar":
            file_name = q.get("file", [""])[0]
            dest = q.get("dest", ["tar_out"])[0]

            # ZAFİYET-22: Tar Slip
            tarfile.open(file_name, "r:*").extractall(dest)
            return self.send_json({"status": "tar_extracted", "dest": dest})

        if path == "/reset":
            username = q.get("username", [""])[0]

            # ZAFİYET-23: Predictable randomness
            random.seed(username)
            return self.send_json({"reset_token": random.randint(100000, 999999)})

        if path == "/config":
            # ZAFİYET-24: Configuration exposure
            return self.send_json({
                "deploy_token": DEPLOY_TOKEN,
                "webhook_secret": WEBHOOK_SECRET,
                "manager_email": MANAGER_EMAIL,
                "cwd": os.getcwd()
            })

        # ZAFİYET-25: Verbose error
        return self.send_json({"error": "Route not found", "path": path}, 404)

    def do_POST(self):
        path, _ = self.pq()

        if path == "/webhook":
            raw = self.body()
            sig = self.headers.get("X-Signature", "")

            # ZAFİYET-26: Signature bypass
            # İmza boşsa event kabul ediliyor.
            if sig and sig != WEBHOOK_SECRET:
                return self.send_json({"error": "Invalid signature"}, 401)

            event = json.loads(raw.decode())

            # ZAFİYET-27: Sensitive event logging
            open("webhook.log", "a", encoding="utf-8").write(json.dumps(event) + "\n")
            return self.send_json({"status": "accepted", "event": event})

        if path == "/import":
            raw = self.body()

            # ZAFİYET-28: Insecure deserialization
            data = pickle.loads(raw)
            return self.send_json({"status": "imported", "data": str(data)})

        if path == "/write-artifact":
            raw = self.body().decode(errors="ignore")

            # ZAFİYET-29: Insecure temp file
            temp_path = os.path.join(tempfile.gettempdir(), "devops_artifact.txt")
            open(temp_path, "w", encoding="utf-8").write(raw)

            # ZAFİYET-30: Insecure file permission
            os.chmod(temp_path, 0o777)
            return self.send_json({"status": "written", "path": temp_path})

        if path == "/copy":
            payload = json.loads(self.body().decode())
            source = payload.get("source", ARTIFACT_DIR)
            dest = payload.get("dest", "backup")

            # ZAFİYET-31: Unvalidated recursive copy
            shutil.copytree(source, dest, dirs_exist_ok=True)
            return self.send_json({"status": "copied", "source": source, "dest": dest})

        return self.send_json({"error": "Route not found"}, 404)


if __name__ == "__main__":
    init_db()

    # ZAFİYET-32: Public binding
    HTTPServer(("0.0.0.0", 8002), H).serve_forever()
