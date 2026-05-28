import os
import sys
import time

def print_progress(stage_name, percent):
    os.system('clear' if os.name != 'nt' else 'cls')
    print("loading xrl-chat")
    print(f"    {stage_name} ...")
    
    bar_length = 20
    filled_length = int(bar_length * percent // 100)
    bar = '=' * filled_length + ' ' * (bar_length - filled_length)
    
    print(f"[{bar}] {percent}%")

def check_libs():
    required_libs = ["firebase-admin", "cryptography", "requests"]
    
    # Импортируем pip прямо внутри Python, чтобы не плодить дочерние процессы
    try:
        from pip._internal import main as pipmain
    except reimport_error:
        try:
            from pip import main as pipmain
        except Exception:
            # Если pip совсем заблокирован, откатываемся на консоль с флагом игнора
            import subprocess
            for i, lib in enumerate(required_libs):
                percent = int(10 + (i / len(required_libs)) * 40)
                print_progress(f"checking {lib}", percent)
                subprocess.run([sys.executable, "-m", "pip", "install", lib, "--quiet", "--break-system-packages"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return

    for i, lib in enumerate(required_libs):
        percent = int(10 + (i / len(required_libs)) * 40)
        print_progress(f"checking {lib}", percent)
        time.sleep(0.1)
        
        try:
            # Встроенный запуск установки с подавлением системных ограничений
            pipmain(['install', lib, '--quiet', '--break-system-packages'])
        except Exception:
            pass

def update_chat_code():
    GITHUB_RAW_CHAT_URL = "https://raw.githubusercontent.com/elernete10075/xrl/refs/heads/main/chat.py"
    CHAT_FILE = "chat.py"
    
    print_progress("checking for updates", 70)
    time.sleep(0.2)
    try:
        import requests
        print_progress("downloading latest updates", 85)
        response = requests.get(GITHUB_RAW_CHAT_URL, timeout=10)
        if response.status_code == 200:
            with open(CHAT_FILE, "w", encoding="utf-8") as f:
                f.write(response.text)
            print_progress("done", 100)
            time.sleep(0.3)
        else:
            if not os.path.exists(CHAT_FILE):
                print("\n[Error] Не удалось получить chat.py с GitHub!")
                sys.exit(1)
    except Exception:
        if not os.path.exists(CHAT_FILE):
            print("\n[Error] Нет подключения к сети!")
            sys.exit(1)

if __name__ == "__main__":
    check_libs()
    update_chat_code()
    
    # Запуск чата
    if os.path.exists("chat.py"):
        os.system(f"{sys.executable} chat.py")
    else:
        print("\n[Error] Файл chat.py не найден.")
