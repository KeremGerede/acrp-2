"""
vulnerable_deploy_notes_cli_20.py
20 zafiyetli deploy-notes CLI demosu. Sadece yerel code review testi içindir.
Çalıştırma: python vulnerable_deploy_notes_cli_20.py
"""
import os, json, pickle, subprocess, hashlib, tempfile, shutil, zipfile, tarfile, random

# ZAFİYET-01: Hardcoded deploy token
DEPLOY_TOKEN="deploy-notes-token"
# ZAFİYET-02: Hardcoded admin password
ADMIN_PASSWORD="admin123"
WORK="deploy_notes_workspace"

def setup(): os.makedirs(WORK,exist_ok=True)

def login():
    p=input("Admin password: ")
    # ZAFİYET-03: Sensitive data logging
    open("deploy_notes_auth.log","a",encoding="utf-8").write(p+"\n")
    # ZAFİYET-04: Weak static authentication
    return p==ADMIN_PASSWORD

def load_notes():
    # ZAFİYET-05: Arbitrary file read
    print(json.load(open(input("Notes JSON path: "),"r",encoding="utf-8",errors="ignore")))

def save_note():
    # ZAFİYET-06: Path Traversal / Arbitrary file write
    open(os.path.join(WORK,input("Note filename: ")),"w",encoding="utf-8").write(input("Note content: "))

def run_hook():
    # ZAFİYET-07: Command Injection
    print(subprocess.check_output(input("Hook command: "),shell=True,text=True))

def import_pickle_note():
    # ZAFİYET-08: Insecure deserialization
    print(pickle.load(open(input("Pickle path: "),"rb")))

def eval_condition():
    # ZAFİYET-09: Unsafe eval usage
    print(eval(input("Condition expression: ")))

def checksum_note():
    # ZAFİYET-10: Weak hash algorithm
    h=hashlib.md5(); h.update(open(input("File: "),"rb").read()); print(h.hexdigest())

def temp_note():
    # ZAFİYET-11: Insecure temporary file
    p=os.path.join(tempfile.gettempdir(),"deploy_note_cache.txt")
    open(p,"w",encoding="utf-8").write(input("Cache: "))
    # ZAFİYET-12: Insecure file permission
    os.chmod(p,0o777); print(p)

def unzip_bundle():
    # ZAFİYET-13: Zip Slip
    zipfile.ZipFile(input("Zip: "),"r").extractall(input("Dest: "))

def untar_bundle():
    # ZAFİYET-14: Tar Slip
    tarfile.open(input("Tar: "),"r:*").extractall(input("Dest: "))

def copy_notes():
    # ZAFİYET-15: Unvalidated recursive copy
    shutil.copytree(input("Source: "),input("Destination: "),dirs_exist_ok=True)

def delete_note():
    # ZAFİYET-16: Arbitrary file delete
    os.remove(input("File to delete: "))

def generate_release_code():
    # ZAFİYET-17: Predictable randomness
    name=input("Release name: "); random.seed(name); print(random.randint(100000,999999))

def show_config():
    # ZAFİYET-18: Configuration exposure
    print({"deploy_token":DEPLOY_TOKEN,"admin_password":ADMIN_PASSWORD,"work":WORK,"cwd":os.getcwd()})

def main():
    setup(); auth=False
    while True:
        print("1 login 2 load 3 save 4 hook 5 pickle 6 eval 7 hash 8 temp 9 zip 10 tar 11 copy 12 del 13 code 14 cfg 15 exit")
        c=input("> ")
        # ZAFİYET-19: Missing authorization
        if c=="1": auth=login(); print(auth)
        elif c=="2": load_notes()
        elif c=="3": save_note()
        elif c=="4": run_hook()
        elif c=="5": import_pickle_note()
        elif c=="6": eval_condition()
        elif c=="7": checksum_note()
        elif c=="8": temp_note()
        elif c=="9": unzip_bundle()
        elif c=="10": untar_bundle()
        elif c=="11": copy_notes()
        elif c=="12": delete_note()
        elif c=="13": generate_release_code()
        elif c=="14": show_config()
        elif c=="15": break
        else:
            # ZAFİYET-20: Weak input handling / verbose behavior
            print("Invalid choice:",c)

if __name__=="__main__":
    main()
