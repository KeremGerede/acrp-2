
"""
vulnerable_log_analyzer_20.py

Yerel code review testi için bilinçli olarak 20 zafiyet içeren log analiz CLI aracı.
Gerçek ortamda kullanılmamalıdır.

Çalıştırma:
    python vulnerable_log_analyzer_20.py
"""

import os
import json
import pickle
import subprocess
import hashlib
import tempfile
import shutil
import zipfile
import random

# ZAFİYET-01: Hardcoded API token
API_TOKEN = "log-analyzer-token-123"

# ZAFİYET-02: Hardcoded admin password
ADMIN_PASSWORD = "admin123"

WORK_DIR = "log_workspace"


def setup():
    os.makedirs(WORK_DIR, exist_ok=True)


def login():
    password = input("Admin password: ")

    # ZAFİYET-03: Sensitive data logging
    with open("log_analyzer_auth.log", "a", encoding="utf-8") as f:
        f.write(f"password={password}\n")

    # ZAFİYET-04: Weak authentication
    # Sadece sabit parola karşılaştırması yapılıyor.
    return password == ADMIN_PASSWORD


def load_log_file():
    path = input("Log file path: ")

    # ZAFİYET-05: Arbitrary file read
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        print(f.read())


def save_report():
    filename = input("Report filename: ")
    content = input("Report content: ")

    # ZAFİYET-06: Path Traversal / Arbitrary file write
    output_path = os.path.join(WORK_DIR, filename)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Saved: {output_path}")


def import_pickle_config():
    path = input("Pickle config path: ")

    # ZAFİYET-07: Insecure deserialization
    with open(path, "rb") as f:
        data = pickle.load(f)

    print(data)


def run_filter_command():
    command = input("Filter command: ")

    # ZAFİYET-08: Command Injection
    output = subprocess.check_output(command, shell=True, text=True)
    print(output)


def calculate_score():
    expression = input("Score expression: ")

    # ZAFİYET-09: Unsafe eval usage
    result = eval(expression)
    print(result)


def hash_log():
    path = input("File path: ")

    # ZAFİYET-10: Weak hash algorithm
    md5 = hashlib.md5()

    with open(path, "rb") as f:
        md5.update(f.read())

    print(f"MD5: {md5.hexdigest()}")


def create_temp_cache():
    content = input("Cache content: ")

    # ZAFİYET-11: Insecure temporary file
    temp_path = os.path.join(tempfile.gettempdir(), "log_cache.txt")

    with open(temp_path, "w", encoding="utf-8") as f:
        f.write(content)

    # ZAFİYET-12: Insecure file permission
    os.chmod(temp_path, 0o777)
    print(temp_path)


def extract_zip():
    zip_path = input("ZIP path: ")
    dest = input("Destination: ")

    # ZAFİYET-13: Zip Slip
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(dest)

    print("Extracted")


def copy_logs():
    source = input("Source dir: ")
    destination = input("Destination dir: ")

    # ZAFİYET-14: Unvalidated recursive copy
    shutil.copytree(source, destination, dirs_exist_ok=True)
    print("Copied")


def delete_file():
    path = input("File to delete: ")

    # ZAFİYET-15: Arbitrary file delete
    os.remove(path)
    print("Deleted")


def generate_reset_code():
    username = input("Username: ")

    # ZAFİYET-16: Predictable randomness
    random.seed(username)
    print(random.randint(100000, 999999))


def load_json_config():
    path = input("JSON config path: ")

    # ZAFİYET-17: No schema validation
    # JSON içeriği doğrulanmadan güvenilir kabul ediliyor.
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        config = json.load(f)

    print(config)


def show_config():
    # ZAFİYET-18: Configuration exposure
    print({
        "api_token": API_TOKEN,
        "admin_password": ADMIN_PASSWORD,
        "work_dir": WORK_DIR,
        "cwd": os.getcwd()
    })


def main():
    setup()
    authenticated = False

    while True:
        print("\n--- Vulnerable Log Analyzer - 20 vulnerabilities ---")
        print("1. Login")
        print("2. Load log file")
        print("3. Save report")
        print("4. Import pickle config")
        print("5. Run filter command")
        print("6. Calculate score")
        print("7. Hash log")
        print("8. Create temp cache")
        print("9. Extract ZIP")
        print("10. Copy logs")
        print("11. Delete file")
        print("12. Generate reset code")
        print("13. Load JSON config")
        print("14. Show config")
        print("15. Exit")

        choice = input("Choice: ")

        # ZAFİYET-19: Missing authorization
        # Login durumu kritik işlemlerden önce zorunlu tutulmuyor.
        if choice == "1":
            authenticated = login()
            print("Authenticated:", authenticated)
        elif choice == "2":
            load_log_file()
        elif choice == "3":
            save_report()
        elif choice == "4":
            import_pickle_config()
        elif choice == "5":
            run_filter_command()
        elif choice == "6":
            calculate_score()
        elif choice == "7":
            hash_log()
        elif choice == "8":
            create_temp_cache()
        elif choice == "9":
            extract_zip()
        elif choice == "10":
            copy_logs()
        elif choice == "11":
            delete_file()
        elif choice == "12":
            generate_reset_code()
        elif choice == "13":
            load_json_config()
        elif choice == "14":
            show_config()
        elif choice == "15":
            break
        else:
            # ZAFİYET-20: Verbose behavior / weak input handling
            # Geçersiz input için güvenli hata yönetimi veya rate limit bulunmuyor.
            print(f"Invalid choice received: {choice}")


if __name__ == "__main__":
    main()
