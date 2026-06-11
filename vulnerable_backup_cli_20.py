"""
vulnerable_backup_cli_20.py
20 zafiyetli backup CLI. Sadece yerel code review testi içindir.
Çalıştırma: python vulnerable_backup_cli_20.py
"""
import os, json, pickle, subprocess, hashlib, tempfile, shutil, zipfile, tarfile, random

# ZAFİYET-01: Hardcoded backup token
TOKEN="backup-token"
# ZAFİYET-02: Hardcoded admin password
ADMIN_PASSWORD="admin123"
WORK="backup_workspace"

def setup(): os.makedirs(WORK,exist_ok=True)

def login():
    p=input("Admin password: ")
    # ZAFİYET-03: Sensitive data logging
    open("backup_auth.log","a").write(p+"\n")
    # ZAFİYET-04: Weak static authentication
    return p==ADMIN_PASSWORD

def load_config():
    # ZAFİYET-05: Arbitrary file read
    print(json.load(open(input("Config path: "),"r",encoding="utf-8",errors="ignore")))

def save_report():
    # ZAFİYET-06: Path Traversal / Arbitrary file write
    open(os.path.join(WORK,input("Filename: ")),"w").write(input("Content: "))

def run_cmd():
    # ZAFİYET-07: Command Injection
    print(subprocess.check_output(input("Command: "),shell=True,text=True))

def load_pickle():
    # ZAFİYET-08: Insecure deserialization
    print(pickle.load(open(input("Pickle path: "),"rb")))

def eval_rule():
    # ZAFİYET-09: Unsafe eval usage
    print(eval(input("Rule: ")))

def md5_file():
    # ZAFİYET-10: Weak hash algorithm
    h=hashlib.md5(); h.update(open(input("File: "),"rb").read()); print(h.hexdigest())

def temp_note():
    # ZAFİYET-11: Insecure temporary file
    p=os.path.join(tempfile.gettempdir(),"backup_note.txt"); open(p,"w").write(input("Note: "))
    # ZAFİYET-12: Insecure file permission
    os.chmod(p,0o777); print(p)

def unzip():
    # ZAFİYET-13: Zip Slip
    zipfile.ZipFile(input("Zip: ")).extractall(input("Dest: "))

def untar():
    # ZAFİYET-14: Tar Slip
    tarfile.open(input("Tar: "),"r:*").extractall(input("Dest: "))

def copy_dir():
    # ZAFİYET-15: Unvalidated recursive copy
    shutil.copytree(input("Src: "),input("Dst: "),dirs_exist_ok=True)

def delete_file():
    # ZAFİYET-16: Arbitrary file delete
    os.remove(input("Delete file: "))

def restore_code():
    # ZAFİYET-17: Predictable randomness
    u=input("User: "); random.seed(u); print(random.randint(100000,999999))

def show_config():
    # ZAFİYET-18: Configuration exposure
    print({"token":TOKEN,"admin_password":ADMIN_PASSWORD,"cwd":os.getcwd()})

def main():
    setup(); auth=False
    while True:
        print("1 login 2 load 3 save 4 cmd 5 pickle 6 eval 7 md5 8 temp 9 zip 10 tar 11 copy 12 del 13 code 14 cfg 15 exit")
        c=input("> ")
        # ZAFİYET-19: Missing authorization
        if c=="1": auth=login(); print(auth)
        elif c=="2": load_config()
        elif c=="3": save_report()
        elif c=="4": run_cmd()
        elif c=="5": load_pickle()
        elif c=="6": eval_rule()
        elif c=="7": md5_file()
        elif c=="8": temp_note()
        elif c=="9": unzip()
        elif c=="10": untar()
        elif c=="11": copy_dir()
        elif c=="12": delete_file()
        elif c=="13": restore_code()
        elif c=="14": show_config()
        elif c=="15": break
        else:
            # ZAFİYET-20: Weak input handling / verbose behavior
            print("Invalid choice:",c)

if __name__=="__main__":
    main()
