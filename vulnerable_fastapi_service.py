"""
vulnerable_fastapi_service.py

Bu dosya yalnızca yerel test / code review agent denemesi için hazırlanmıştır.
Gerçek projede, sunucuda veya public ortamda çalıştırmayın.

Çalıştırmak istersen:
    pip install fastapi uvicorn python-multipart pyjwt
    uvicorn vulnerable_fastapi_service:app --reload
"""

from fastapi import FastAPI, Request, Form, Header
from fastapi.responses import HTMLResponse, JSONResponse
import sqlite3
import os
import jwt
import time
import logging

app = FastAPI(title="Vulnerable FastAPI Demo")

DB_NAME = "fastapi_users.db"

# ZAFİYET-01: Hardcoded JWT secret
# Secret key kod içine yazılmamalı; environment variable veya secret manager kullanılmalıdır.
JWT_SECRET = "hardcoded-jwt-secret"

# ZAFİYET-02: Fazla detaylı loglama
# Hassas veriler, tokenlar veya kullanıcı girdileri doğrudan loglanmamalıdır.
logging.basicConfig(level=logging.DEBUG)


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            password TEXT,
            role TEXT,
            api_key TEXT
        )
    """)

    cursor.execute("DELETE FROM users")

    # ZAFİYET-03: Plain text password ve API key saklama
    # Parolalar hashlenmeli, API key gibi bilgiler güvenli şekilde saklanmalıdır.
    cursor.execute("""
        INSERT INTO users (email, password, role, api_key)
        VALUES ('admin@example.com', 'admin123', 'admin', 'ADMIN-API-KEY-123')
    """)

    cursor.execute("""
        INSERT INTO users (email, password, role, api_key)
        VALUES ('user@example.com', 'password', 'user', 'USER-API-KEY-456')
    """)

    conn.commit()
    conn.close()


@app.on_event("startup")
def startup():
    init_db()


@app.get("/")
def home():
    return {
        "message": "Vulnerable FastAPI demo is running",
        "warning": "Bu uygulama bilinçli olarak zafiyetlidir."
    }


@app.post("/login")
def login(email: str = Form(...), password: str = Form(...)):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # ZAFİYET-04: SQL Injection
    # Kullanıcı girdisi parametreli sorgu yerine string içine gömülüyor.
    query = f"SELECT id, email, role FROM users WHERE email = '{email}' AND password = '{password}'"

    logging.debug(f"Running login query: {query}")

    cursor.execute(query)
    user = cursor.fetchone()
    conn.close()

    if not user:
        return JSONResponse({"error": "Invalid credentials"}, status_code=401)

    payload = {
        "user_id": user[0],
        "email": user[1],
        "role": user[2],
        "iat": int(time.time())

        # ZAFİYET-05: Token expiration eksik
        # JWT içerisinde exp değeri yok. Token süresiz kullanılabilir.
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")

    return {
        "status": "success",

        # ZAFİYET-06: Token response içinde doğrudan dönülüyor
        # Bu normal olabilir ancak güvenli cookie, kısa süreli token ve refresh token yapısı düşünülmelidir.
        "token": token
    }


@app.get("/profile/{user_id}")
def get_profile(user_id: int, authorization: str | None = Header(default=None)):
    # ZAFİYET-07: Broken Access Control / IDOR
    # Token kontrolü yapılmadan istenilen user_id bilgisi okunabiliyor.
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(f"SELECT id, email, role, api_key FROM users WHERE id = {user_id}")
    user = cursor.fetchone()
    conn.close()

    if not user:
        return JSONResponse({"error": "User not found"}, status_code=404)

    return {
        "id": user[0],
        "email": user[1],
        "role": user[2],

        # ZAFİYET-08: Sensitive Data Exposure
        # API key gibi hassas bilgiler response içinde gösterilmemelidir.
        "api_key": user[3]
    }


@app.get("/render", response_class=HTMLResponse)
def render_page(name: str = "Guest"):
    # ZAFİYET-09: Reflected XSS
    # Kullanıcı girdisi HTML içine escape edilmeden yerleştiriliyor.
    html = f"""
    <html>
        <body>
            <h2>Hello {name}</h2>
            <p>Welcome to vulnerable FastAPI demo.</p>
        </body>
    </html>
    """

    return HTMLResponse(content=html)


@app.get("/download")
def download_file(path: str):
    # ZAFİYET-10: Path Traversal
    # Kullanıcının verdiği path doğrudan dosya okumak için kullanılıyor.
    # Güvenli yaklaşım: whitelist, base directory kontrolü ve path normalize işlemleri.
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        return {
            "path": path,
            "content": content
        }
    except FileNotFoundError:
        return JSONResponse({"error": "File not found"}, status_code=404)


@app.post("/admin/change-role")
def change_role(user_id: int = Form(...), new_role: str = Form(...)):
    # ZAFİYET-11: Missing Authentication / Authorization
    # Admin işlemi olmasına rağmen hiçbir kullanıcı/rol kontrolü yapılmıyor.
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # ZAFİYET-12: SQL Injection ihtimali
    # new_role değeri doğrudan SQL içine ekleniyor.
    query = f"UPDATE users SET role = '{new_role}' WHERE id = {user_id}"

    cursor.execute(query)
    conn.commit()
    conn.close()

    return {
        "status": "role_changed",
        "user_id": user_id,
        "new_role": new_role
    }


@app.post("/debug/log")
async def debug_log(request: Request):
    body = await request.body()

    # ZAFİYET-13: Sensitive Request Logging
    # Request body komple loglanıyor. Parola/token gibi bilgiler loglara düşebilir.
    logging.debug(f"Incoming raw body: {body}")

    return {
        "status": "logged"
    }


@app.get("/config")
def get_config():
    # ZAFİYET-14: Internal Configuration Exposure
    # Uygulama içi konfigürasyon ve gizli değerler dışarı açılıyor.
    return {
        "db_name": DB_NAME,
        "jwt_secret": JWT_SECRET,
        "environment": os.environ.get("ENV", "development")
    }
