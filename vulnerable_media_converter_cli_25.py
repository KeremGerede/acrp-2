
"""
vulnerable_media_converter_cli_25.py

Yerel code review testi için bilinçli olarak 25 zafiyet içeren medya/dosya dönüştürme CLI aracı.
Gerçek ortamda kullanılmamalıdır.

Çalıştırma:
    python vulnerable_media_converter_cli_25.py
"""

import os
import json
import pickle
import subprocess
import hashlib
import random
import tempfile
import shutil
import zipfile
import tarfile

# ZAFİYET-01: Hardcoded API token
API_TOKEN = "media-converter-token-123"

# ZAFİYET-02: Hardcoded admin password
ADMIN_PASSWORD = "admin123"

# ZAFİYET-03: Hardcoded storage secret
STORAGE_SECRET = "storage-secret-123"

WORK_DIR = "media_workspace"


def setup():
    os.makedirs(WORK_DIR, exist_ok=True)


def login():
    password = input("Admin password: ")

    # ZAFİYET-04: Sensitive data logging
    with open("media_auth.log", "a", encoding="utf-8") as f:
        f.write(f"password={password}\n")

    # ZAFİYET-05: Weak static password authentication
    return password == ADMIN_PASSWORD


def load_job_config():
    path = input("Job config path: ")

    # ZAFİYET-06: Arbitrary file read
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        print(json.load(f))


def save_conversion_report():
    filename = input("Report filename: ")
    content = input("Report content: ")

    # ZAFİYET-07: Path Traversal / Arbitrary file write
    output_path = os.path.join(WORK_DIR, filename)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(output_path)


def run_converter_command():
    command = input("Converter command: ")

    # ZAFİYET-08: Command Injection
    output = subprocess.check_output(command, shell=True, text=True)
    print(output)


def import_pickle_preset():
    path = input("Pickle preset path: ")

    # ZAFİYET-09: Insecure deserialization
    with open(path, "rb") as f:
        print(pickle.load(f))


def calculate_quality_score():
    expression = input("Quality formula: ")

    # ZAFİYET-10: Unsafe eval usage
    print(eval(expression))


def hash_media_file():
    path = input("Media file path: ")

    # ZAFİYET-11: Weak hash algorithm
    md5 = hashlib.md5()
    with open(path, "rb") as f:
        md5.update(f.read())
    print(md5.hexdigest())


def create_temp_cache():
    content = input("Cache content: ")

    # ZAFİYET-12: Insecure temporary file
    temp_path = os.path.join(tempfile.gettempdir(), "media_cache.txt")
    with open(temp_path, "w", encoding="utf-8") as f:
        f.write(content)

    # ZAFİYET-13: Insecure file permission
    os.chmod(temp_path, 0o777)
    print(temp_path)


def extract_zip_archive():
    path = input("ZIP path: ")
    dest = input("Destination: ")

    # ZAFİYET-14: Zip Slip
    with zipfile.ZipFile(path, "r") as z:
        z.extractall(dest)


def extract_tar_archive():
    path = input("TAR path: ")
    dest = input("Destination: ")

    # ZAFİYET-15: Tar Slip
    with tarfile.open(path, "r:*") as t:
        t.extractall(dest)


def copy_media_directory():
    source = input("Source directory: ")
    destination = input("Destination directory: ")

    # ZAFİYET-16: Unvalidated recursive copy
    shutil.copytree(source, destination, dirs_exist_ok=True)


def delete_media_file():
    path = input("File to delete: ")

    # ZAFİYET-17: Arbitrary file delete
    os.remove(path)


def generate_public_link():
    filename = input("Filename: ")

    # ZAFİYET-18: Predictable public link token
    random.seed(filename)
    token = random.randint(100000, 999999)
    print(f"https://example.local/media/{filename}?token={token}")


def show_internal_config():
    # ZAFİYET-19: Configuration exposure
    print({
        "api_token": API_TOKEN,
        "admin_password": ADMIN_PASSWORD,
        "storage_secret": STORAGE_SECRET,
        "work_dir": WORK_DIR,
        "cwd": os.getcwd()
    })


def load_metadata_without_validation():
    path = input("Metadata JSON path: ")

    # ZAFİYET-20: No schema validation
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        metadata = json.load(f)

    print(metadata)


def rename_media_file():
    old = input("Old file path: ")
    new = input("New file path: ")

    # ZAFİYET-21: Arbitrary file move
    os.rename(old, new)


def write_thumbnail():
    path = input("Thumbnail output path: ")
    content = input("Thumbnail placeholder content: ")

    # ZAFİYET-22: Arbitrary file write
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def read_environment():
    # ZAFİYET-23: Environment variable exposure
    print(dict(os.environ))


def run_cleanup():
    target = input("Cleanup target directory: ")

    # ZAFİYET-24: Dangerous recursive delete behavior
    shutil.rmtree(target, ignore_errors=True)


def main():
    setup()
    authenticated = False

    while True:
        print("\n--- Vulnerable Media Converter CLI - 25 vulnerabilities ---")
        print("1. Login")
        print("2. Load job config")
        print("3. Save conversion report")
        print("4. Run converter command")
        print("5. Import pickle preset")
        print("6. Calculate quality score")
        print("7. Hash media file")
        print("8. Create temp cache")
        print("9. Extract ZIP")
        print("10. Extract TAR")
        print("11. Copy media directory")
        print("12. Delete media file")
        print("13. Generate public link")
        print("14. Show internal config")
        print("15. Load metadata")
        print("16. Rename media file")
        print("17. Write thumbnail")
        print("18. Read environment")
        print("19. Run cleanup")
        print("20. Exit")

        choice = input("Choice: ")

        # ZAFİYET-25: Missing authorization
        # Login durumu kritik işlemler için zorunlu tutulmuyor.
        if choice == "1":
            authenticated = login()
            print("Authenticated:", authenticated)
        elif choice == "2":
            load_job_config()
        elif choice == "3":
            save_conversion_report()
        elif choice == "4":
            run_converter_command()
        elif choice == "5":
            import_pickle_preset()
        elif choice == "6":
            calculate_quality_score()
        elif choice == "7":
            hash_media_file()
        elif choice == "8":
            create_temp_cache()
        elif choice == "9":
            extract_zip_archive()
        elif choice == "10":
            extract_tar_archive()
        elif choice == "11":
            copy_media_directory()
        elif choice == "12":
            delete_media_file()
        elif choice == "13":
            generate_public_link()
        elif choice == "14":
            show_internal_config()
        elif choice == "15":
            load_metadata_without_validation()
        elif choice == "16":
            rename_media_file()
        elif choice == "17":
            write_thumbnail()
        elif choice == "18":
            read_environment()
        elif choice == "19":
            run_cleanup()
        elif choice == "20":
            break
        else:
            print("Invalid choice")


if __name__ == "__main__":
    main()
