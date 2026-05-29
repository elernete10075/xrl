import os
import sys
import subprocess
import time

def install_dependencies():
    """Установка всех необходимых библиотек для Windows."""
    libs = ["firebase-admin", "cryptography", "requests", "windows-curses"]
    print("--- Настройка окружения Windows ---")
    for lib in libs:
        print(f"Проверка/Установка: {lib}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", lib, "--quiet"])
        except subprocess.CalledProcessError:
            print(f"[!] Не удалось установить {lib}. Проверь интернет.")

def download_chat():
    """Скачивание актуальной версии chat.py."""
    url = "https://raw.githubusercontent.com/elernete10075/xrl/refs/heads/main/chat.py"
    filename = "chat.py"
    
    try:
        import requests
        print("Проверка обновлений...")
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(response.text)
            print("Файл chat.py обновлен.")
        else:
            print(f"[!] Ошибка скачивания: статус {response.status_code}")
    except Exception as e:
        print(f"[!] Ошибка подключения к серверу: {e}")

def run_chat():
    """Запуск чата."""
    if os.path.exists("chat.py"):
        print("Запуск XRL-CHAT...")
        # Запуск через subprocess для корректной работы с потоками ввода-вывода
        subprocess.run([sys.executable, "chat.py"])
    else:
        print("[!] Ошибка: файл chat.py не найден!")
        input("Нажми Enter, чтобы выйти...")

if __name__ == "__main__":
    # 1. Ставим библиотеки
    install_dependencies()
    # 2. Обновляем код
    download_chat()
    # 3. Запускаем
    run_chat()
