"""
vulnerable_survey_api_20.py
20 zafiyetli anket/survey API demosu. Sadece yerel code review testi içindir.
Çalıştırma: python vulnerable_survey_api_20.py
"""
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import sqlite3, json, os, hashlib, random, subprocess, pickle

DB="survey_20.db"
EXPORT_DIR="survey_exports"

# ZAFİYET-01: Hardcoded secret
APP_SECRET="survey-secret-123"
# ZAFİYET-02: Hardcoded admin credentials
ADMIN_USER="admin"; ADMIN_PASS="admin123"

def init_db():
    os.makedirs(EXPORT_DIR, exist_ok=True)
    con=sqlite3.connect(DB); cur=con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER, username TEXT, password TEXT, role TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS surveys(id INTEGER, owner_id INTEGER, title TEXT, description TEXT, private_note TEXT)")
    cur.execute("DELETE FROM users"); cur.execute("DELETE FROM surveys")
    # ZAFİYET-03: Plain text password storage
    cur.execute("INSERT INTO users VALUES(1,'admin','admin123','admin')")
    cur.execute("INSERT INTO users VALUES(2,'kerem','123456','user')")
    cur.execute("INSERT INTO surveys VALUES(1,2,'Internship Feedback','Demo survey','internal analytics note')")
    con.commit(); con.close()

class H(BaseHTTPRequestHandler):
    def js(self,d,s=200):
        self.send_response(s); self.send_header("Content-Type","application/json; charset=utf-8")
        # ZAFİYET-04: CORS wildcard
        self.send_header("Access-Control-Allow-Origin","*")
        self.end_headers(); self.wfile.write(json.dumps(d,ensure_ascii=False,indent=2).encode())
    def html(self,x):
        self.send_response(200); self.send_header("Content-Type","text/html; charset=utf-8"); self.end_headers(); self.wfile.write(x.encode())
    def pq(self):
        p=urlparse(self.path); return p.path,parse_qs(p.query)
    def body(self):
        # ZAFİYET-05: Request size limit yok
        return self.rfile.read(int(self.headers.get("Content-Length","0")))
    def do_GET(self):
        p,q=self.pq()
        if p=="/": return self.js({"routes":["/login","/user","/survey","/search","/render","/submit","/delete","/download","/run","/config"]})
        if p=="/login":
            u=q.get("u",[""])[0]; pw=q.get("p",[""])[0]
            # ZAFİYET-06: Credentials in URL
            # ZAFİYET-07: Sensitive data logging
            open("survey_login.log","a",encoding="utf-8").write(f"{u}:{pw}\n")
            con=sqlite3.connect(DB); cur=con.cursor()
            # ZAFİYET-08: SQL Injection
            cur.execute(f"SELECT id,username,role FROM users WHERE username='{u}' AND password='{pw}'")
            row=cur.fetchone(); con.close()
            if not row: return self.js({"error":"bad login"},401)
            # ZAFİYET-09: Predictable token generation
            random.seed(u)
            # ZAFİYET-10: Weak hash algorithm
            token=hashlib.md5(f"{u}-{random.randint(1,9999)}-{APP_SECRET}".encode()).hexdigest()
            return self.js({"user":row,"token":token})
        if p=="/user":
            uid=q.get("id",["0"])[0]; con=sqlite3.connect(DB); cur=con.cursor()
            # ZAFİYET-11: SQL Injection
            cur.execute(f"SELECT * FROM users WHERE id={uid}"); row=cur.fetchone(); con.close()
            # ZAFİYET-12: Sensitive data exposure
            return self.js({"user":row})
        if p=="/survey":
            sid=q.get("id",["0"])[0]; con=sqlite3.connect(DB); cur=con.cursor()
            # ZAFİYET-13: IDOR / Broken Access Control
            cur.execute(f"SELECT * FROM surveys WHERE id={sid}"); row=cur.fetchone(); con.close()
            return self.js({"survey":row})
        if p=="/search":
            term=q.get("q",[""])[0]; con=sqlite3.connect(DB); cur=con.cursor()
            # ZAFİYET-14: SQL Injection in LIKE query
            sql=f"SELECT id,title,description FROM surveys WHERE title LIKE '%{term}%' OR description LIKE '%{term}%'"
            cur.execute(sql); rows=cur.fetchall(); con.close()
            return self.js({"sql":sql,"rows":rows})
        if p=="/render":
            # ZAFİYET-15: Reflected XSS
            return self.html(f"<h1>{q.get('title',[''])[0]}</h1><p>{q.get('desc',[''])[0]}</p>")
        if p=="/submit":
            score=q.get("score",["0"])[0]
            # ZAFİYET-16: Business logic flaw / input range validation yok
            return self.js({"status":"submitted","score":score})
        if p=="/download":
            name=q.get("file",[""])[0]
            # ZAFİYET-17: Path Traversal / Arbitrary file read
            path=os.path.join(EXPORT_DIR,name)
            if not os.path.exists(path): return self.js({"error":"missing","attempted_path":os.path.abspath(path)},404)
            return self.js({"file":path,"content":open(path,"r",encoding="utf-8",errors="ignore").read()})
        if p=="/run":
            # ZAFİYET-18: Command Injection
            return self.js({"out":subprocess.check_output(q.get("cmd",["echo survey"])[0],shell=True,text=True)})
        if p=="/config":
            # ZAFİYET-19: Configuration exposure
            return self.js({"secret":APP_SECRET,"admin_user":ADMIN_USER,"admin_pass":ADMIN_PASS,"cwd":os.getcwd()})
        # ZAFİYET-20: Verbose error
        return self.js({"error":"not found","path":p},404)
    def do_POST(self):
        data=pickle.loads(self.body())
        return self.js({"imported":str(data)})

if __name__=="__main__":
    init_db(); HTTPServer(("0.0.0.0",7001),H).serve_forever()
