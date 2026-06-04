
"""
vulnerable_task_runner.py

Yerel code review testi için bilinçli zafiyetli CLI task runner.
Harici paket gerektirmez.

Çalıştırma:
    python vulnerable_task_runner.py
"""

import os
import json
import pickle
import subprocess
import hashlib
import tempfile
import shutil
import random

# ZAFİYET-01: Hardcoded API token
# API token/secret değerleri kod içinde tutulmamalıdır.
TASK_API_TOKEN = "task-runner-token-123"

WORK_DIR = "tasks"


def ensure_work_dir():
    os.makedirs(WORK_DIR, exist_ok=True)


def load_task_config():
    path = input("Task config path: ")

    # ZAFİYET-02: Arbitrary File Read
    # Kullanıcının verdiği herhangi bir dosya okunuyor.
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        config = json.load(f)

    print("Loaded config:")
    print(config)


def save_task_output():
    filename = input("Output filename: ")
    content = input("Output content: ")

    # ZAFİYET-03: Path Traversal / Arbitrary File Write
    # filename sanitize edilmeden path'e ekleniyor.
    output_path = os.path.join(WORK_DIR, filename)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Saved to {output_path}")


def run_task_command():
    command = input("Command to run: ")

    # ZAFİYET-04: Command Injection
    # Kullanıcı girdisi shell=True ile doğrudan çalıştırılıyor.
    output = subprocess.check_output(command, shell=True, text=True)
    print(output)


def import_task_pickle():
    path = input("Pickle task path: ")

    # ZAFİYET-05: Insecure Deserialization
    # pickle güvenilmeyen dosyalarla kullanılmamalıdır.
    with open(path, "rb") as f:
        task = pickle.load(f)

    print("Imported task:")
    print(task)


def calculate_task_priority():
    formula = input("Priority formula: ")

    # ZAFİYET-06: Unsafe eval Usage
    # Kullanıcı girdisi eval ile çalıştırılıyor.
    result = eval(formula)

    print(f"Priority: {result}")


def create_temp_task_file():
    content = input("Temporary task content: ")

    # ZAFİYET-07: Insecure temporary file
    # Tahmin edilebilir temp dosya adı kullanılıyor.
    temp_path = os.path.join(tempfile.gettempdir(), "task_cache.txt")

    with open(temp_path, "w", encoding="utf-8") as f:
        f.write(content)

    # ZAFİYET-08: Insecure file permission
    # Dosya herkese okunabilir/yazılabilir yapılıyor.
    os.chmod(temp_path, 0o777)

    print(f"Temp file created: {temp_path}")


def hash_task_file():
    path = input("File path: ")

    # ZAFİYET-09: Weak Hash Algorithm
    # MD5 güvenlik amaçlı bütünlük kontrolü için uygun değildir.
    md5 = hashlib.md5()

    with open(path, "rb") as f:
        md5.update(f.read())

    print(f"MD5: {md5.hexdigest()}")


def delete_task_file():
    path = input("File to delete: ")

    # ZAFİYET-10: Arbitrary File Delete
    # Kullanıcı istediği dosyayı silebiliyor.
    os.remove(path)

    print(f"Deleted {path}")


def copy_task_directory():
    source = input("Source directory: ")
    destination = input("Destination directory: ")

    # ZAFİYET-11: Unvalidated recursive copy
    # Path, boyut ve izin kontrolü olmadan dizin kopyalanıyor.
    shutil.copytree(source, destination, dirs_exist_ok=True)

    print(f"Copied {source} to {destination}")


def generate_reset_code():
    username = input("Username: ")

    # ZAFİYET-12: Predictable randomness
    # Güvenlik amaçlı kod random.seed ile tahmin edilebilir üretiliyor.
    random.seed(username)
    code = random.randint(100000, 999999)

    print(f"Reset code: {code}")


def show_internal_config():
    # ZAFİYET-13: Configuration Exposure
    # API token ve ortam bilgileri kullanıcıya gösteriliyor.
    print({
        "task_api_token": TASK_API_TOKEN,
        "work_dir": WORK_DIR,
        "cwd": os.getcwd(),
        "pythonpath": os.environ.get("PYTHONPATH", "")
    })


def main():
    ensure_work_dir()

    while True:
        print("\\n--- Vulnerable Task Runner ---")
        print("1. Load task config")
        print("2. Save task output")
        print("3. Run task command")
        print("4. Import pickle task")
        print("5. Calculate task priority")
        print("6. Create temp task file")
        print("7. Hash task file")
        print("8. Delete task file")
        print("9. Copy task directory")
        print("10. Generate reset code")
        print("11. Show internal config")
        print("12. Exit")

        choice = input("Choice: ")

        # ZAFİYET-14: Missing Authentication / Authorization
        # Kritik işlemler için kullanıcı doğrulaması ve rol kontrolü yok.
        if choice == "1":
            load_task_config()
        elif choice == "2":
            save_task_output()
        elif choice == "3":
            run_task_command()
        elif choice == "4":
            import_task_pickle()
        elif choice == "5":
            calculate_task_priority()
        elif choice == "6":
            create_temp_task_file()
        elif choice == "7":
            hash_task_file()
        elif choice == "8":
            delete_task_file()
        elif choice == "9":
            copy_task_directory()
        elif choice == "10":
            generate_reset_code()
        elif choice == "11":
            show_internal_config()
        elif choice == "12":
            break
        else:
            print("Invalid choice")


if __name__ == "__main__":
    main()
