"""
vulnerable_demo_app.py

Bu dosya yalnızca yerel test / code review agent denemesi için hazırlanmıştır.
Gerçek projede, sunucuda veya public ortamda çalıştırmayın.

Çalıştırmak istersen:
    pip install flask
    python vulnerable_demo_app.py
"""

from flask import Flask, request, jsonify, render_template_string
import sqlite3
import os
import subprocess
import pickle
import hashlib

app = Flask(__name__)

# ZAFİYET-01: Hardcoded secret key
# Gizli anahtarlar kod içine yazılmamalıdır. Environment variable veya secret manager kullanılmalıdır.
app.config["SECRET_KEY"] = "super-secret-key-123"


DB_NAME = "users.db"


def get_db_connection():
    return sqlite3.connect(DB_NAME)


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password TEXT,
            role TEXT
        )
    """)

    # ZAFİYET-02: Düz metin / zayıf parola saklama örneği
    # Parolalar asla plain text veya zayıf hash ile tutulmamalıdır.
    # bcrypt/argon2 gibi güçlü algoritmalar kullanılmalıdır.
    cursor.execute("DELETE FROM users")
    cursor.execute(
        "INSERT INTO users (username, password, role) VALUES ('admin', 'admin123', 'admin')"
    )
    cursor.execute(
        "INSERT INTO users (username, password, role) VALUES ('kerem', '123456', 'user')"
    )

    conn.commit()
    conn.close()


@app.route("/")
def home():
    return jsonify({
        "message": "Vulnerable demo app is running",
        "warning": "Bu uygulama bilinçli olarak zafiyetlidir."
    })


@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username", "")
    password = request.form.get("password", "")

    conn = get_db_connection()
    cursor = conn.cursor()

    # ZAFİYET-03: SQL Injection
    # Kullanıcı girdisi doğrudan SQL sorgusuna ekleniyor.
    # Örnek saldırı:
    # username: admin' --
    # password: anything
    query = f"SELECT id, username, role FROM users WHERE username = '{username}' AND password = '{password}'"

    cursor.execute(query)
    user = cursor.fetchone()
    conn.close()

    if user:
        return jsonify({
            "status": "success",
            "user_id": user[0],
            "username": user[1],
            "role": user[2]
        })

    return jsonify({"status": "failed"}), 401


@app.route("/search")
def search():
    keyword = request.args.get("q", "")

    # ZAFİYET-04: Reflected XSS
    # Kullanıcıdan gelen veri HTML içine escape edilmeden basılıyor.
    # Örnek:
    # /search?q=<script>alert('xss')</script>
    html = f"""
    <html>
        <body>
            <h1>Search Result</h1>
            <p>You searched for: {keyword}</p>
        </body>
    </html>
    """

    return render_template_string(html)


@app.route("/run")
def run_command():
    cmd = request.args.get("cmd", "echo hello")

    # ZAFİYET-05: Command Injection
    # Kullanıcıdan alınan komut doğrudan shell=True ile çalıştırılıyor.
    # Gerçek sistemde shell=True ve doğrudan kullanıcı komutu kullanılmamalıdır.
    result = subprocess.check_output(cmd, shell=True, text=True)

    return jsonify({
        "command": cmd,
        "output": result
    })


@app.route("/read-file")
def read_file():
    filename = request.args.get("file", "notes.txt")

    # ZAFİYET-06: Path Traversal
    # Kullanıcı dosya yolunu kontrol ediyor.
    # ../../ gibi path kullanımlarıyla yetkisiz dosyalar okunabilir.
    file_path = os.path.join("files", filename)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        return jsonify({
            "file": file_path,
            "content": content
        })
    except FileNotFoundError:
        return jsonify({"error": "File not found"}), 404


@app.route("/deserialize", methods=["POST"])
def deserialize_data():
    raw_data = request.get_data()

    # ZAFİYET-07: Insecure Deserialization
    # pickle, güvenilmeyen kullanıcı verisiyle kullanılmamalıdır.
    # Zararlı payload çalıştırılmasına sebep olabilir.
    data = pickle.loads(raw_data)

    return jsonify({
        "status": "deserialized",
        "data": str(data)
    })


@app.route("/hash", methods=["POST"])
def weak_hash():
    password = request.form.get("password", "")

    # ZAFİYET-08: Weak Cryptographic Hash
    # MD5 parola saklama veya güvenlik amaçlı kullanım için uygun değildir.
    hashed_password = hashlib.md5(password.encode()).hexdigest()

    return jsonify({
        "password": password,

        # ZAFİYET-09: Sensitive Data Exposure
        # Parola ve hash aynı response içinde dönülüyor.
        # Hassas bilgiler kullanıcıya veya loglara basılmamalıdır.
        "md5_hash": hashed_password
    })


@app.route("/calculate", methods=["POST"])
def calculate():
    expression = request.form.get("expression", "1+1")

    # ZAFİYET-10: Unsafe eval Usage
    # Kullanıcı girdisi eval ile çalıştırılıyor.
    # Bu durum arbitrary code execution riskine yol açar.
    result = eval(expression)

    return jsonify({
        "expression": expression,
        "result": result
    })


@app.route("/user/<user_id>")
def get_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # ZAFİYET-11: SQL Injection tekrar örneği
    # URL parametresi doğrudan sorguya ekleniyor.
    query = f"SELECT id, username, role FROM users WHERE id = {user_id}"

    cursor.execute(query)
    user = cursor.fetchone()
    conn.close()

    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "id": user[0],
        "username": user[1],
        "role": user[2]
    })


@app.route("/admin/delete-user", methods=["POST"])
def delete_user():
    user_id = request.form.get("user_id")

    # ZAFİYET-12: Missing Authentication / Authorization
    # Admin işlemi için kullanıcı kimliği veya rol kontrolü yapılmıyor.
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM users WHERE id = {user_id}")
    conn.commit()
    conn.close()

    return jsonify({
        "status": "deleted",
        "user_id": user_id
    })


if __name__ == "__main__":
    init_db()

    # ZAFİYET-13: Debug Mode Enabled
    # Debug mode production ortamında açık bırakılmamalıdır.
    app.run(host="0.0.0.0", port=5000, debug=True)
