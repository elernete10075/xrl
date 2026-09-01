import os
import sys
import subprocess
import time

def enable_ansi_support():
    """Включение поддержки ANSI-цветов в консоли Windows."""
    if os.name == 'nt':
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)

# Цветовая палитра для Windows PowerShell / CMD
CYAN = "\033[1;36m"
MAGENTA = "\033[1;35m"
DARK_MAGENTA = "\033[0;35m"
YELLOW = "\033[1;33m"
GRAY = "\033[0;37m"
RED = "\033[1;31m"
RESET = "\033[0m"

LOGOTYPE = f"""
{CYAN}  ░▒▓████████▓▒░▒▓██████▓▒░░▒▓█▓▒░░▒▓█▓▒░░▒▓██████▓▒░  
        ░▒▓█▓▒░     ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ {MAGENTA}
        ░▒▓█▓▒░     ░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ 
        ░▒▓██████▓▒░░▒▓█▓▒░      ░▒▓████████▓▒░▒▓█▓▒░░▒▓█▓▒░ {DARK_MAGENTA}
        ░▒▓█▓▒░     ░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ 
        ░▒▓█▓▒░     ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ 
        ░▒▓████████▓▒░▒▓██████▓▒░░▒▓█▓▒░░▒▓█▓▒░░▒▓██████▓▒░  {RESET}
"""

def print_progress(stage_name, percent):
    os.system('cls' if os.name == 'nt' else 'clear')
    print(LOGOTYPE)
    print(f"{YELLOW}>>> Loading XRL-CHAT System (Windows)...{RESET}\n")
    print(f"    {stage_name} ...")
    
    bar_length = 25
    filled_length = int(bar_length * percent // 100)
    bar = '=' * filled_length + ' ' * (bar_length - filled_length)
    
    print(f"[{CYAN}{bar}{RESET}] {percent}%\n")

def create_start_menu_shortcut():
    """Создает ярлык в Меню 'Пуск' для работы через поиск Windows без засорения рабочего стола."""
    try:
        appdata_dir = os.environ.get("APPDATA", "")
        start_menu_dir = os.path.join(appdata_dir, r"Microsoft\Windows\Start Menu\Programs")
        
        shortcut_path = os.path.join(start_menu_dir, "ECHO Chat.lnk")
        script_path = os.path.abspath(__file__)
        app_dir = os.path.dirname(script_path)

        if not os.path.exists(shortcut_path):
            # Встроенная генерация .lnk через PowerShell VBS-скриптер
            ps_command = f"""
            $WScriptShell = New-Object -ComObject WScript.Shell
            $Shortcut = $WScriptShell.CreateShortcut('{shortcut_path}')
            $Shortcut.TargetPath = 'python.exe'
            $Shortcut.Arguments = '"{script_path}"'
            $Shortcut.WorkingDirectory = '{app_dir}'
            $Shortcut.Description = 'Launch ECHO Chat'
            $Shortcut.Save()
            """
            subprocess.run(["powershell", "-Command", ps_command], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

def install_dependencies():
    """Установка всех необходимых библиотек для Windows."""
    libs = ["firebase-admin", "cryptography", "requests", "windows-curses"]
    for i, lib in enumerate(libs):
        percent = int(10 + (i / len(libs)) * 40)
        print_progress(f"checking dependency {lib}", percent)
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", lib, "--quiet"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except Exception:
            pass

def update_core_files():
    """Скачивание актуальных версий chat.py и Server_1.json."""
    GITHUB_RAW_CHAT_URL = "https://raw.githubusercontent.com/elernete10075/xrl/refs/heads/main/chat.py"
    GITHUB_RAW_KEY_URL = "https://raw.githubusercontent.com/elernete10075/xrl/main/Server_1.json"
    
    CHAT_FILE = "chat.py"
    KEY_FILE = "Server_1.json"

    print_progress("checking core files", 60)
    time.sleep(0.2)

    try:
        import requests

        # Проверка и скачивание Server_1.json при отсутствии
        if not os.path.exists(KEY_FILE):
            print_progress(f"downloading {KEY_FILE}", 75)
            key_resp = requests.get(GITHUB_RAW_KEY_URL, timeout=10)
            if key_resp.status_code == 200:
                with open(KEY_FILE, "w", encoding="utf-8") as f:
                    f.write(key_resp.text)

        # Обновление основного файла chat.py
        print_progress("downloading latest updates", 90)
        response = requests.get(GITHUB_RAW_CHAT_URL, timeout=15)
        if response.status_code == 200:
            with open(CHAT_FILE, "w", encoding="utf-8") as f:
                f.write(response.text)
            print_progress("system ready", 100)
            time.sleep(0.3)
        else:
            if not os.path.exists(CHAT_FILE):
                print(f"\n{RED}[!] Ошибка скачивания chat.py: статус {response.status_code}{RESET}")
                input("Нажми Enter, чтобы выйти...")
                sys.exit(1)
    except Exception as e:
        if not os.path.exists(CHAT_FILE):
            print(f"\n{RED}[!] Ошибка подключения к серверу: {e}{RESET}")
            input("Нажми Enter, чтобы выйти...")
            sys.exit(1)

def run_chat():
    """Запуск чата."""
    if os.path.exists("chat.py"):
        os.system('cls')
        subprocess.run([sys.executable, "chat.py"])
    else:
        print(f"\n{RED}[!] Ошибка: файл chat.py не найден!{RESET}")
        input("Нажми Enter, чтобы выйти...")

if __name__ == "__main__":
    enable_ansi_support()
    create_start_menu_shortcut()
    install_dependencies()
    update_core_files()
    run_chat()
