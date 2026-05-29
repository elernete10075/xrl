#!/bin/bash

wget https://raw.githubusercontent.com/elernete10075/xrl/main/serviceAccountKey.json -O serviceAccountKey.json


clear
echo "   Installing XRL-CHAT Bootstrapper   "
echo "______________________________________"
echo ""

# Создаем папку xrl-chat в домашней директории, если её нет
TARGET_DIR="$HOME/xrl-chat"
mkdir -p "$TARGET_DIR"

# Удаляем старый лаунчер из корня хома, если он там был
rm -f "$HOME/launcher.py"
rm -f "$TARGET_DIR/launcher.py"

echo "[1/3] Downloading launcher.py into ~/xrl-chat/..."
# Скачиваем лаунчер прямо в созданную папку
curl -sSL "https://raw.githubusercontent.com/elernete10075/xrl/refs/heads/main/launcher.py" -o "$TARGET_DIR/launcher.py"

echo "[2/3] Configuring short command 'start-xrl'..."
SHELL_RC="$HOME/.bashrc"
if [ -f "$HOME/.zshrc" ]; then
    SHELL_RC="$HOME/.zshrc"
fi

# Очищаем старый алиас, если он существовал, чтобы прописать новый правильный путь
sed -i '/alias start-xrl=/d' "$SHELL_RC"

# Прописываем новый алиас с переходом в нужную папку перед запуском
echo "alias start-xrl='cd \$HOME/xrl-chat && python3 \$HOME/xrl-chat/launcher.py'" >> "$SHELL_RC"

echo "[3/3] Installation completed successfully!"
echo "--------------------------------------"
echo "Now you can just type: start-xrl"
echo "--------------------------------------"
echo "Starting the chat for the first time..."
echo ""

# Переходим в папку и запускаем
cd "$TARGET_DIR"
python3 launcher.py
