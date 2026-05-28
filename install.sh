#!/bin/bash

# Очищаем экран для красивого вывода
clear
echo "======================================"
echo "    Installing XRL-CHAT Bootstrapper  "
echo "======================================"
echo ""

# Скачиваем сам лаунчер в домашнюю директорию пользователя
echo "[1/3] Downloading launcher.py..."
curl -sSL "https://raw.githubusercontent.com/твой_ник/твой_репозиторий/main/launcher.py" -o "$HOME/launcher.py"

# Создаем сокращение (alias) для быстрого запуска из любой папки
echo "[2/3] Configuring short command 'start-xrl'..."

# Проверяем, какой конфигурационный файл использует терминал (обычно .bashrc или .zshrc)
SHELL_RC="$HOME/.bashrc"
if [ -f "$HOME/.zshrc" ]; then
    SHELL_RC="$HOME/.zshrc"
fi

# Проверяем, нет ли уже такого алиаса, чтобы не дублировать
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

# Запускаем лаунчер прямо сейчас
python3 "$HOME/launcher.py"
