import os
import sys
import time
import subprocess

# ANSI цвета для терминала
CYAN = "\033[1;36m"
MAGENTA = "\033[1;35m"
DARK_MAGENTA = "\033[0;35m"
YELLOW = "\033[1;33m"
GRAY = "\033[0;37m"
RESET = "\033[0m"

LOGOTYPE = f"""
{CYAN}        ░▒▓████████▓▒░▒▓██████▓▒░░▒▓█▓▒░░▒▓█▓▒░░▒▓██████▓▒░  
        ░▒▓█▓▒░     ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ {MAGENTA}
        ░▒▓█▓▒░     ░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ 
        ░▒▓██████▓▒░░▒▓█▓▒░      ░▒▓████████▓▒░▒▓█▓▒░░▒▓█▓▒░ {DARK_MAGENTA}
        ░▒▓█▓▒░     ░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ 
        ░▒▓█▓▒░     ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ 
        ░▒▓████████▓▒░▒▓██████▓▒░░▒▓█▓▒░░▒▓█▓▒░░▒▓██████▓▒░  {RESET}
"""

def print_progress(stage_name, percent):
    os.system('clear' if os.name != 'nt' else 'cls')
    print(LOGOTYPE)
    print(f"{YELLOW}>>> Loading XRL-CHAT System...{RESET}\n")
    print(f"    {stage_name} ...")
    
    bar_length = 25
    filled_length = int(bar_length * percent // 100)
    bar = '=' * filled_length + ' ' * (bar_length - filled_length)
    
    print(f"[{CYAN}{bar}{RESET}] {percent}%\n")

def check_alias():
    """Автоматическая настройка короткой команды echochat"""
    home = os.path.expanduser("~")
    script_path = os.path.abspath(__file__)
    app_dir = os.path.dirname(script_path)
    
    shell_rc = os.path.join(home, ".zshrc") if os.path.exists(os.path.join(home, ".zshrc")) else os.path.join(home, ".bashrc")
    
    alias_line = f"alias echochat='cd {app_dir} && {sys.executable} {script_path}'"
    
    if os.path.exists(shell_rc):
        try:
            with open(shell_rc, "r", encoding="utf-8") as f:
                content = f.read()
            if alias_line not in content:
                # Очищаем старые алиасы echochat если есть
                lines = [line for line in content.splitlines() if not line.startswith("alias echochat=")]
                lines.append(alias_line)
                with open(shell_rc, "w", encoding="utf-8") as f:
                    f.write("\n".join(lines) + "\n")
        except Exception:
            pass

def check_libs():
    required_libs = ["firebase-admin", "cryptography", "requests"]
    for i, lib in enumerate(required_libs):
        percent = int(10 + (i / len(required_libs)) * 30)
        print_progress(f"checking dependency {lib}", percent)
        subprocess.run(
            [sys.executable, "-m", "pip", "install", lib, "--quiet", "--break-system-packages"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

def update_chat_code():
    GITHUB_RAW_CHAT_URL = "https://raw.githubusercontent.com/elernete10075/xrl/refs/heads/main/chat.py"
    GITHUB_RAW_KEY_URL = "https://raw.githubusercontent.com/elernete10075/xrl/main/Server_1.json"
    
    CHAT_FILE = "chat.py"
    KEY_FILE = "Server_1.json"
    
    print_progress("checking core files", 50)
    time.sleep(0.2)
    
    try:
        import requests
        
        # Проверка и скачивание Server_1.json при отсутствии
        if not os.path.exists(KEY_FILE):
            print_progress(f"downloading {KEY_FILE}", 65)
            key_resp = requests.get(GITHUB_RAW_KEY_URL, timeout=10)
            if key_resp.status_code == 200:
                with open(KEY_FILE, "w", encoding="utf-8") as f:
                    f.write(key_resp.text)
        
        # Обновление основного кода chat.py
        print_progress("downloading latest updates", 85)
        response = requests.get(GITHUB_RAW_CHAT_URL, timeout=10)
        if response.status_code == 200:
            with open(CHAT_FILE, "w", encoding="utf-8") as f:
                f.write(response.text)
            print_progress("system ready", 100)
            time.sleep(0.3)
        else:
            if not os.path.exists(CHAT_FILE):
                print(f"\n{GRAY}[Error] Не удалось получить chat.py с GitHub!{RESET}")
                sys.exit(1)
    except Exception:
        if not os.path.exists(CHAT_FILE):
            print(f"\n{GRAY}[Error] Нет подключения к сети!{RESET}")
            sys.exit(1)

if __name__ == "__main__":
    check_alias()
    check_libs()
    update_chat_code()
    
    # Запуск чата из рабочей директории
    if os.path.exists("chat.py"):
        os.system(f"{sys.executable} chat.py")
    else:
        print(f"\n{GRAY}[Error] Файл chat.py не найден.{RESET}")
