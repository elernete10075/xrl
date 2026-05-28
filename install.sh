#!/bin/bash

# Очищаем экран
clear
echo "    Installing XRL-CHAT Bootstrapper  "
echo "______________________________________"
echo ""

# Принудительно удаляем старый сломанный лаунчер, если он остался
rm -f "$HOME/launcher.py"

echo "[1/3] Downloading launcher.py..."
# Скачиваем по твоей точной ссылке
curl -sSL "https://raw.githubusercontent.com/elernete10075/xrl/refs/heads/main/launcher.py" -o "$HOME/launcher.py"

echo "[2/3] Configuring short command 'start-xrl'..."
SHELL_RC="$HOME/.bashrc"
if [ -f "$HOME/.zshrc" ]; then
    SHELL_RC="$HOME/.zshrc"
fi

if ! grep -q "alias start-xrl=" "$SHELL_RC"; then
    echo "" >> "$SHELL_RC"
    echo "# XRL-Chat Alias" >> "$SHELL_RC"
    echo "alias start-xrl='python3 \$HOME/launcher.py'" >> "$SHELL_RC"
fi

echo "[3/3] Installation completed successfully!"
echo "--------------------------------------"
echo "Now you can just type: start-xrl"
echo "--------------------------------------"
echo "Starting the chat for the first time..."
echo ""

# Запускаем свежескачанный лаунчер
python3 "$HOME/launcher.py"
