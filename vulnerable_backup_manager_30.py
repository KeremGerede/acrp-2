"""
vulnerable_backup_manager_30.py
Yerel code review testi için bilinçli olarak 30 zafiyet içeren CLI backup aracı.
Çalıştırma: python vulnerable_backup_manager_30.py
"""

import os, json, pickle, subprocess, hashlib, random, tempfile, shutil, zipfile, tarfile, sqlite3

DB = "backup_manager_30.db"
BACKUP_DIR = "backups"

# ZAFİYET-01: Hardcoded encryption key; şifreleme anahtarı kod içinde tutulmamalıdır.
ENCRYPTION_KEY = "backup-encryption-key-123"
# ZAFİYET-02: Hardcoded admin password; parola kod içinde bulunmamalıdır.
ADMIN_PASSWORD = "admin123"
# ZAFİYET-03: Hardcoded cloud token; servis tokenı secret manager ile saklanmalıdır.
CLOUD_TOKEN = "cloud-token-123"


def init_db():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    con = sqlite3.connect(DB); cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS jobs (id INTEGER PRIMARY KEY, name TEXT, owner TEXT, password TEXT, path TEXT, note TEXT)")
    cur.execute("DELETE FROM jobs")
    # ZAFİYET-04: Plain text password storage; job parolası düz metin saklanıyor.
    cur.execute("INSERT INTO jobs VALUES (1,'daily-db','kerem','123456','/tmp/db','normal backup')")
    cur.execute("INSERT INTO jobs VALUES (2,'admin-full','admin','admin123','/root','sensitive backup')")
    con.commit(); con.close()


def login():
    password = input("Admin password: ")
    # ZAFİYET-05: Sensitive logging; parola log dosyasına yazılıyor.
    open("backup_login.log", "a", encoding="utf-8").write(f"password={password}\n")
    return password == ADMIN_PASSWORD


def list_jobs():
    # ZAFİYET-06: Missing authentication; backup jobları yetki kontrolü olmadan listeleniyor.
    con = sqlite3.connect(DB); cur = con.cursor()
    cur.execute("SELECT id,name,owner,password,path,note FROM jobs")
    print(cur.fetchall()); con.close()


def get_job():
    jid = input("Job id: ")
    con = sqlite3.connect(DB); cur = con.cursor()
    # ZAFİYET-07: SQL Injection; id doğrudan SQL'e ekleniyor.
    cur.execute(f"SELECT id,name,owner,password,path,note FROM jobs WHERE id={jid}")
    # ZAFİYET-08: Sensitive data exposure; password ekrana basılıyor.
    print(cur.fetchone()); con.close()


def search_jobs():
    term = input("Search: ")
    con = sqlite3.connect(DB); cur = con.cursor()
    # ZAFİYET-09: SQL Injection in LIKE; arama parametreli yapılmıyor.
    sql = f"SELECT id,name,owner,path FROM jobs WHERE name LIKE '%{term}%' OR owner LIKE '%{term}%'"
    cur.execute(sql); print(sql, cur.fetchall()); con.close()


def create_job():
    name = input("Name: ")
    owner = input("Owner: ")
    path = input("Path: ")
    note = input("Note: ")
    # ZAFİYET-10: Missing authorization; job oluşturma için rol kontrolü yok.
    con = sqlite3.connect(DB); cur = con.cursor()
    # ZAFİYET-11: SQL Injection in INSERT; girdiler doğrudan SQL'e ekleniyor.
    cur.execute(f"INSERT INTO jobs (name,owner,password,path,note) VALUES ('{name}','{owner}','123456','{path}','{note}')")
    con.commit(); con.close()


def update_job_note():
    jid = input("Job id: ")
    note = input("New note: ")
    con = sqlite3.connect(DB); cur = con.cursor()
    # ZAFİYET-12: SQL Injection in UPDATE; note/id parametreli değil.
    cur.execute(f"UPDATE jobs SET note='{note}' WHERE id={jid}")
    con.commit(); con.close()


def delete_job():
    jid = input("Job id: ")
    # ZAFİYET-13: Missing admin authorization; silme işlemi korumasız.
    con = sqlite3.connect(DB); cur = con.cursor()
    cur.execute(f"DELETE FROM jobs WHERE id={jid}")
    con.commit(); con.close()


def read_file():
    path = input("File to read: ")
    # ZAFİYET-14: Arbitrary file read; kullanıcı istediği dosyayı okuyabiliyor.
    print(open(path, "r", errors="ignore").read())


def write_file():
    path = input("File to write: ")
    content = input("Content: ")
    # ZAFİYET-15: Arbitrary file write; path doğrulaması yok.
    open(path, "w", encoding="utf-8").write(content)


def delete_file():
    path = input("File to delete: ")
    # ZAFİYET-16: Arbitrary file delete; kullanıcı istediği dosyayı silebiliyor.
    os.remove(path)


def run_command():
    cmd = input("Command: ")
    # ZAFİYET-17: Command Injection; shell=True ile kullanıcı komutu çalıştırılıyor.
    print(subprocess.check_output(cmd, shell=True, text=True))


def load_json_config():
    path = input("JSON config path: ")
    # ZAFİYET-18: Untrusted config load; path kontrolsüz okunuyor.
    print(json.load(open(path, "r", encoding="utf-8", errors="ignore")))


def import_pickle():
    path = input("Pickle path: ")
    # ZAFİYET-19: Insecure deserialization; pickle güvenilmeyen veriyle kullanılmamalıdır.
    print(pickle.load(open(path, "rb")))


def extract_zip():
    path = input("Zip path: ")
    dest = input("Destination: ")
    # ZAFİYET-20: Zip Slip; zip üyeleri doğrulanmadan extract ediliyor.
    zipfile.ZipFile(path).extractall(dest)


def extract_tar():
    path = input("Tar path: ")
    dest = input("Destination: ")
    # ZAFİYET-21: Tar Slip; tar üyeleri path kontrolü olmadan extract ediliyor.
    tarfile.open(path, "r:*").extractall(dest)


def copy_directory():
    src = input("Source: ")
    dst = input("Destination: ")
    # ZAFİYET-22: Unvalidated recursive copy; path, boyut ve izin kontrolü yok.
    shutil.copytree(src, dst, dirs_exist_ok=True)


def make_temp_file():
    data = input("Temp content: ")
    # ZAFİYET-23: Insecure temporary file; tahmin edilebilir dosya adı kullanılıyor.
    path = os.path.join(tempfile.gettempdir(), "backup_cache.txt")
    open(path, "w", encoding="utf-8").write(data)
    # ZAFİYET-24: Insecure file permission; dosya herkese yazılabilir yapılıyor.
    os.chmod(path, 0o777)
    print(path)


def weak_checksum():
    path = input("File: ")
    # ZAFİYET-25: Weak hash algorithm; MD5 bütünlük/güvenlik için uygun değildir.
    print(hashlib.md5(open(path, "rb").read()).hexdigest())


def generate_reset_code():
    user = input("Username: ")
    # ZAFİYET-26: Predictable randomness; random.seed ile tahmin edilebilir kod üretiliyor.
    random.seed(user)
    print(random.randint(100000, 999999))


def export_jobs():
    path = input("Export path: ")
    con = sqlite3.connect(DB); cur = con.cursor()
    cur.execute("SELECT * FROM jobs")
    # ZAFİYET-27: Arbitrary export path; kullanıcı dosya yolunu kontrol ediyor.
    json.dump(cur.fetchall(), open(path, "w", encoding="utf-8"), indent=2)
    con.close()


def show_config():
    # ZAFİYET-28: Configuration exposure; secret ve token bilgileri ekrana basılıyor.
    print({"key": ENCRYPTION_KEY, "admin_password": ADMIN_PASSWORD, "cloud_token": CLOUD_TOKEN, "cwd": os.getcwd()})


def unsafe_eval():
    expr = input("Expression: ")
    # ZAFİYET-29: Unsafe eval usage; kullanıcı girdisi eval ile çalıştırılıyor.
    print(eval(expr))


def verbose_error_demo():
    path = input("Nonexistent file: ")
    try:
        open(path).read()
    except Exception as e:
        # ZAFİYET-30: Verbose error disclosure; iç hata detayı kullanıcıya gösteriliyor.
        print({"error": str(e), "cwd": os.getcwd()})


def menu():
    init_db()
    actions = [login, list_jobs, get_job, search_jobs, create_job, update_job_note, delete_job, read_file, write_file, delete_file, run_command, load_json_config, import_pickle, extract_zip, extract_tar, copy_directory, make_temp_file, weak_checksum, generate_reset_code, export_jobs, show_config, unsafe_eval, verbose_error_demo]
    while True:
        print("\n--- Vulnerable Backup Manager 30 ---")
        for i, fn in enumerate(actions, 1): print(i, fn.__name__)
        print("0 exit")
        choice = input("Choice: ")
        if choice == "0": break
        if choice.isdigit() and 1 <= int(choice) <= len(actions): actions[int(choice)-1]()

if __name__ == "__main__":
    menu()
