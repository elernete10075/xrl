#!/bin/bash

clear

# Ультра-компактный логотип ECHO (ширина всего 24 символа - не съедет ни в каком терминале)
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

# Создаем папку bin в домашней директории
BIN_DIR="$HOME/.local/bin"
mkdir -p "$BIN_DIR"

# Создаем исполняемый файл echochat
CMD_FILE="$BIN_DIR/echochat"
echo "#!/bin/bash" > "$CMD_FILE"
echo "cd \"$TARGET_DIR\" && python3 \"$TARGET_DIR/$LAUNCHER_NAME\" \"\$@\"" >> "$CMD_FILE"
chmod +x "$CMD_FILE"

# Прописываем PATH в bashrc и zshrc чтобы команда подхватывалась сразу
for RC in "$HOME/.bashrc" "$HOME/.zshrc"; do
    if [ -f "$RC" ]; then
        sed -i '/alias echochat=/d' "$RC"
        sed -i '/alias start-xrl=/d' "$RC"
        if ! grep -q 'PATH.*\.local/bin' "$RC"; then
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$RC"
        fi
        echo "alias echochat='cd $TARGET_DIR && python3 $TARGET_DIR/$LAUNCHER_NAME'" >> "$RC"
    fi
done

# Экспортируем PATH для текущей сессии
export PATH="$HOME/.local/bin:$PATH"

echo -e "\n\033[1;32mSUCCESS! Installation complete.\033[0m"
echo -e "\033[1;33mTo launch anytime, type: echochat\033[0m\n"

# Переходим и запускаем
cd "$TARGET_DIR"
python3 "$LAUNCHER_NAME"
