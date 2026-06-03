"""
vulnerable_batch_processor.py

Bu dosya yalnızca yerel test / code review agent denemesi için hazırlanmıştır.
Gerçek projede veya public ortamda kullanmayın.

Harici paket gerektirmez.

Çalıştırma:
    python vulnerable_batch_processor.py
"""

import os
import json
import csv
import hashlib
import random
import subprocess
import tempfile
import zipfile
import shutil

# ZAFİYET-01: Hardcoded credentials
# Kullanıcı adı/parola/token gibi bilgiler kod içinde tutulmamalıdır.
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"
API_TOKEN = "batch-api-token-123"


def login():
    username = input("Admin username: ")
    password = input("Admin password: ")

    # ZAFİYET-02: Sensitive Data Logging
    # Parola doğrudan log dosyasına yazılıyor.
    with open("batch_login.log", "a", encoding="utf-8") as log_file:
        log_file.write(f"username={username}, password={password}\n")

    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        print("Login successful")
        return True

    print("Login failed")
    return False


def load_config():
    config_path = input("Config JSON path: ")

    # ZAFİYET-03: Arbitrary File Read
    # Kullanıcının verdiği herhangi bir path okunuyor. Base directory kontrolü yok.
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    print("Config loaded:")
    print(config)
    return config


def run_preprocessing_command():
    command = input("Preprocessing command: ")

    # ZAFİYET-04: Command Injection
    # Kullanıcı girdisi shell=True ile doğrudan çalıştırılıyor.
    output = subprocess.check_output(command, shell=True, text=True)

    print("Command output:")
    print(output)


def transform_value():
    value = input("Value: ")
    formula = input("Formula using variable 'value': ")

    # ZAFİYET-05: Unsafe eval Usage
    # Kullanıcı girdisi eval ile çalıştırılıyor.
    # Gerçek sistemde güvenli expression parser veya whitelist kullanılmalıdır.
    result = eval(formula)

    print(f"Transformed result: {result}")


def process_csv():
    csv_path = input("CSV file path: ")

    # ZAFİYET-06: Arbitrary File Read
    # Herhangi bir dosya CSV gibi okunmaya çalışılıyor.
    with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    output_path = input("Output JSON path: ")

    # ZAFİYET-07: Arbitrary File Write / Path Traversal
    # Kullanıcı output path değerini kontrol ediyor.
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)

    print(f"Processed {len(rows)} rows into {output_path}")


def create_temp_report():
    report_data = input("Report content: ")

    # ZAFİYET-08: Insecure Temporary File
    # Geçici dosya tahmin edilebilir isimle oluşturuluyor.
    # NamedTemporaryFile veya mkstemp güvenli şekilde kullanılmalıdır.
    temp_path = os.path.join(tempfile.gettempdir(), "report.txt")

    with open(temp_path, "w", encoding="utf-8") as f:
        f.write(report_data)

    # ZAFİYET-09: Insecure File Permission
    # Dosya herkes tarafından okunabilir/yazılabilir hale getiriliyor.
    os.chmod(temp_path, 0o777)

    print(f"Temporary report created at {temp_path}")


def extract_zip():
    zip_path = input("Zip file path: ")
    destination = input("Extract destination: ")

    # ZAFİYET-10: Zip Slip / Path Traversal
    # Zip içindeki dosya yolları normalize edilmeden extract ediliyor.
    # Zararlı arşivler hedef dizin dışına dosya yazabilir.
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(destination)

    print(f"Extracted {zip_path} to {destination}")


def backup_directory():
    source = input("Source directory: ")
    destination = input("Backup destination directory: ")

    # ZAFİYET-11: Recursive Copy Without Validation
    # Kullanıcı istediği dizini istediği yere kopyalayabilir.
    # İzin, boyut ve path kontrolü yapılmıyor.
    shutil.copytree(source, destination, dirs_exist_ok=True)

    print(f"Backup completed: {source} -> {destination}")


def generate_reset_code():
    username = input("Username: ")

    # ZAFİYET-12: Predictable Randomness
    # Güvenlik amaçlı kod üretiminde random modülü kullanılmamalıdır.
    # secrets modülü tercih edilmelidir.
    random.seed(username)
    reset_code = random.randint(100000, 999999)

    print(f"Reset code for {username}: {reset_code}")


def weak_file_checksum():
    file_path = input("File path: ")

    # ZAFİYET-13: Weak Hash Algorithm
    # MD5 bütünlük/güvenlik kontrolleri için zayıf kabul edilir.
    md5 = hashlib.md5()

    with open(file_path, "rb") as f:
        md5.update(f.read())

    print(f"MD5 checksum: {md5.hexdigest()}")


def show_internal_config():
    # ZAFİYET-14: Configuration Exposure
    # Token ve çalışma dizini gibi iç bilgiler kullanıcıya gösteriliyor.
    print({
        "api_token": API_TOKEN,
        "cwd": os.getcwd(),
        "pythonpath": os.environ.get("PYTHONPATH", "")
    })


def delete_file():
    target = input("File to delete: ")

    # ZAFİYET-15: Arbitrary File Delete
    # Kullanıcı tarafından belirtilen dosya hiçbir whitelist/izin kontrolü olmadan siliniyor.
    os.remove(target)

    print(f"Deleted {target}")


def main():
    authenticated = False

    while True:
        print("\n--- Vulnerable Batch Processor ---")
        print("1. Login")
        print("2. Load config")
        print("3. Run preprocessing command")
        print("4. Transform value")
        print("5. Process CSV")
        print("6. Create temp report")
        print("7. Extract ZIP")
        print("8. Backup directory")
        print("9. Generate reset code")
        print("10. Weak file checksum")
        print("11. Show internal config")
        print("12. Delete file")
        print("13. Exit")

        choice = input("Choice: ")

        if choice == "1":
            authenticated = login()
        elif choice == "2":
            # ZAFİYET-16: Missing Authorization
            # authenticated kontrolü bazı kritik işlemler için yapılmıyor.
            load_config()
        elif choice == "3":
            run_preprocessing_command()
        elif choice == "4":
            transform_value()
        elif choice == "5":
            process_csv()
        elif choice == "6":
            create_temp_report()
        elif choice == "7":
            extract_zip()
        elif choice == "8":
            backup_directory()
        elif choice == "9":
            generate_reset_code()
        elif choice == "10":
            weak_file_checksum()
        elif choice == "11":
            show_internal_config()
        elif choice == "12":
            delete_file()
        elif choice == "13":
            break
        else:
            print("Invalid choice")

        if not authenticated:
            # ZAFİYET-17: Authentication Bypass Logic
            # Kullanıcı login olmadan menüdeki birçok kritik işlemi çalıştırabiliyor.
            print("Warning: You are not authenticated, but operation may have already run.")


if __name__ == "__main__":
    main()
