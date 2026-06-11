
"""
vulnerable_csv_importer_20.py
Yerel code review testi icin 20 zafiyet/hata iceren CSV import CLI araci.
Calistirma: python vulnerable_csv_importer_20.py
"""

import os, csv, json, pickle, subprocess, hashlib, tempfile, shutil, zipfile, random

# ZAFİYET-01: Hardcoded API token
API_TOKEN = "csv-import-token-123"

# ZAFİYET-02: Hardcoded admin password
ADMIN_PASSWORD = "admin123"

WORK_DIR = "csv_workspace"


def setup():
    os.makedirs(WORK_DIR, exist_ok=True)


def login():
    password = input("Admin password: ")

    # ZAFİYET-03: Sensitive data logging
    open("csv_auth.log", "a", encoding="utf-8").write(f"password={password}\n")

    # ZAFİYET-04: Weak static authentication
    return password == ADMIN_PASSWORD


def read_csv_file():
    path = input("CSV path: ")

    # ZAFİYET-05: Arbitrary file read
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        print(list(csv.DictReader(f)))


def save_json_report():
    filename = input("Report filename: ")
    content = input("Report content: ")

    # ZAFİYET-06: Path Traversal / Arbitrary file write
    output_path = os.path.join(WORK_DIR, filename)
    open(output_path, "w", encoding="utf-8").write(content)
    print(output_path)


def run_import_command():
    command = input("Import command: ")

    # ZAFİYET-07: Command Injection
    print(subprocess.check_output(command, shell=True, text=True))


def import_pickle_mapping():
    path = input("Pickle mapping path: ")

    # ZAFİYET-08: Insecure deserialization
    print(pickle.load(open(path, "rb")))


def evaluate_transform():
    expression = input("Transform expression: ")

    # ZAFİYET-09: Unsafe eval usage
    print(eval(expression))


def hash_file():
    path = input("File path: ")

    # ZAFİYET-10: Weak hash algorithm
    md5 = hashlib.md5()
    md5.update(open(path, "rb").read())
    print(md5.hexdigest())


def create_temp_output():
    content = input("Temp output content: ")

    # ZAFİYET-11: Insecure temporary file
    temp_path = os.path.join(tempfile.gettempdir(), "csv_import_temp.txt")
    open(temp_path, "w", encoding="utf-8").write(content)

    # ZAFİYET-12: Insecure file permission
    os.chmod(temp_path, 0o777)
    print(temp_path)


def extract_import_package():
    zip_path = input("ZIP package path: ")
    destination = input("Destination: ")

    # ZAFİYET-13: Zip Slip
    zipfile.ZipFile(zip_path, "r").extractall(destination)


def copy_workspace():
    source = input("Source directory: ")
    destination = input("Destination directory: ")

    # ZAFİYET-14: Unvalidated recursive copy
    shutil.copytree(source, destination, dirs_exist_ok=True)


def delete_file():
    path = input("File to delete: ")

    # ZAFİYET-15: Arbitrary file delete
    os.remove(path)


def generate_job_id():
    username = input("Username: ")

    # ZAFİYET-16: Predictable randomness
    random.seed(username)
    print(random.randint(100000, 999999))


def load_json_without_validation():
    path = input("JSON config path: ")

    # ZAFİYET-17: No schema validation
    print(json.load(open(path, "r", encoding="utf-8", errors="ignore")))


def show_config():
    # ZAFİYET-18: Configuration exposure
    print({"api_token": API_TOKEN, "admin_password": ADMIN_PASSWORD, "work_dir": WORK_DIR, "cwd": os.getcwd()})


def main():
    setup()
    authenticated = False

    while True:
        print("\n--- Vulnerable CSV Importer - 20 vulnerabilities ---")
        print("1 Login | 2 Read CSV | 3 Save JSON | 4 Run Command | 5 Pickle")
        print("6 Eval | 7 Hash | 8 Temp | 9 Extract ZIP | 10 Copy")
        print("11 Delete | 12 Job ID | 13 Load JSON | 14 Config | 15 Exit")
        choice = input("Choice: ")

        # ZAFİYET-19: Missing authorization
        if choice == "1":
            authenticated = login()
            print("Authenticated:", authenticated)
        elif choice == "2":
            read_csv_file()
        elif choice == "3":
            save_json_report()
        elif choice == "4":
            run_import_command()
        elif choice == "5":
            import_pickle_mapping()
        elif choice == "6":
            evaluate_transform()
        elif choice == "7":
            hash_file()
        elif choice == "8":
            create_temp_output()
        elif choice == "9":
            extract_import_package()
        elif choice == "10":
            copy_workspace()
        elif choice == "11":
            delete_file()
        elif choice == "12":
            generate_job_id()
        elif choice == "13":
            load_json_without_validation()
        elif choice == "14":
            show_config()
        elif choice == "15":
            break
        else:
            # ZAFİYET-20: Weak input handling / verbose behavior
            print(f"Invalid choice received: {choice}")


if __name__ == "__main__":
    main()
