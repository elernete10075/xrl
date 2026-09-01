import os
import sys
import time
import subprocess

# ANSI цвета
CYAN = "\033[1;36m"
MAGENTA = "\033[1;35m"
DARK_MAGENTA = "\033[0;35m"
YELLOW = "\033[1;33m"
GRAY = "\033[0;37m"
RESET = "\033[0m"

# Чистый логотип с ровным отступом в 8 пробелов
LOGO_LINES = [
    "        ░▒▓████████▓▒░▒▓██████▓▒░░▒▓█▓▒░░▒▓█▓▒░░▒▓██████▓▒░",
    "        ░▒▓█▓▒░     ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░",
    "        ░▒▓█▓▒░     ░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░",
    "        ░▒▓██████▓▒░░▒▓█▓▒░      ░▒▓████████▓▒░▒▓█▓▒░░▒▓█▓▒░",
    "        ░▒▓█▓▒░     ░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░",
    "        ░▒▓█▓▒░     ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░",
    "        ░▒▓████████▓▒░▒▓██████▓▒░░▒▓█▓▒░░▒▓█▓▒░░▒▓██████▓▒░"
]

# Цвета для каждой строки по порядку
LINE_COLORS = [
    CYAN,
    CYAN,
    MAGENTA,
    MAGENTA,
    DARK_MAGENTA,
    DARK_MAGENTA,
    DARK_MAGENTA
]

def render_logo():
    output = []
    for line, color in zip(LOGO_LINES, LINE_COLORS):
        output.append(f"{color}{line}{RESET}")
    return "\n".join(output)

def print_progress(stage_name, percent):
    os.system('clear' if os.name != 'nt' else 'cls')
    print(render_logo())
    print(f"\n{YELLOW}>>> Loading XRL-CHAT System...{RESET}\n")
    print(f"    {stage_name} ...")
    
    bar_length = 20
    filled_length = int(bar_length * percent // 100)
    bar = '=' * filled_length + ' ' * (bar_length - filled_length)
    
    print(f"[{CYAN}{bar}{RESET}] {percent}%\n")

def check_libs():
    required_libs = ["firebase-admin", "cryptography", "requests"]
    for i, lib in enumerate(required_libs):
        percent = int(10 + (i / len(required_libs)) * 30)
        print_progress(f"checking dependency {lib}", percent)
        subprocess.run(
            [sys.executable, "-m", "pip", "install", lib, "--quiet", "--break-system-packages"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

def update_chat_code():
    GITHUB_RAW_CHAT_URL = "https://raw.githubusercontent.com/elernete10075/xrl/refs/heads/main/chat.py"
    GITHUB_RAW_KEY_URL = "https://raw.githubusercontent.com/elernete10075/xrl/main/Server_1.json"
    
    CHAT_FILE = "chat.py"
    KEY_FILE = "Server_1.json"
    
    print_progress("checking core files", 50)
    time.sleep(0.1)
    
    try:
        import requests
        
        if not os.path.exists(KEY_FILE):
            print_progress(f"downloading {KEY_FILE}", 65)
            key_resp = requests.get(GITHUB_RAW_KEY_URL, timeout=10)
            if key_resp.status_code == 200:
                with open(KEY_FILE, "w", encoding="utf-8") as f:
                    f.write(key_resp.text)
        
        print_progress("downloading latest updates", 85)
        response = requests.get(GITHUB_RAW_CHAT_URL, timeout=10)
        if response.status_code == 200:
            with open(CHAT_FILE, "w", encoding="utf-8") as f:
                f.write(response.text)
            print_progress("system ready", 100)
            time.sleep(0.2)
        else:
            if not os.path.exists(CHAT_FILE):
                print(f"\n{GRAY}[Error] Не удалось получить chat.py с GitHub!{RESET}")
                sys.exit(1)
    except Exception:
        if not os.path.exists(CHAT_FILE):
            print(f"\n{GRAY}[Error] Нет подключения к сети!{RESET}")
            sys.exit(1)

def reset_tty():
    try:
        os.system('stty sane 2>/dev/null')
    except Exception:
        pass

if __name__ == "__main__":
    check_libs()
    update_chat_code()
    
    if os.path.exists("chat.py"):
        reset_tty()
        os.system('clear')
        try:
            with open('/dev/tty', 'r+') as tty:
                subprocess.run([sys.executable, "chat.py"], stdin=tty, stdout=tty, stderr=tty)
        except Exception:
            subprocess.run([sys.executable, "chat.py"])
    else:
        print(f"\n{GRAY}[Error] Файл chat.py не найден.{RESET}")
