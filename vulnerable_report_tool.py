"""
vulnerable_report_tool.py

Yerel code review testi için bilinçli zafiyetli rapor/dosya işleme aracı.
Harici paket gerektirmez.

Çalıştırma:
    python vulnerable_report_tool.py
"""

import os
import json
import csv
import pickle
import hashlib
import tempfile
import subprocess
import shutil

# ZAFİYET-01: Hardcoded API key
# API key kod içine yazılmamalıdır.
REPORT_API_KEY = "report-api-key-123"

# ZAFİYET-02: Güvensiz varsayılan çıktı dizini
# Dosyalar sabit ve kontrolsüz dizine yazılıyor.
OUTPUT_DIR = "reports"


def ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_json_report():
    path = input("JSON report path: ")

    # ZAFİYET-03: Arbitrary File Read
    # Kullanıcının verdiği herhangi bir dosya okunuyor.
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        data = json.load(f)

    print("Loaded report:")
    print(data)


def save_report():
    filename = input("Output filename: ")
    content = input("Report content: ")

    # ZAFİYET-04: Path Traversal / Arbitrary File Write
    # filename sanitize edilmeden path'e ekleniyor.
    output_path = os.path.join(OUTPUT_DIR, filename)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Saved to {output_path}")


def import_pickle_report():
    path = input("Pickle report path: ")

    # ZAFİYET-05: Insecure Deserialization
    # pickle güvenilmeyen dosyalarla kullanılmamalıdır.
    with open(path, "rb") as f:
        report = pickle.load(f)

    print("Imported pickle report:")
    print(report)


def convert_csv_to_json():
    csv_path = input("CSV path: ")
    json_path = input("JSON output path: ")

    # ZAFİYET-06: Arbitrary File Read
    # CSV için herhangi bir dosya okunabiliyor.
    with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
        rows = list(csv.DictReader(f))

    # ZAFİYET-07: Arbitrary File Write
    # Output path kullanıcı kontrolünde.
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)

    print(f"Converted {len(rows)} rows")


def run_report_command():
    command = input("Report command: ")

    # ZAFİYET-08: Command Injection
    # Kullanıcı girdisi shell=True ile çalıştırılıyor.
    output = subprocess.check_output(command, shell=True, text=True)
    print(output)


def create_temp_file():
    content = input("Temporary content: ")

    # ZAFİYET-09: Insecure temporary file
    # Tahmin edilebilir geçici dosya adı kullanılıyor.
    temp_path = os.path.join(tempfile.gettempdir(), "report_cache.txt")

    with open(temp_path, "w", encoding="utf-8") as f:
        f.write(content)

    # ZAFİYET-10: Insecure file permission
    # Geçici dosyaya fazla geniş izin veriliyor.
    os.chmod(temp_path, 0o777)

    print(f"Temp file: {temp_path}")


def hash_report():
    path = input("File path: ")

    # ZAFİYET-11: Weak hash algorithm
    # MD5 güvenlik amaçlı bütünlük kontrolü için uygun değildir.
    md5 = hashlib.md5()

    with open(path, "rb") as f:
        md5.update(f.read())

    print(f"MD5: {md5.hexdigest()}")


def delete_report():
    path = input("File to delete: ")

    # ZAFİYET-12: Arbitrary File Delete
    # Kullanıcı tarafından belirtilen dosya kontrolsüz siliniyor.
    os.remove(path)
    print(f"Deleted {path}")


def copy_report_directory():
    source = input("Source directory: ")
    destination = input("Destination directory: ")

    # ZAFİYET-13: Unvalidated recursive copy
    # İzin, boyut ve path kontrolü olmadan dizin kopyalanıyor.
    shutil.copytree(source, destination, dirs_exist_ok=True)

    print(f"Copied {source} to {destination}")


def show_internal_settings():
    # ZAFİYET-14: Configuration exposure
    # API key ve ortam bilgileri kullanıcıya gösteriliyor.
    print({
        "report_api_key": REPORT_API_KEY,
        "output_dir": OUTPUT_DIR,
        "cwd": os.getcwd(),
        "pythonpath": os.environ.get("PYTHONPATH", "")
    })


def main():
    ensure_output_dir()

    while True:
        print("\n--- Vulnerable Report Tool ---")
        print("1. Load JSON report")
        print("2. Save report")
        print("3. Import pickle report")
        print("4. Convert CSV to JSON")
        print("5. Run report command")
        print("6. Create temp file")
        print("7. Hash report")
        print("8. Delete report")
        print("9. Copy report directory")
        print("10. Show internal settings")
        print("11. Exit")

        choice = input("Choice: ")

        # ZAFİYET-15: Missing authentication / authorization
        # Kritik işlemler için kullanıcı doğrulaması veya rol kontrolü yok.
        if choice == "1":
            load_json_report()
        elif choice == "2":
            save_report()
        elif choice == "3":
            import_pickle_report()
        elif choice == "4":
            convert_csv_to_json()
        elif choice == "5":
            run_report_command()
        elif choice == "6":
            create_temp_file()
        elif choice == "7":
            hash_report()
        elif choice == "8":
            delete_report()
        elif choice == "9":
            copy_report_directory()
        elif choice == "10":
            show_internal_settings()
        elif choice == "11":
            break
        else:
            print("Invalid choice")


if __name__ == "__main__":
    main()
