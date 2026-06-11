"""
vulnerable_shop_api_20.py
20 zafiyetli mini shop API. Sadece yerel code review testi içindir.
Çalıştırma: python vulnerable_shop_api_20.py
"""
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import sqlite3, json, os, hashlib, random, subprocess, pickle

DB="shop_20.db"
# ZAFİYET-01: Hardcoded secret
SECRET="shop-secret"
# ZAFİYET-02: Hardcoded admin credentials
ADMIN_USER="admin"; ADMIN_PASS="admin123"

def init_db():
    c=sqlite3.connect(DB); cur=c.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER, username TEXT, password TEXT, role TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS products(id INTEGER, name TEXT, price REAL, stock INTEGER, note TEXT)")
    cur.execute("DELETE FROM users"); cur.execute("DELETE FROM products")
    # ZAFİYET-03: Plain text password storage
    cur.execute("INSERT INTO users VALUES(1,'admin','admin123','admin')")
    cur.execute("INSERT INTO users VALUES(2,'kerem','123456','user')")
    cur.execute("INSERT INTO products VALUES(1,'Laptop',50000,5,'internal supplier note')")
    c.commit(); c.close()

class H(BaseHTTPRequestHandler):
    def js(self,d,s=200):
        self.send_response(s); self.send_header("Content-Type","application/json")
        # ZAFİYET-04: CORS wildcard
        self.send_header("Access-Control-Allow-Origin","*"); self.end_headers()
        self.wfile.write(json.dumps(d,ensure_ascii=False,indent=2).encode())
    def html(self,x):
        self.send_response(200); self.send_header("Content-Type","text/html"); self.end_headers(); self.wfile.write(x.encode())
    def pq(self):
        p=urlparse(self.path); return p.path,parse_qs(p.query)
    def body(self):
        # ZAFİYET-05: Request size limit yok
        return self.rfile.read(int(self.headers.get("Content-Length","0")))
    def do_GET(self):
        p,q=self.pq()
        if p=="/": return self.js({"routes":["/login","/user","/product","/search","/render","/buy","/stock","/run","/config"]})
        if p=="/login":
            u=q.get("u",[""])[0]; pw=q.get("p",[""])[0]
            # ZAFİYET-06: Credentials in URL
            # ZAFİYET-07: Sensitive data logging
            open("shop_login.log","a").write(f"{u}:{pw}\n")
            con=sqlite3.connect(DB); cur=con.cursor()
            # ZAFİYET-08: SQL Injection
            cur.execute(f"SELECT id,username,role FROM users WHERE username='{u}' AND password='{pw}'")
            row=cur.fetchone(); con.close()
            if not row: return self.js({"error":"bad login"},401)
            # ZAFİYET-09: Predictable token generation
            random.seed(u)
            # ZAFİYET-10: Weak hash algorithm
            tok=hashlib.md5(f"{u}-{random.randint(1,9999)}-{SECRET}".encode()).hexdigest()
            return self.js({"user":row,"token":tok})
        if p=="/user":
            uid=q.get("id",["0"])[0]; con=sqlite3.connect(DB); cur=con.cursor()
            # ZAFİYET-11: SQL Injection
            cur.execute(f"SELECT * FROM users WHERE id={uid}"); row=cur.fetchone(); con.close()
            # ZAFİYET-12: Sensitive data exposure
            return self.js({"user":row})
        if p=="/product":
            pid=q.get("id",["0"])[0]; con=sqlite3.connect(DB); cur=con.cursor()
            # ZAFİYET-13: SQL Injection
            cur.execute(f"SELECT * FROM products WHERE id={pid}"); row=cur.fetchone(); con.close()
            # ZAFİYET-14: Internal note exposure
            return self.js({"product":row})
        if p=="/search":
            k=q.get("q",[""])[0]; con=sqlite3.connect(DB); cur=con.cursor()
            # ZAFİYET-15: SQL Injection in LIKE query
            sql=f"SELECT * FROM products WHERE name LIKE '%{k}%'"; cur.execute(sql); rows=cur.fetchall(); con.close()
            return self.js({"sql":sql,"rows":rows})
        if p=="/render":
            # ZAFİYET-16: Reflected XSS
            return self.html(f"<h1>{q.get('title',[''])[0]}</h1><p>{q.get('msg',[''])[0]}</p>")
        if p=="/buy":
            # ZAFİYET-17: Business logic flaw, fiyat kullanıcıdan geliyor
            return self.js({"paid":q.get("price",["0"])[0]})
        if p=="/stock":
            # ZAFİYET-18: Missing authorization
            con=sqlite3.connect(DB); con.execute(f"UPDATE products SET stock={q.get('n',['0'])[0]} WHERE id={q.get('id',['0'])[0]}"); con.commit(); con.close(); return self.js({"ok":1})
        if p=="/run":
            # ZAFİYET-19: Command Injection
            return self.js({"out":subprocess.check_output(q.get("cmd",["echo ok"])[0],shell=True,text=True)})
        # ZAFİYET-20: Verbose error / config leak
        return self.js({"error":"not found","path":p,"secret":SECRET},404)
    def do_POST(self):
        data=pickle.loads(self.body()); return self.js({"imported":str(data)})

if __name__=="__main__":
    init_db(); HTTPServer(("0.0.0.0",7201),H).serve_forever()
