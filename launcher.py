import os
import sys
import time
import subprocess

# Ссылка на твой чистый код чата на GitHub (замени на свою ссылку!)
GITHUB_RAW_CHAT_URL = "https://github.com/elernete10075/xrl/tree/main/chat.py"
CHAT_FILE = "chat.py"

def print_progress(stage_name, percent):
    """Рисует красивый лоадер в терминале"""
    os.system('clear' if os.name != 'nt' else 'cls')
    print("loading xrl-chat")
    print(f"    {stage_name} ...")
    
    bar_length = 20
    filled_length = int(bar_length * percent // 100)
    bar = '=' * filled_length + ' ' * (bar_length - filled_length)
    
    print(f"[{bar}] {percent}%")

def check_libs():
    """Тихая проверка и установка библиотек без мусора в консоли"""
    required_libs = ["firebase-admin", "cryptography", "requests"]
    
    for i, lib in enumerate(required_libs):
        percent = int(10 + (i / len(required_libs)) * 40)  # Стадии от 10% до 50%
        print_progress(f"checking {lib}", percent)
        time.sleep(0.3)
        
        # Запуск pip install в "тихом" режиме (stdout в никуда)
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", lib, "--quiet"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

def update_chat_code():
    """Скачивает последнюю версию чата с гитхаба"""
    print_progress("checking for updates", 70)
    time.sleep(0.5)
    
    try:
        import requests
        print_progress("downloading latest updates", 85)
        response = requests.get(GITHUB_RAW_CHAT_URL, timeout=10)
        if response.status_code == 200:
            with open(CHAT_FILE, "w", encoding="utf-8") as f:
                f.write(response.text)
            print_progress("done", 100)
            time.sleep(0.5)
        else:
            # Если гитхаб не ответил, но локальный файл есть — просто запускаем
            if not os.path.exists(CHAT_FILE):
                print("\n[Error] Не удалось скачать чат с GitHub!")
                sys.exit(1)
    except Exception:
        if not os.path.exists(CHAT_FILE):
            print("\n[Error] Нет подключения к сети для первой загрузки!")
            sys.exit(1)

if __name__ == "__main__":
    # 1. Устанавливаем зависимости (10% - 50%)
    check_libs()
    
    # 2. Обновляем/качаем сам чат (50% - 100%)
    update_chat_code()
    
    # 3. Запуск основного чата
    os.system(f"{sys.executable} {CHAT_FILE}")
