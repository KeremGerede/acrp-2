"""
vulnerable_cli_user_manager.py

Bu dosya yalnızca yerel test / code review agent denemesi için hazırlanmıştır.
Gerçek projede veya public ortamda kullanmayın.

Çalıştırma:
    python vulnerable_cli_user_manager.py
"""

import json
import os
import pickle
import hashlib
import subprocess

# ZAFİYET-01: Hardcoded secret
# Gizli anahtarlar kod içine yazılmamalıdır. Environment variable veya secret manager kullanılmalıdır.
APP_SECRET = "cli-hardcoded-secret-123"

# ZAFİYET-02: Hassas verilerin düz metin tutulması
# Kullanıcı parolaları plain text saklanıyor. Gerçek sistemde bcrypt/argon2 kullanılmalıdır.
USERS = [
    {
        "id": 1,
        "username": "admin",
        "password": "admin123",
        "role": "admin",
        "api_key": "ADMIN-API-KEY-123"
    },
    {
        "id": 2,
        "username": "kerem",
        "password": "123456",
        "role": "user",
        "api_key": "USER-API-KEY-456"
    }
]


def login():
    username = input("Username: ")
    password = input("Password: ")

    # ZAFİYET-03: Sensitive Data Logging
    # Kullanıcı adı ve parola doğrudan log dosyasına yazılıyor.
    with open("login_attempts.log", "a", encoding="utf-8") as log_file:
        log_file.write(f"username={username}, password={password}\n")

    for user in USERS:
        if user["username"] == username and user["password"] == password:
            print("Login successful")

            # ZAFİYET-04: Sensitive Data Exposure
            # API key gibi hassas bilgiler kullanıcıya gösteriliyor.
            print(f"Your API key: {user['api_key']}")
            return user

    print("Invalid credentials")
    return None


def export_user_data(user):
    filename = input("Export filename: ")

    # ZAFİYET-05: Path Traversal / Arbitrary File Write
    # Kullanıcı dosya adını kontrol ediyor. ../ ile istenmeyen dizinlere yazabilir.
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(user, f, indent=2)

    print(f"User data exported to {filename}")


def import_backup():
    filename = input("Backup file path: ")

    # ZAFİYET-06: Insecure Deserialization
    # pickle güvenilmeyen dosyalarla kullanılmamalıdır.
    # Zararlı pickle içeriği kod çalıştırmaya sebep olabilir.
    with open(filename, "rb") as f:
        data = pickle.load(f)

    print("Backup imported:")
    print(data)


def calculate_score():
    expression = input("Score formula: ")

    # ZAFİYET-07: Unsafe eval Usage
    # Kullanıcı girdisi eval ile çalıştırılıyor.
    # Bu durum arbitrary code execution riskine yol açabilir.
    result = eval(expression)

    print(f"Result: {result}")


def run_system_check():
    command = input("System command: ")

    # ZAFİYET-08: Command Injection
    # Kullanıcıdan gelen komut doğrudan shell=True ile çalıştırılıyor.
    # Güvenli yaklaşımda shell kullanılmamalı ve komutlar whitelist edilmelidir.
    output = subprocess.check_output(command, shell=True, text=True)

    print(output)


def hash_password_demo():
    password = input("Password to hash: ")

    # ZAFİYET-09: Weak Cryptographic Hash
    # MD5 parola saklama veya güvenlik amaçlı kullanım için uygun değildir.
    md5_hash = hashlib.md5(password.encode()).hexdigest()

    # ZAFİYET-10: Sensitive Data Exposure
    # Parola ve hash birlikte ekrana basılıyor.
    print(f"Password: {password}")
    print(f"MD5 Hash: {md5_hash}")


def read_file():
    filename = input("File path to read: ")

    # ZAFİYET-11: Arbitrary File Read
    # Kullanıcının verdiği herhangi bir dosya yolu okunuyor.
    # Base directory ve izin kontrolü yapılmalıdır.
    if not os.path.exists(filename):
        print("File not found")
        return

    with open(filename, "r", encoding="utf-8", errors="ignore") as f:
        print(f.read())


def admin_delete_user():
    user_id = int(input("User ID to delete: "))

    # ZAFİYET-12: Missing Authentication / Authorization
    # Admin işlemi olmasına rağmen kullanıcının admin olup olmadığı kontrol edilmiyor.
    global USERS
    USERS = [user for user in USERS if user["id"] != user_id]

    print(f"User {user_id} deleted")


def main():
    current_user = None

    while True:
        print("\n--- Vulnerable CLI User Manager ---")
        print("1. Login")
        print("2. Export current user data")
        print("3. Import backup")
        print("4. Calculate score")
        print("5. Run system check")
        print("6. Hash password demo")
        print("7. Read file")
        print("8. Admin delete user")
        print("9. Exit")

        choice = input("Choice: ")

        if choice == "1":
            current_user = login()
        elif choice == "2":
            if current_user:
                export_user_data(current_user)
            else:
                print("Please login first")
        elif choice == "3":
            import_backup()
        elif choice == "4":
            calculate_score()
        elif choice == "5":
            run_system_check()
        elif choice == "6":
            hash_password_demo()
        elif choice == "7":
            read_file()
        elif choice == "8":
            admin_delete_user()
        elif choice == "9":
            break
        else:
            print("Invalid choice")


if __name__ == "__main__":
    main()
