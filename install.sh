#!/bin/bash

clear

# Компактный логотип ECHO
echo -e "\033[1;36m██████  ██████ ██  ██  ██████ \033[0m"
echo -e "\033[1;36m██      ██     ██  ██  ██  ██ \033[0m"
echo -e "\033[1;35m██████  ██     ██████  ██  ██ \033[0m"
echo -e "\033[1;35m██      ██     ██  ██  ██  ██ \033[0m"
echo -e "\033[0;35m██████  ██████ ██  ██  ██████ \033[0m"
echo -e "\033[0;37m=========================================\033[0m"
echo -e "\033[1;33m         INSTALLING XRL-CHAT             \033[0m"
echo -e "\033[0;37m=========================================\033[0m\n"

TARGET_DIR="$HOME/xrl-chat"
LAUNCHER_NAME="launcher.py"
KEY_NAME="Server_1.json"

mkdir -p "$TARGET_DIR"

echo -e "\033[1;36m[1/3] Downloading Server_1.json...\033[0m"
curl -sSL "https://raw.githubusercontent.com/elernete10075/xrl/main/$KEY_NAME" -o "$TARGET_DIR/$KEY_NAME"

echo -e "\033[1;36m[2/3] Downloading Linux Launcher...\033[0m"
curl -sSL "https://raw.githubusercontent.com/elernete10075/xrl/refs/heads/main/$LAUNCHER_NAME" -o "$TARGET_DIR/$LAUNCHER_NAME"

echo -e "\033[1;36m[3/3] Creating global 'echochat' command...\033[0m"

# Создание бинарного файла команды в ~/.local/bin
BIN_DIR="$HOME/.local/bin"
mkdir -p "$BIN_DIR"
CMD_FILE="$BIN_DIR/echochat"

cat << 'EOF' > "$CMD_FILE"
#!/bin/bash
cd "$HOME/xrl-chat" && python3 "$HOME/xrl-chat/launcher.py" "$@"
EOF

chmod +x "$CMD_FILE"

# Попытка продублировать в системную папку /usr/local/bin (если есть sudo/права)
if [ -w "/usr/local/bin" ]; then
    cp "$CMD_FILE" "/usr/local/bin/echochat" 2>/dev/null
    chmod +x "/usr/local/bin/echochat" 2>/dev/null
fi

# Регистрация пути и алиасов в bashrc / zshrc
for RC in "$HOME/.bashrc" "$HOME/.zshrc"; do
    if [ -f "$RC" ]; then
        sed -i '/alias echochat=/d' "$RC"
        sed -i '/alias start-xrl=/d' "$RC"
        if ! grep -q 'PATH.*\.local/bin' "$RC"; then
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$RC"
        fi
        echo "alias echochat='cd $TARGET_DIR && python3 $TARGET_DIR/$LAUNCHER_NAME'" >> "$RC"
        echo "alias start-xrl='cd $TARGET_DIR && python3 $TARGET_DIR/$LAUNCHER_NAME'" >> "$RC"
    fi
done

echo -e "\n\033[1;32mSUCCESS! Installation complete.\033[0m"
echo -e "\033[1;33mTo start chat in a new terminal, type: echochat\033[0m\n"

# Сброс режимов ввода TTY терминала перед вызовом чата (чинит неработающие стрелки)
stty sane 2>/dev/null

# Запуск
cd "$TARGET_DIR"
python3 "$LAUNCHER_NAME"
