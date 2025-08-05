import os
import sqlite3
import requests
import shlex
import subprocess
import ast
from urllib.parse import urlparse

# 🔑 Fixed: Get secrets from environment variables
AWS_SECRET_KEY = os.getenv('AWS_SECRET_KEY')
if not AWS_SECRET_KEY:
    raise ValueError("AWS_SECRET_KEY environment variable not set")

# 🔐 Fixed: Get password from environment variable
PASSWORD = os.getenv('PASSWORD')
if not PASSWORD:
    raise ValueError("PASSWORD environment variable not set")

# 💡 Global variable (bad practice)
db_conn = None

def connect_db():
    global db_conn
    # ✅ Fixed: Use parameterized queries to prevent SQL injection
    user_input = input("Enter username: ")
    query = "SELECT * FROM users WHERE username = ?"
    db_conn = sqlite3.connect("users.db")
    cursor = db_conn.cursor()
    cursor.execute(query, (user_input,))
    print(cursor.fetchall())

def safe_eval():
    # ✅ Fixed: Use ast.literal_eval for safe evaluation
    expr = input("Enter math expression: ")
    try:
        result = ast.literal_eval(expr)
        print(result)
    except (ValueError, SyntaxError) as e:
        print(f"Invalid expression: {e}")

def safe_command_execution():
    # ✅ Fixed: Use subprocess with proper argument handling
    filename = input("Enter filename to list: ")
    try:
        # Validate filename to prevent path traversal
        if '..' in filename or filename.startswith('/'):
            print("Invalid filename")
            return
        subprocess.run(["ls", "-l", filename], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e}")

def send_data():
    data = {
        "secret": AWS_SECRET_KEY
    }
    # ✅ Fixed: Use HTTPS instead of HTTP
    try:
        requests.post("https://example.com/submit", data=data, timeout=30)
    except requests.RequestException as e:
        print(f"Request failed: {e}")

def download_url():
    # ✅ Fixed: Validate URL to prevent SSRF
    url = input("Enter URL to fetch: ")
    try:
        parsed = urlparse(url)
        # Only allow HTTPS and specific domains
        if parsed.scheme != 'https' or not parsed.netloc.endswith('.example.com'):
            print("Invalid URL: Only HTTPS URLs from example.com domain allowed")
            return
        r = requests.get(url, timeout=30)
        print(r.text)
    except requests.RequestException as e:
        print(f"Request failed: {e}")

def secure_file_permission():
    # ✅ Fixed: Use secure file permissions
    with open("temp.txt", "w") as f:
        f.write("temporary")
    os.chmod("temp.txt", 0o644)  # Read/write for owner, read for group/others

def unused_function():
    # 💡 Dead code
    print("This function is never called")

# Entry point
if __name__ == "__main__":
    connect_db()
    safe_eval()
    safe_command_execution()
    send_data()
    download_url()
    secure_file_permission()
