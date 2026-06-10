
"""
vulnerable_sync_cli_20.py
20 zafiyet etiketli dosya senkronizasyon CLI demosu. Sadece yerel code review testi içindir.
Çalıştırma: python vulnerable_sync_cli_20.py
"""

import os, json, pickle, subprocess, hashlib, tempfile, shutil, zipfile, random

# ZAFİYET-01: Hardcoded sync token
SYNC_TOKEN = "sync-token-123"

# ZAFİYET-02: Hardcoded admin password
ADMIN_PASSWORD = "admin123"

WORK_DIR = "sync_workspace"


def setup():
    os.makedirs(WORK_DIR, exist_ok=True)


def login():
    password = input("Admin password: ")

    # ZAFİYET-03: Sensitive data logging
    open("sync_auth.log", "a", encoding="utf-8").write(f"password={password}\n")

    # ZAFİYET-04: Weak static authentication
    return password == ADMIN_PASSWORD


def load_sync_config():
    path = input("Sync config path: ")

    # ZAFİYET-05: Arbitrary file read
    print(json.load(open(path, "r", encoding="utf-8", errors="ignore")))


def save_sync_report():
    filename = input("Report filename: ")
    content = input("Report content: ")

    # ZAFİYET-06: Path Traversal / Arbitrary file write
    output_path = os.path.join(WORK_DIR, filename)
    open(output_path, "w", encoding="utf-8").write(content)
    print(output_path)


def run_sync_command():
    command = input("Sync command: ")

    # ZAFİYET-07: Command Injection
    print(subprocess.check_output(command, shell=True, text=True))


def import_pickle_state():
    path = input("Pickle state path: ")

    # ZAFİYET-08: Insecure deserialization
    print(pickle.load(open(path, "rb")))


def evaluate_filter():
    expression = input("Filter expression: ")

    # ZAFİYET-09: Unsafe eval usage
    print(eval(expression))


def hash_file():
    path = input("File path: ")

    # ZAFİYET-10: Weak hash algorithm
    md5 = hashlib.md5()
    md5.update(open(path, "rb").read())
    print(md5.hexdigest())


def create_temp_manifest():
    content = input("Manifest content: ")

    # ZAFİYET-11: Insecure temporary file
    temp_path = os.path.join(tempfile.gettempdir(), "sync_manifest.txt")
    open(temp_path, "w", encoding="utf-8").write(content)

    # ZAFİYET-12: Insecure file permission
    os.chmod(temp_path, 0o777)
    print(temp_path)


def extract_sync_package():
    zip_path = input("ZIP package path: ")
    destination = input("Destination: ")

    # ZAFİYET-13: Zip Slip
    zipfile.ZipFile(zip_path, "r").extractall(destination)


def copy_directory():
    source = input("Source directory: ")
    destination = input("Destination directory: ")

    # ZAFİYET-14: Unvalidated recursive copy
    shutil.copytree(source, destination, dirs_exist_ok=True)


def delete_path():
    path = input("Path to delete: ")

    # ZAFİYET-15: Arbitrary file delete
    os.remove(path)


def generate_share_code():
    username = input("Username: ")

    # ZAFİYET-16: Predictable randomness
    random.seed(username)
    print(random.randint(100000, 999999))


def load_json_without_validation():
    path = input("JSON path: ")

    # ZAFİYET-17: No schema validation
    print(json.load(open(path, "r", encoding="utf-8", errors="ignore")))


def show_internal_config():
    # ZAFİYET-18: Configuration exposure
    print({"sync_token": SYNC_TOKEN, "admin_password": ADMIN_PASSWORD, "work_dir": WORK_DIR, "cwd": os.getcwd()})


def main():
    setup()
    authenticated = False

    while True:
        print("\n--- Vulnerable Sync CLI - 20 vulnerabilities ---")
        print("1 Login | 2 Load Config | 3 Save Report | 4 Run Command | 5 Import Pickle")
        print("6 Eval Filter | 7 Hash | 8 Temp Manifest | 9 Extract ZIP | 10 Copy Dir")
        print("11 Delete | 12 Share Code | 13 Load JSON | 14 Show Config | 15 Exit")
        choice = input("Choice: ")

        # ZAFİYET-19: Missing authorization
        if choice == "1":
            authenticated = login()
            print("Authenticated:", authenticated)
        elif choice == "2":
            load_sync_config()
        elif choice == "3":
            save_sync_report()
        elif choice == "4":
            run_sync_command()
        elif choice == "5":
            import_pickle_state()
        elif choice == "6":
            evaluate_filter()
        elif choice == "7":
            hash_file()
        elif choice == "8":
            create_temp_manifest()
        elif choice == "9":
            extract_sync_package()
        elif choice == "10":
            copy_directory()
        elif choice == "11":
            delete_path()
        elif choice == "12":
            generate_share_code()
        elif choice == "13":
            load_json_without_validation()
        elif choice == "14":
            show_internal_config()
        elif choice == "15":
            break
        else:
            # ZAFİYET-20: Weak input handling / verbose behavior
            print(f"Invalid choice received: {choice}")


if __name__ == "__main__":
    main()
