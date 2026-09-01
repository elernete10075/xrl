#!/bin/bash

clear

# Вывод логотипа ECHO
echo -e "\033[1;36m░▒▓████████▓▒░▒▓██████▓▒░░▒▓█▓▒░░▒▓█▓▒░░▒▓██████▓▒░  \033[0m"
echo -e "\033[1;36m░▒▓█▓▒░     ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ \033[0m"
echo -e "\033[1;35m░▒▓█▓▒░     ░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ \033[0m"
echo -e "\033[1;35m░▒▓██████▓▒░░▒▓█▓▒░      ░▒▓████████▓▒░▒▓█▓▒░░▒▓█▓▒░ \033[0m"
echo -e "\033[0;35m░▒▓█▓▒░     ░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ \033[0m"
echo -e "\033[0;35m░▒▓█▓▒░     ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ \033[0m"
echo -e "\033[0;35m░▒▓████████▓▒░▒▓██████▓▒░░▒▓█▓▒░░▒▓█▓▒░░▒▓██████▓▒░  \033[0m"
echo -e "\033[0;37m========================================================\033[0m"
echo -e "\033[1;33m             INSTALLING XRL-CHAT SYSTEM                \033[0m"
echo -e "\033[0;37m========================================================\033[0m\n"

TARGET_DIR="$HOME/xrl-chat"
LAUNCHER_NAME="launcher.py"
KEY_ENC_NAME="Server_1.enc"
KEY_OUT_NAME="Server_1.json"

mkdir -p "$TARGET_DIR"

echo -e "\033[1;36m[1/3] Downloading and decoding Firebase Key...\033[0m"
# Скачиваем Server_1.enc и сразу раскодируем через base64 -d
curl -sSL "https://raw.githubusercontent.com/elernete10075/xrl/main/$KEY_ENC_NAME" | base64 -d > "$TARGET_DIR/$KEY_OUT_NAME"

echo -e "\033[1;36m[2/3] Downloading Linux Launcher...\033[0m"
curl -sSL "https://raw.githubusercontent.com/elernete10075/xrl/refs/heads/main/$LAUNCHER_NAME" -o "$TARGET_DIR/$LAUNCHER_NAME"

echo -e "\033[1;36m[3/3] Creating global 'echochat' command...\033[0m"

BIN_DIR="$HOME/.local/bin"
mkdir -p "$BIN_DIR"
CMD_FILE="$BIN_DIR/echochat"

cat << 'EOF' > "$CMD_FILE"
#!/bin/bash
cd "$HOME/xrl-chat" && python3 "$HOME/xrl-chat/launcher.py" "$@"
EOF

chmod +x "$CMD_FILE"

if [ -w "/usr/local/bin" ]; then
    cp "$CMD_FILE" "/usr/local/bin/echochat" 2>/dev/null
    chmod +x "/usr/local/bin/echochat" 2>/dev/null
fi

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

stty sane 2>/dev/null

cd "$TARGET_DIR"
python3 "$LAUNCHER_NAME"
