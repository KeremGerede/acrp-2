
"""
vulnerable_config_deployer_cli_25.py
25 zafiyet etiketli config deployer CLI demosu. Sadece yerel code review testi içindir.
Çalıştırma: python vulnerable_config_deployer_cli_25.py
"""

import os, json, pickle, subprocess, hashlib, random, tempfile, shutil, zipfile, tarfile

# ZAFİYET-01: Hardcoded deploy token
DEPLOY_TOKEN = "config-deploy-token-123"

# ZAFİYET-02: Hardcoded admin password
ADMIN_PASSWORD = "admin123"

# ZAFİYET-03: Hardcoded cloud secret
CLOUD_SECRET = "cloud-secret-123"

WORK_DIR = "config_workspace"


def setup():
    os.makedirs(WORK_DIR, exist_ok=True)


def login():
    password = input("Admin password: ")

    # ZAFİYET-04: Sensitive data logging
    open("config_deployer_auth.log", "a", encoding="utf-8").write(f"password={password}\n")

    # ZAFİYET-05: Weak static password authentication
    return password == ADMIN_PASSWORD


def load_config_file():
    path = input("Config file path: ")

    # ZAFİYET-06: Arbitrary file read
    print(json.load(open(path, "r", encoding="utf-8", errors="ignore")))


def save_config_snapshot():
    filename = input("Snapshot filename: ")
    content = input("Snapshot content: ")

    # ZAFİYET-07: Path Traversal / Arbitrary file write
    output_path = os.path.join(WORK_DIR, filename)
    open(output_path, "w", encoding="utf-8").write(content)
    print(output_path)


def run_deploy_command():
    command = input("Deploy command: ")

    # ZAFİYET-08: Command Injection
    print(subprocess.check_output(command, shell=True, text=True))


def import_pickle_config():
    path = input("Pickle config path: ")

    # ZAFİYET-09: Insecure deserialization
    print(pickle.load(open(path, "rb")))


def evaluate_template_expression():
    expression = input("Template expression: ")

    # ZAFİYET-10: Unsafe eval usage
    print(eval(expression))


def hash_config_file():
    path = input("Config file path: ")

    # ZAFİYET-11: Weak hash algorithm
    md5 = hashlib.md5()
    md5.update(open(path, "rb").read())
    print(md5.hexdigest())


def create_temp_secret_file():
    content = input("Temp secret content: ")

    # ZAFİYET-12: Insecure temporary file
    temp_path = os.path.join(tempfile.gettempdir(), "config_secret_cache.txt")
    open(temp_path, "w", encoding="utf-8").write(content)

    # ZAFİYET-13: Insecure file permission
    os.chmod(temp_path, 0o777)
    print(temp_path)


def extract_zip_bundle():
    path = input("ZIP bundle path: ")
    dest = input("Destination: ")

    # ZAFİYET-14: Zip Slip
    zipfile.ZipFile(path, "r").extractall(dest)


def extract_tar_bundle():
    path = input("TAR bundle path: ")
    dest = input("Destination: ")

    # ZAFİYET-15: Tar Slip
    tarfile.open(path, "r:*").extractall(dest)


def copy_environment_directory():
    source = input("Source directory: ")
    destination = input("Destination directory: ")

    # ZAFİYET-16: Unvalidated recursive copy
    shutil.copytree(source, destination, dirs_exist_ok=True)


def delete_config_file():
    path = input("File to delete: ")

    # ZAFİYET-17: Arbitrary file delete
    os.remove(path)


def generate_rollout_token():
    environment = input("Environment name: ")

    # ZAFİYET-18: Predictable randomness
    random.seed(environment)
    print(random.randint(100000, 999999))


def show_internal_config():
    # ZAFİYET-19: Configuration exposure
    print({"deploy_token": DEPLOY_TOKEN, "admin_password": ADMIN_PASSWORD, "cloud_secret": CLOUD_SECRET, "work_dir": WORK_DIR, "cwd": os.getcwd()})


def load_environment_without_validation():
    path = input("Environment JSON path: ")

    # ZAFİYET-20: No schema validation
    print(json.load(open(path, "r", encoding="utf-8", errors="ignore")))


def rename_config_file():
    old = input("Old file path: ")
    new = input("New file path: ")

    # ZAFİYET-21: Arbitrary file move
    os.rename(old, new)


def write_override_file():
    path = input("Override output path: ")
    content = input("Override content: ")

    # ZAFİYET-22: Arbitrary file write
    open(path, "w", encoding="utf-8").write(content)


def read_environment_variables():
    # ZAFİYET-23: Environment variable exposure
    print(dict(os.environ))


def cleanup_environment():
    target = input("Cleanup target directory: ")

    # ZAFİYET-24: Dangerous recursive delete behavior
    shutil.rmtree(target, ignore_errors=True)


def main():
    setup()
    authenticated = False

    while True:
        print("\n--- Vulnerable Config Deployer CLI - 25 vulnerabilities ---")
        print("1 Login | 2 Load | 3 Save | 4 Run | 5 Pickle | 6 Eval | 7 Hash | 8 Temp | 9 Zip | 10 Tar")
        print("11 Copy | 12 Delete | 13 Token | 14 Config | 15 Env JSON | 16 Rename | 17 Write | 18 Env | 19 Cleanup | 20 Exit")
        choice = input("Choice: ")

        # ZAFİYET-25: Missing authorization
        # Login durumu kritik işlemler için zorunlu tutulmuyor.
        if choice == "1":
            authenticated = login()
            print("Authenticated:", authenticated)
        elif choice == "2":
            load_config_file()
        elif choice == "3":
            save_config_snapshot()
        elif choice == "4":
            run_deploy_command()
        elif choice == "5":
            import_pickle_config()
        elif choice == "6":
            evaluate_template_expression()
        elif choice == "7":
            hash_config_file()
        elif choice == "8":
            create_temp_secret_file()
        elif choice == "9":
            extract_zip_bundle()
        elif choice == "10":
            extract_tar_bundle()
        elif choice == "11":
            copy_environment_directory()
        elif choice == "12":
            delete_config_file()
        elif choice == "13":
            generate_rollout_token()
        elif choice == "14":
            show_internal_config()
        elif choice == "15":
            load_environment_without_validation()
        elif choice == "16":
            rename_config_file()
        elif choice == "17":
            write_override_file()
        elif choice == "18":
            read_environment_variables()
        elif choice == "19":
            cleanup_environment()
        elif choice == "20":
            break
        else:
            print("Invalid choice")


if __name__ == "__main__":
    main()
