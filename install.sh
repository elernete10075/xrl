#!/bin/bash

# Очистка экрана
clear

# Вывод логотипа ECHO с сохранением выравнивания (8 пробелов) и цветным градиентом
echo -e "\033[1;36m        ░▒▓████████▓▒░▒▓██████▓▒░░▒▓█▓▒░░▒▓█▓▒░░▒▓██████▓▒░  \033[0m"
echo -e "\033[1;36m        ░▒▓█▓▒░     ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ \033[0m"
echo -e "\033[1;35m        ░▒▓█▓▒░     ░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ \033[0m"
echo -e "\033[1;35m        ░▒▓██████▓▒░░▒▓█▓▒░      ░▒▓████████▓▒░▒▓█▓▒░░▒▓█▓▒░ \033[0m"
echo -e "\033[0;35m        ░▒▓█▓▒░     ░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ \033[0m"
echo -e "\033[0;35m        ░▒▓█▓▒░     ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ \033[0m"
echo -e "\033[0;35m        ░▒▓████████▓▒░▒▓██████▓▒░░▒▓█▓▒░░▒▓█▓▒░░▒▓██████▓▒░  \033[0m"
echo -e "\033[0;37m========================================================\033[0m"
echo -e "\033[1;33m             INSTALLING XRL-CHAT SYSTEM                \033[0m"
echo -e "\033[0;37m========================================================\033[0m\n"

# Настройки путей
TARGET_DIR="$HOME/xrl-chat"
LAUNCHER_NAME="launcher.py"
KEY_NAME="Server_1.json"

# Создаем папку xrl-chat
mkdir -p "$TARGET_DIR"

# Удаляем старые версии лаунчера, если они оставались
rm -f "$HOME/$LAUNCHER_NAME"
rm -f "$TARGET_DIR/$LAUNCHER_NAME"

# 1. Скачивание конфига Firebase (Server_1.json)
echo -e "\033[1;36m[1/3] Downloading Server_1.json configuration...\033[0m"
if curl -sSL "https://raw.githubusercontent.com/elernete10075/xrl/main/$KEY_NAME" -o "$TARGET_DIR/$KEY_NAME"; then
    echo -e "\033[0;37m     -> Server_1.json saved successfully.\033[0m"
else
    echo -e "\033[1;31m     [ERROR] Failed to download $KEY_NAME!\033[0m"
fi

# 2. Скачивание лаунчера
echo -e "\033[1;36m[2/3] Downloading Linux Launcher...\033[0m"
if curl -sSL "https://raw.githubusercontent.com/elernete10075/xrl/refs/heads/main/$LAUNCHER_NAME" -o "$TARGET_DIR/$LAUNCHER_NAME"; then
    echo -e "\033[0;37m     -> $LAUNCHER_NAME saved successfully.\033[0m"
else
    echo -e "\033[1;31m     [ERROR] Failed to download $LAUNCHER_NAME!\033[0m"
fi

# 3. Настройка алиаса start-xrl
echo -e "\033[1;36m[3/3] Configuring short command 'start-xrl'...\033[0m"
SHELL_RC="$HOME/.bashrc"
if [ -f "$HOME/.zshrc" ]; then
    SHELL_RC="$HOME/.zshrc"
fi

# Удаляем старый алиас и прописываем актуальный
sed -i '/alias start-xrl=/d' "$SHELL_RC"
echo "alias start-xrl='cd \$HOME/xrl-chat && python3 \$HOME/xrl-chat/$LAUNCHER_NAME'" >> "$SHELL_RC"
echo -e "\033[0;37m     -> Alias created in $SHELL_RC\033[0m"

echo -e "\n\033[0;37m--------------------------------------------------------\033[0m"
echo -e "\033[1;32m SUCCESS! Installation complete.\033[0m"
echo -e "\033[1;33m To start the application, type: start-xrl\033[0m"
echo -e "\033[0;37m--------------------------------------------------------\033[0m\n"

echo -e "\033[1;36mStarting the chat for the first time...\033[0m\n"

# Переходим в папку и запускаем
cd "$TARGET_DIR"
python3 "$LAUNCHER_NAME"
