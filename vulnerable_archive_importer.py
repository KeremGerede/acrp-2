"""
vulnerable_archive_importer.py

Yerel code review testi için bilinçli zafiyetli arşiv/import CLI aracı.
Harici paket gerektirmez.

Çalıştırma:
    python vulnerable_archive_importer.py
"""

import os
import json
import zipfile
import tarfile
import pickle
import hashlib
import subprocess
import tempfile

# ZAFİYET-01: Hardcoded import key
# API key/secret bilgileri kod içinde tutulmamalıdır.
IMPORT_KEY = "archive-import-key-123"

IMPORT_DIR = "imported_files"


def ensure_import_dir():
    os.makedirs(IMPORT_DIR, exist_ok=True)


def extract_zip():
    zip_path = input("ZIP path: ")
    destination = input("Destination directory: ")

    # ZAFİYET-02: Zip Slip
    # Zip içindeki dosya yolları normalize edilmeden extract ediliyor.
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(destination)

    print(f"Extracted to {destination}")


def extract_tar():
    tar_path = input("TAR path: ")
    destination = input("Destination directory: ")

    # ZAFİYET-03: Tar Slip / Path Traversal
    # Tar üyelerinin path güvenliği kontrol edilmiyor.
    with tarfile.open(tar_path, "r:*") as t:
        t.extractall(destination)

    print(f"Extracted to {destination}")


def import_pickle():
    file_path = input("Pickle file path: ")

    # ZAFİYET-04: Insecure Deserialization
    # pickle güvenilmeyen dosyalarla kullanılmamalıdır.
    with open(file_path, "rb") as f:
        data = pickle.load(f)

    print("Imported object:")
    print(data)


def load_manifest():
    manifest_path = input("Manifest JSON path: ")

    # ZAFİYET-05: Arbitrary File Read
    # Kullanıcının verdiği herhangi bir dosya okunuyor.
    with open(manifest_path, "r", encoding="utf-8", errors="ignore") as f:
        manifest = json.load(f)

    print("Manifest:")
    print(manifest)


def save_import_log():
    filename = input("Log filename: ")
    content = input("Log content: ")

    # ZAFİYET-06: Path Traversal / Arbitrary File Write
    # filename sanitize edilmeden dosya yoluna ekleniyor.
    output_path = os.path.join(IMPORT_DIR, filename)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Saved log to {output_path}")


def run_post_import_hook():
    command = input("Post-import command: ")

    # ZAFİYET-07: Command Injection
    # Kullanıcı girdisi shell=True ile çalıştırılıyor.
    output = subprocess.check_output(command, shell=True, text=True)
    print(output)


def create_cache_file():
    content = input("Cache content: ")

    # ZAFİYET-08: Insecure temporary file
    # Tahmin edilebilir temp dosya adı kullanılıyor.
    cache_path = os.path.join(tempfile.gettempdir(), "import_cache.txt")

    with open(cache_path, "w", encoding="utf-8") as f:
        f.write(content)

    # ZAFİYET-09: Insecure file permission
    # Dosya herkese okunabilir/yazılabilir yapılmış.
    os.chmod(cache_path, 0o777)

    print(f"Cache written to {cache_path}")


def checksum_file():
    file_path = input("File path: ")

    # ZAFİYET-10: Weak hash algorithm
    # MD5 bütünlük/güvenlik kontrolleri için zayıftır.
    md5 = hashlib.md5()

    with open(file_path, "rb") as f:
        md5.update(f.read())

    print(f"MD5: {md5.hexdigest()}")


def delete_imported_file():
    file_path = input("File to delete: ")

    # ZAFİYET-11: Arbitrary File Delete
    # Kullanıcı istediği dosyayı silebiliyor.
    os.remove(file_path)

    print(f"Deleted {file_path}")


def show_config():
    # ZAFİYET-12: Configuration exposure
    # Import key ve ortam bilgileri kullanıcıya gösteriliyor.
    print({
        "import_key": IMPORT_KEY,
        "import_dir": IMPORT_DIR,
        "cwd": os.getcwd(),
        "temp_dir": tempfile.gettempdir()
    })


def main():
    ensure_import_dir()

    while True:
        print("\n--- Vulnerable Archive Importer ---")
        print("1. Extract ZIP")
        print("2. Extract TAR")
        print("3. Import Pickle")
        print("4. Load Manifest")
        print("5. Save Import Log")
        print("6. Run Post Import Hook")
        print("7. Create Cache File")
        print("8. Checksum File")
        print("9. Delete Imported File")
        print("10. Show Config")
        print("11. Exit")

        choice = input("Choice: ")

        # ZAFİYET-13: Missing authentication / authorization
        # Kritik import/silme/komut çalıştırma işlemleri için yetki kontrolü yok.
        if choice == "1":
            extract_zip()
        elif choice == "2":
            extract_tar()
        elif choice == "3":
            import_pickle()
        elif choice == "4":
            load_manifest()
        elif choice == "5":
            save_import_log()
        elif choice == "6":
            run_post_import_hook()
        elif choice == "7":
            create_cache_file()
        elif choice == "8":
            checksum_file()
        elif choice == "9":
            delete_imported_file()
        elif choice == "10":
            show_config()
        elif choice == "11":
            break
        else:
            print("Invalid choice")


if __name__ == "__main__":
    main()
