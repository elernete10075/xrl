import os
import sys
import subprocess
import time

def install_deps():
    # Библиотеки, необходимые для Windows
    libs = ["firebase-admin", "cryptography", "requests", "windows-curses"]
    print("--- Installing/Updating dependencies for Windows ---")
    for lib in libs:
        print(f"Installing {lib}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", lib, "--quiet"])

def update_and_run():
    # Файл чата
    CHAT_FILE = "chat.py"
    URL = "https://raw.githubusercontent.com/elernete10075/xrl/refs/heads/main/chat.py"
    
    # Скачивание chat.py
    import requests
    print("Checking for updates...")
    resp = requests.get(URL, timeout=10)
    with open(CHAT_FILE, "w", encoding="utf-8") as f:
        f.write(resp.text)
    
    # Запуск чата
    print("Launching XRL-CHAT...")
    subprocess.run([sys.executable, CHAT_FILE])

if __name__ == "__main__":
    try:
        install_deps()
        update_and_run()
    except Exception as e:
        print(f"\n[Error] Something went wrong: {e}")
        input("Press Enter to close...")
