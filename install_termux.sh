#!/data/data/com.termux/files/usr/bin/bash

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
echo -e "\033[1;33m          INSTALLING XRL-CHAT FOR TERMUX              \033[0m"
echo -e "\033[0;37m========================================================\033[0m\n"

TARGET_DIR="$HOME/xrl-chat"
LAUNCHER_NAME="launcher.py"
KEY_ENC_NAME="Server_1.enc"
KEY_OUT_NAME="Server_1.json"

echo -e "\033[1;36m[1/4] Updating Termux packages...\033[0m"
pkg update -y && pkg upgrade -y

echo -e "\033[1;36m[2/4] Installing required Termux dependencies...\033[0m"
pkg install python curl git clang libffi openssl -y

mkdir -p "$TARGET_DIR"

echo -e "\033[1;36m[3/4] Downloading core files & decoding key...\033[0m"
curl -sSL "https://raw.githubusercontent.com/elernete10075/xrl/main/$KEY_ENC_NAME" | base64 -d > "$TARGET_DIR/$KEY_OUT_NAME"
curl -sSL "https://raw.githubusercontent.com/elernete10075/xrl/refs/heads/main/$LAUNCHER_NAME" -o "$TARGET_DIR/$LAUNCHER_NAME"

echo -e "\033[1;36m[4/4] Creating global 'echochat' command...\033[0m"
PREFIX_BIN="$PREFIX/bin/echochat"

cat << 'EOF' > "$PREFIX_BIN"
#!/data/data/com.termux/files/usr/bin/bash
cd "$HOME/xrl-chat" && python "$HOME/xrl-chat/launcher.py" "$@"
EOF

chmod +x "$PREFIX_BIN"

echo -e "\n\033[1;32mSUCCESS! Installation complete.\033[0m"
echo -e "\033[1;33mTo start chat in Termux, type: echochat\033[0m\n"

stty sane 2>/dev/null

cd "$TARGET_DIR"
python "$LAUNCHER_NAME"
