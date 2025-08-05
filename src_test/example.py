import os
import sqlite3
import requests

# 🔑 Hardcoded secret (Secrets Detection)
AWS_SECRET_KEY = "AKIAIOSFODNN7EXAMPLE"

# 🔐 Hardcoded password (CWE / Secrets)
PASSWORD = "p@ssw0rd123"

# 💡 Global variable (bad practice)
db_conn = None

def connect_db():
    global db_conn
    # ⚠️ Insecure: No input sanitization (SQL Injection - OWASP A1)
    user_input = input("Enter username: ")
    query = f"SELECT * FROM users WHERE username = '{user_input}'"
    db_conn = sqlite3.connect("users.db")
    cursor = db_conn.cursor()
    cursor.execute(query)
    print(cursor.fetchall())

def unsafe_eval():
    # 🔍 Using eval (Security Audit)
    expr = input("Enter math expression: ")
    result = eval(expr)
    print(result)

def command_injection():
    # ⚠️ Command injection (CWE-78)
    filename = input("Enter filename to list: ")
    os.system("ls -l " + filename)

def send_data():
    data = {
        "secret": AWS_SECRET_KEY
    }
    # 🔍 Using unencrypted HTTP (Security Audit)
    requests.post("http://example.com/submit", data=data)

def download_url():
    # 🔐 SSRF risk (OWASP A10)
    url = input("Enter URL to fetch: ")
    r = requests.get(url)
    print(r.text)

def insecure_file_permission():
    # 🔍 Unsafe permission (e.g. 0777)
    with open("temp.txt", "w") as f:
        f.write("temporary")
    os.chmod("temp.txt", 0o777)

def unused_function():
    # 💡 Dead code
    print("This function is never called")

# Entry point
if __name__ == "__main__":
    connect_db()
    unsafe_eval()
    command_injection()
    send_data()
    download_url()
    insecure_file_permission()
