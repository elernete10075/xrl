import curses
import os
import json
import time
import sys
import math
import random
import string
import threading
import queue
import base64
import firebase_admin
from firebase_admin import credentials, db

# ==========================================
# FIREBASE & ENCRYPTION ENGINE
# ==========================================
DB_URL = "https://xrl-chat-default-rtdb.europe-west1.firebasedatabase.app/"

global_chat_ref = None
groups_ref = None
users_ref = None
msg_queue = queue.Queue()

SECRET_KEY = "xrl_echo_secure_key_2026"

def xor_cipher(data: str, key: str = SECRET_KEY) -> str:
    if not data:
        return ""
    key_chars = [ord(c) for c in key]
    res = []
    for i, char in enumerate(data):
        res.append(chr(ord(char) ^ key_chars[i % len(key_chars)]))
    return "".join(res)

def encrypt_str(plain_text: str) -> str:
    if not plain_text:
        return ""
    cipher = xor_cipher(plain_text)
    return base64.b64encode(cipher.encode('utf-8')).decode('utf-8')

def decrypt_str(cipher_text: str) -> str:
    if not cipher_text:
        return ""
    try:
        decoded = base64.b64decode(cipher_text.encode('utf-8')).decode('utf-8')
        return xor_cipher(decoded)
    except Exception:
        return cipher_text

def init_firebase():
    global global_chat_ref, groups_ref, users_ref
    cred_file = "Server_1.json"
    if os.path.exists(cred_file):
        try:
            if not firebase_admin._apps:
                cred = credentials.Certificate(cred_file)
                firebase_admin.initialize_app(cred, {'databaseURL': DB_URL})
            global_chat_ref = db.reference("chat/global/messages")
            groups_ref = db.reference("groups")
            users_ref = db.reference("users")
        except Exception:
            pass

init_firebase()

def register_or_get_user(username):
    ID_FILE = "ac_id"
    user_id = ""
    if os.path.exists(ID_FILE):
        with open(ID_FILE, "r", encoding="utf-8") as f:
            user_id = f.read().strip()
    else:
        user_id = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
        with open(ID_FILE, "w", encoding="utf-8") as f:
            f.write(user_id)

    if users_ref:
        try:
            users_ref.child(user_id).set({
                "username": encrypt_str(username),
                "last_active": time.time()
            })
        except Exception:
            pass

    return user_id

def async_send_global_message(username, text):
    if not global_chat_ref:
        return
    try:
        global_chat_ref.push({
            'username': encrypt_str(username),
            'text': encrypt_str(text),
            'timestamp': time.time()
        })
    except Exception as e:
        msg_queue.put({"type": "error", "content": f"[System Error]: {e}"})

def async_send_group_message(username, text, group_name):
    if not groups_ref:
        return
    try:
        groups_ref.child(group_name).child("messages").push({
            'username': encrypt_str(username),
            'text': encrypt_str(text),
            'timestamp': time.time()
        })
    except Exception as e:
        msg_queue.put({"type": "error", "content": f"[System Error]: {e}"})

def background_fetch_loop(app_instance):
    last_global_keys = set()
    last_group_keys = set()
    last_group = None
    
    while True:
        try:
            if groups_ref:
                remote_groups_data = groups_ref.get()
                if remote_groups_data and isinstance(remote_groups_data, dict):
                    for g_name in remote_groups_data.keys():
                        if g_name not in app_instance.groups:
                            app_instance.groups.append(g_name)

            mode = app_instance.state
            if mode == "CHAT":
                if global_chat_ref:
                    data = global_chat_ref.order_by_key().limit_to_last(50).get()
                    if data and isinstance(data, dict):
                        for key, val in data.items():
                            if key not in last_global_keys:
                                last_global_keys.add(key)
                                if isinstance(val, dict) and 'text' in val:
                                    msg_queue.put({
                                        "type": "global_chat",
                                        "username": decrypt_str(val.get('username', '')),
                                        "text": decrypt_str(val.get('text', ''))
                                    })
            elif mode == "GROUP_CHAT":
                current_grp = app_instance.current_group
                if current_grp != last_group:
                    last_group_keys.clear()
                    last_group = current_grp

                if groups_ref and current_grp:
                    data = groups_ref.child(current_grp).child("messages").order_by_key().limit_to_last(50).get()
                    if data and isinstance(data, dict):
                        for key, val in data.items():
                            if key not in last_group_keys:
                                last_group_keys.add(key)
                                if isinstance(val, dict) and 'text' in val:
                                    msg_queue.put({
                                        "type": "group_chat",
                                        "group": current_grp,
                                        "username": decrypt_str(val.get('username', '')),
                                        "text": decrypt_str(val.get('text', ''))
                                    })
        except Exception:
            pass
        time.sleep(0.3)

def start_firebase_stream(app_instance):
    threading.Thread(target=background_fetch_loop, args=(app_instance,), daemon=True).start()


# ==========================================
# STREAM ANIMATION CONTROLLER
# ==========================================
class MessageStreamer:
    """Управляет посимвольной анимацией появления новых сообщений"""
    def __init__(self):
        self.target_text = ""
        self.current_text = ""
        self.char_index = 0
        self.last_tick = time.time()
        self.speed = 0.015

    def start_stream(self, full_text):
        self.target_text = full_text
        self.current_text = ""
        self.char_index = 0
        self.last_tick = time.time()

    def update(self):
        if self.char_index < len(self.target_text):
            now = time.time()
            if now - self.last_tick >= self.speed:
                step = random.randint(1, 2)
                self.char_index = min(len(self.target_text), self.char_index + step)
                self.current_text = self.target_text[:self.char_index]
                self.last_tick = now
                return True
        return False

    def is_animating(self):
        return self.char_index < len(self.target_text)


# ==========================================
# CONFIG & THEMES MANAGEMENT
# ==========================================
LOGO = [
    "        ░▒▓████████▓▒░▒▓██████▓▒░░▒▓█▓▒░░▒▓█▓▒░░▒▓██████▓▒░  ",
    "        ░▒▓█▓▒░     ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ ",
    "        ░▒▓█▓▒░     ░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ ",
    "        ░▒▓██████▓▒░░▒▓█▓▒░      ░▒▓████████▓▒░▒▓█▓▒░░▒▓█▓▒░ ",
    "        ░▒▓█▓▒░     ░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ ",
    "        ░▒▓█▓▒░     ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ ",
    "        ░▒▓████████▓▒░▒▓██████▓▒░░▒▓█▓▒░░▒▓█▓▒░░▒▓██████▓▒░  "
]

THEMES_DIR = "themes"
FRIENDS_DIR = "friends_chats"
CONFIG_FILE = "config.json"

DEFAULT_THEME_DATA = {
    "default": {"primary": 6, "secondary": 5, "text": 7, "gradient": [6, 5, 4]},
    "Dracula": {"primary": 5, "secondary": 1, "text": 7, "gradient": [5, 1, 5, 1]},
    "Cyberpunk": {"primary": 6, "secondary": 5, "text": 7, "gradient": [6, 5, 4]},
    "Matrix": {"primary": 2, "secondary": 0, "text": 2, "gradient": [2, 2]}
}


class EchoApp:
    def __init__(self):
        self.username = "User"
        self.load_config_username()
        self.user_id = register_or_get_user(self.username)
        
        self.current_group = ""
        self.current_theme_name = "default"
        self.active_theme = DEFAULT_THEME_DATA["default"]
        
        self.global_messages = []
        self.group_messages = {}
        
        self.groups = []
        self.group_passwords = {}
        self.friends = []
        self.active_friend = None
        self.dm_messages = {}

        self.menu_items = ["Chat", "Groups", "Friends", "Profile", "Themes", "Credits", "Exit"]
        self.selected_menu = 0
        self.selected_group_idx = 0
        self.selected_friend_idx = 0
        
        self.theme_items = []
        self.selected_theme_page = 0
        self.selected_theme_idx = 0
        
        self.palette_page = 0
        
        self.new_theme_name = ""
        self.new_theme_primary = 6
        self.new_theme_secondary = 5
        self.new_theme_text = 7
        self.new_theme_gradient = []
        self.create_theme_step = 0

        self.input_buffer = ""
        self.temp_group_name = ""
        self.temp_group_pass = ""
        self.target_group_join = ""
        self.scroll_offset = 0
        
        self.state = "MENU"

        self.ensure_dirs()
        self.init_default_themes_files()
        self.load_config()
        self.load_themes()

    def ensure_dirs(self):
        if not os.path.exists(THEMES_DIR):
            os.makedirs(THEMES_DIR)
        if not os.path.exists(FRIENDS_DIR):
            os.makedirs(FRIENDS_DIR)

    def init_default_themes_files(self):
        for name, data in DEFAULT_THEME_DATA.items():
            filepath = os.path.join(THEMES_DIR, f"{name}.json")
            if not os.path.exists(filepath):
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)

    def load_config_username(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    self.username = cfg.get("username", "User")
            except Exception:
                pass

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    self.username = cfg.get("username", self.username)
                    self.current_theme_name = cfg.get("theme", self.current_theme_name)
                    self.groups = cfg.get("groups", [])
                    enc_passwords = cfg.get("group_passwords_enc", {})
                    self.group_passwords = {k: decrypt_str(v) for k, v in enc_passwords.items()}
                    self.friends = cfg.get("friends", self.friends)
            except Exception:
                pass

    def save_config(self):
        enc_passwords = {k: encrypt_str(v) for k, v in self.group_passwords.items()}
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "username": self.username,
                "theme": self.current_theme_name,
                "groups": self.groups,
                "group_passwords_enc": enc_passwords,
                "friends": self.friends
            }, f, ensure_ascii=False, indent=4)
        register_or_get_user(self.username)

    def load_dm(self, friend_id):
        filepath = os.path.join(FRIENDS_DIR, f"{friend_id}.json")
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    encrypted_data = json.load(f)
                    self.dm_messages[friend_id] = [decrypt_str(msg) for msg in encrypted_data]
            except Exception:
                self.dm_messages[friend_id] = []
        else:
            self.dm_messages[friend_id] = []

    def save_dm(self, friend_id):
        filepath = os.path.join(FRIENDS_DIR, f"{friend_id}.json")
        encrypted_data = [encrypt_str(msg) for msg in self.dm_messages.get(friend_id, [])]
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(encrypted_data, f, ensure_ascii=False, indent=4)

    def load_themes(self):
        files = []
        if os.path.exists(THEMES_DIR):
            for file in sorted(os.listdir(THEMES_DIR)):
                if file.endswith(".json"):
                    files.append(file[:-5])

        if not files:
            files = ["default"]

        self.theme_items = ["[ COLOR PALETTE ]", "[ CREATE THEME ]"] + files

        filepath = os.path.join(THEMES_DIR, f"{self.current_theme_name}.json")
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    self.active_theme = json.load(f)
            except Exception:
                self.active_theme = DEFAULT_THEME_DATA["default"]
        else:
            self.active_theme = DEFAULT_THEME_DATA["default"]

    def init_colors(self):
        if curses.has_colors():
            curses.start_color()
            curses.use_default_colors()
            
            p = self.active_theme.get("primary", 6)
            s = self.active_theme.get("secondary", 5)
            t = self.active_theme.get("text", 7)
            
            curses.init_pair(1, p, -1)
            curses.init_pair(2, s, -1)
            curses.init_pair(3, t, -1)
            curses.init_pair(4, curses.COLOR_BLACK, p)
            
            grad = self.active_theme.get("gradient", [p, s])
            for idx, color_code in enumerate(grad):
                curses.init_pair(10 + idx, color_code, -1)

            max_colors = min(curses.COLORS, 256)
            for c in range(max_colors):
                try:
                    curses.init_pair(20 + c, curses.COLOR_BLACK, c)
                except Exception:
                    pass

    def transition_animation(self):
        """Плавная волновая анимация перевода страниц сверху вниз (Top-to-Bottom Wave)"""
        try:
            height, width = self.stdscr.getmaxyx()
            fill_char = "░"
            for y in range(height):
                try:
                    self.stdscr.addstr(y, 0, fill_char * (width - 1), curses.color_pair(2))
                    self.stdscr.refresh()
                    time.sleep(0.005)
                except curses.error:
                    pass
            time.sleep(0.02)
        except Exception:
            pass

    def change_state(self, new_state, curs_state=0):
        self.transition_animation()
        self.state = new_state
        curses.curs_set(curs_state)

    def draw_logo(self, stdscr):
        grad = self.active_theme.get("gradient", [self.active_theme.get("primary", 6)])
        grad_len = len(grad)

        for idx, line in enumerate(LOGO):
            color_pair = curses.color_pair(10 + (idx % grad_len)) | curses.A_BOLD if curses.has_colors() else curses.A_BOLD
            try:
                stdscr.addstr(idx + 1, 0, line, color_pair)
            except curses.error:
                pass

    def run(self, stdscr):
        self.stdscr = stdscr
        curses.curs_set(0)
        self.stdscr.nodelay(True)
        self.init_colors()

        start_firebase_stream(self)

        while True:
            while not msg_queue.empty():
                item = msg_queue.get()
                if item.get("type") == "global_chat":
                    formatted = f"{item['username']}: {item['text']}"
                    streamer = MessageStreamer()
                    streamer.start_stream(formatted)
                    self.global_messages.append(streamer)
                elif item.get("type") == "group_chat":
                    grp = item['group']
                    if grp not in self.group_messages:
                        self.group_messages[grp] = []
                    formatted = f"{item['username']}: {item['text']}"
                    streamer = MessageStreamer()
                    streamer.start_stream(formatted)
                    self.group_messages[grp].append(streamer)

            for s in self.global_messages:
                s.update()
            for grp_msgs in self.group_messages.values():
                for s in grp_msgs:
                    s.update()

            self.draw()
            if not self.handle_input():
                break
            time.sleep(0.015)

    def draw(self):
        self.stdscr.erase()
        height, width = self.stdscr.getmaxyx()

        if self.state == "MENU":
            self.draw_menu(height, width)
        elif self.state == "CHAT":
            self.draw_global_chat(height, width)
        elif self.state == "GROUP_CHAT":
            self.draw_group_chat(height, width)
        elif self.state == "GROUPS":
            self.draw_groups(height, width)
        elif self.state in ("CREATE_GROUP_NAME", "CREATE_GROUP_PASS"):
            self.draw_create_group(height, width)
        elif self.state == "ENTER_GROUP_PASS":
            self.draw_enter_group_pass(height, width)
        elif self.state == "FRIENDS":
            self.draw_friends_menu(height, width)
        elif self.state == "ADD_FRIEND":
            self.draw_add_friend(height, width)
        elif self.state == "DM_CHAT":
            self.draw_dm_chat(height, width)
        elif self.state == "PROFILE":
            self.draw_profile(height, width)
        elif self.state == "THEMES":
            self.draw_themes(height, width)
        elif self.state == "CREATE_THEME_WIZARD":
            self.draw_create_theme_wizard(height, width)
        elif self.state == "PALETTE":
            self.draw_palette(height, width)
        elif self.state == "CREDITS":
            self.draw_credits(height, width)

        self.stdscr.refresh()

    def draw_menu(self, height, width):
        self.draw_logo(self.stdscr)
        start_y = len(LOGO) + 2

        try:
            self.stdscr.addstr(start_y, 0, f"=== ECHO CHAT MAIN MENU | ID: {self.user_id} ===", curses.color_pair(1) | curses.A_BOLD)
        except curses.error:
            pass

        for idx, item in enumerate(self.menu_items):
            y = start_y + 2 + idx
            if idx == self.selected_menu:
                attr = curses.color_pair(4) | curses.A_BOLD
                prefix = " > "
            else:
                attr = curses.color_pair(3)
                prefix = "   "
            try:
                self.stdscr.addstr(y, 0, f"{prefix}{item}", attr)
            except curses.error:
                pass

    def draw_global_chat(self, height, width):
        self.draw_logo(self.stdscr)
        logo_offset = len(LOGO) + 1
        
        header = f"=== GLOBAL PUBLIC CHAT | User: {self.username} ==="
        try:
            self.stdscr.addstr(logo_offset, 0, header[:width-1], curses.color_pair(1) | curses.A_BOLD)
            self.stdscr.addstr(logo_offset + 1, 0, "-" * (width-1), curses.color_pair(2))
        except curses.error:
            pass

        chat_start_y = logo_offset + 2
        chat_height = height - chat_start_y - 2
        if chat_height > 0:
            visible = self.global_messages[-(chat_height + self.scroll_offset): len(self.global_messages) - self.scroll_offset if self.scroll_offset > 0 else None]
            for idx, streamer in enumerate(visible[:chat_height]):
                msg_text = streamer.current_text
                if streamer.is_animating():
                    msg_text += "▌"
                try:
                    self.stdscr.addstr(chat_start_y + idx, 0, msg_text[:width-1], curses.color_pair(3))
                except curses.error:
                    pass

        try:
            self.stdscr.addstr(height - 2, 0, "-" * (width-1), curses.color_pair(2))
            prompt = f"[Global] > {self.input_buffer}"
            self.stdscr.addstr(height - 1, 0, prompt[:width-1], curses.color_pair(1))
        except curses.error:
            pass

    def draw_group_chat(self, height, width):
        self.draw_logo(self.stdscr)
        logo_offset = len(LOGO) + 1
        
        header = f"=== GROUP ROOM: {self.current_group} | User: {self.username} ==="
        try:
            self.stdscr.addstr(logo_offset, 0, header[:width-1], curses.color_pair(1) | curses.A_BOLD)
            self.stdscr.addstr(logo_offset + 1, 0, "-" * (width-1), curses.color_pair(2))
        except curses.error:
            pass

        chat_start_y = logo_offset + 2
        chat_height = height - chat_start_y - 2
        msgs = self.group_messages.get(self.current_group, [])
        if chat_height > 0:
            visible = msgs[-(chat_height + self.scroll_offset): len(msgs) - self.scroll_offset if self.scroll_offset > 0 else None]
            for idx, streamer in enumerate(visible[:chat_height]):
                msg_text = streamer.current_text
                if streamer.is_animating():
                    msg_text += "▌"
                try:
                    self.stdscr.addstr(chat_start_y + idx, 0, msg_text[:width-1], curses.color_pair(3))
                except curses.error:
                    pass

        try:
            self.stdscr.addstr(height - 2, 0, "-" * (width-1), curses.color_pair(2))
            prompt = f"[{self.current_group}] > {self.input_buffer}"
            self.stdscr.addstr(height - 1, 0, prompt[:width-1], curses.color_pair(1))
        except curses.error:
            pass

    def draw_groups(self, height, width):
        self.draw_logo(self.stdscr)
        start_y = len(LOGO) + 2
        try:
            self.stdscr.addstr(start_y, 0, "=== GROUPS & ROOMS ===", curses.color_pair(1) | curses.A_BOLD)
        except curses.error:
            pass

        items = ["[ + CREATE NEW GROUP ]"] + self.groups
        for idx, grp in enumerate(items):
            y = start_y + 2 + idx
            is_locked = ""
            if grp != "[ + CREATE NEW GROUP ]" and self.group_passwords.get(grp):
                is_locked = " [LOCKED]"
                
            if idx == self.selected_group_idx:
                attr = curses.color_pair(4) | curses.A_BOLD
                prefix = " > "
            else:
                attr = curses.color_pair(3)
                prefix = "   "
            try:
                self.stdscr.addstr(y, 0, f"{prefix}{grp}{is_locked}", attr)
            except curses.error:
                pass

    def draw_create_group(self, height, width):
        self.draw_logo(self.stdscr)
        start_y = len(LOGO) + 2
        try:
            self.stdscr.addstr(start_y, 0, "=== CREATE NEW GROUP ===", curses.color_pair(1) | curses.A_BOLD)
            if self.state == "CREATE_GROUP_NAME":
                self.stdscr.addstr(start_y + 2, 0, f"Enter Group Name: {self.input_buffer}", curses.color_pair(3))
                self.stdscr.addstr(start_y + 4, 0, "[Enter] Next  |  [Esc] Cancel", curses.color_pair(2))
            elif self.state == "CREATE_GROUP_PASS":
                self.stdscr.addstr(start_y + 2, 0, f"Group: {self.temp_group_name}", curses.color_pair(3))
                self.stdscr.addstr(start_y + 3, 0, f"Set Password (leave empty for public): {self.input_buffer}", curses.color_pair(1) | curses.A_BOLD)
                self.stdscr.addstr(start_y + 5, 0, "[Enter] Save Group  |  [Esc] Cancel", curses.color_pair(2))
        except curses.error:
            pass

    def draw_enter_group_pass(self, height, width):
        self.draw_logo(self.stdscr)
        start_y = len(LOGO) + 2
        try:
            self.stdscr.addstr(start_y, 0, f"=== ENTER PASSWORD FOR '{self.target_group_join}' ===", curses.color_pair(1) | curses.A_BOLD)
            self.stdscr.addstr(start_y + 2, 0, f"Password: {self.input_buffer}", curses.color_pair(3))
            self.stdscr.addstr(start_y + 4, 0, "[Enter] Join  |  [Esc] Cancel", curses.color_pair(2))
        except curses.error:
            pass

    def draw_friends_menu(self, height, width):
        self.draw_logo(self.stdscr)
        start_y = len(LOGO) + 2
        try:
            self.stdscr.addstr(start_y, 0, f"=== FRIENDS | YOUR ID: {self.user_id} ===", curses.color_pair(1) | curses.A_BOLD)
        except curses.error:
            pass

        items = ["[ + ADD FRIEND BY ID ]"] + self.friends
        for idx, item in enumerate(items):
            y = start_y + 2 + idx
            if idx == self.selected_friend_idx:
                attr = curses.color_pair(4) | curses.A_BOLD
                prefix = " > "
            else:
                attr = curses.color_pair(3)
                prefix = "   "
            try:
                self.stdscr.addstr(y, 0, f"{prefix}{item}", attr)
            except curses.error:
                pass

    def draw_add_friend(self, height, width):
        self.draw_logo(self.stdscr)
        start_y = len(LOGO) + 2
        try:
            self.stdscr.addstr(start_y, 0, "=== ADD FRIEND ===", curses.color_pair(1) | curses.A_BOLD)
            self.stdscr.addstr(start_y + 2, 0, f"Enter Friend ID: {self.input_buffer}", curses.color_pair(3))
            self.stdscr.addstr(start_y + 4, 0, "[Enter] Add  |  [Esc] Cancel", curses.color_pair(2))
        except curses.error:
            pass

    def draw_dm_chat(self, height, width):
        self.draw_logo(self.stdscr)
        logo_offset = len(LOGO) + 1
        
        header = f"=== Friend ID: {self.active_friend} | Encrypted DM ==="
        try:
            self.stdscr.addstr(logo_offset, 0, header[:width-1], curses.color_pair(1) | curses.A_BOLD)
            self.stdscr.addstr(logo_offset + 1, 0, "-" * (width-1), curses.color_pair(2))
        except curses.error:
            pass

        chat_start_y = logo_offset + 2
        chat_height = height - chat_start_y - 2
        msgs = self.dm_messages.get(self.active_friend, [])
        if chat_height > 0:
            visible = msgs[-(chat_height + self.scroll_offset): len(msgs) - self.scroll_offset if self.scroll_offset > 0 else None]
            for idx, msg in enumerate(visible[:chat_height]):
                try:
                    self.stdscr.addstr(chat_start_y + idx, 0, msg[:width-1], curses.color_pair(3))
                except curses.error:
                    pass

        try:
            self.stdscr.addstr(height - 2, 0, "-" * (width-1), curses.color_pair(2))
            prompt = f"DM -> {self.active_friend} > {self.input_buffer}"
            self.stdscr.addstr(height - 1, 0, prompt[:width-1], curses.color_pair(1))
        except curses.error:
            pass

    def draw_profile(self, height, width):
        self.draw_logo(self.stdscr)
        start_y = len(LOGO) + 2
        try:
            self.stdscr.addstr(start_y, 0, "=== PROFILE SETTINGS ===", curses.color_pair(1) | curses.A_BOLD)
            self.stdscr.addstr(start_y + 2, 0, f"Your Unique ID: {self.user_id}", curses.color_pair(2))
            self.stdscr.addstr(start_y + 3, 0, f"Current Username: {self.username}", curses.color_pair(3))
            self.stdscr.addstr(start_y + 5, 0, f"New Username: {self.input_buffer}", curses.color_pair(1) | curses.A_BOLD)
            self.stdscr.addstr(start_y + 7, 0, "[Enter] Save  |  [Esc] Cancel", curses.color_pair(2))
        except curses.error:
            pass

    def draw_themes(self, height, width):
        self.draw_logo(self.stdscr)
        start_y = len(LOGO) + 2
        
        per_page = 7
        total_pages = math.ceil(len(self.theme_items) / per_page) or 1
        start_idx = self.selected_theme_page * per_page
        end_idx = start_idx + per_page
        page_themes = self.theme_items[start_idx:end_idx]

        try:
            self.stdscr.addstr(start_y, 0, f"=== THEMES (Page {self.selected_theme_page + 1}/{total_pages}) ===", curses.color_pair(1) | curses.A_BOLD)
            self.stdscr.addstr(start_y + 1, 0, "[Left/Right] Switch Page  |  [Enter] Select", curses.color_pair(2))
        except curses.error:
            pass

        for idx, th_name in enumerate(page_themes):
            y = start_y + 3 + idx
            global_idx = start_idx + idx
            if global_idx == self.selected_theme_idx:
                attr = curses.color_pair(4) | curses.A_BOLD
                prefix = " > "
            else:
                attr = curses.color_pair(3)
                prefix = "   "
            try:
                self.stdscr.addstr(y, 0, f"{prefix}{th_name}", attr)
            except curses.error:
                pass

    def draw_create_theme_wizard(self, height, width):
        self.draw_logo(self.stdscr)
        start_y = len(LOGO) + 2
        try:
            self.stdscr.addstr(start_y, 0, "=== CREATE CUSTOM THEME ===", curses.color_pair(1) | curses.A_BOLD)
            if self.create_theme_step == 0:
                self.stdscr.addstr(start_y + 2, 0, f"Theme File Name: {self.input_buffer}", curses.color_pair(3))
                self.stdscr.addstr(start_y + 4, 0, "[Enter] Next  |  [Esc] Cancel", curses.color_pair(2))
            elif self.create_theme_step == 1:
                self.stdscr.addstr(start_y + 2, 0, f"Primary Color ID (0-255): {self.input_buffer}", curses.color_pair(3))
            elif self.create_theme_step == 2:
                self.stdscr.addstr(start_y + 2, 0, f"Secondary Color ID (0-255): {self.input_buffer}", curses.color_pair(3))
            elif self.create_theme_step == 3:
                self.stdscr.addstr(start_y + 2, 0, f"Text Color ID (0-255): {self.input_buffer}", curses.color_pair(3))
            elif self.create_theme_step == 4:
                self.stdscr.addstr(start_y + 2, 0, f"Gradient Color IDs (space-separated): {self.input_buffer}", curses.color_pair(3))
                self.stdscr.addstr(start_y + 4, 0, "[Enter] Finish & Save Theme", curses.color_pair(2))
        except curses.error:
            pass

    def draw_palette(self, height, width):
        self.draw_logo(self.stdscr)
        start_y = len(LOGO) + 2
        
        total_colors = min(curses.COLORS, 256)
        per_page = 48
        total_pages = math.ceil(total_colors / per_page) or 1
        
        start_c = self.palette_page * per_page
        end_c = min(start_c + per_page, total_colors)

        try:
            self.stdscr.addstr(start_y, 0, f"=== 256 COLOR PALETTE (Page {self.palette_page + 1}/{total_pages}) ===", curses.color_pair(1) | curses.A_BOLD)
            self.stdscr.addstr(start_y + 1, 0, "[Left/Right] Page  |  [Esc] Back", curses.color_pair(2))

            for idx, c in enumerate(range(start_c, end_c)):
                col = idx // 16
                row = idx % 16
                
                x_pos = col * 25
                y_pos = start_y + 3 + row
                
                sample = "  "
                attr = curses.color_pair(20 + c)
                self.stdscr.addstr(y_pos, x_pos, f"{c:3d}:", curses.color_pair(3))
                self.stdscr.addstr(y_pos, x_pos + 5, "[", curses.color_pair(3))
                self.stdscr.addstr(y_pos, x_pos + 6, sample, attr)
                self.stdscr.addstr(y_pos, x_pos + 8, "]", curses.color_pair(3))
        except curses.error:
            pass

    def draw_credits(self, height, width):
        self.draw_logo(self.stdscr)
        start_y = len(LOGO) + 2
        try:
            self.stdscr.addstr(start_y, 0, "=== CREDITS ===", curses.color_pair(1) | curses.A_BOLD)
            self.stdscr.addstr(start_y + 2, 4, "echo chat by", curses.color_pair(3))
            self.stdscr.addstr(start_y + 3, 4, "gemini ai", curses.color_pair(1) | curses.A_BOLD)
            self.stdscr.addstr(start_y + 4, 4, "xrl-dev", curses.color_pair(2) | curses.A_BOLD)
            
            self.stdscr.addstr(start_y + 6, 4, "version 2.0.5", curses.color_pair(3))
            self.stdscr.addstr(start_y + 8, 0, "[Esc] Back to Menu", curses.color_pair(2))
        except curses.error:
            pass

    def handle_input(self):
        try:
            key = self.stdscr.getch()
        except Exception:
            key = -1

        if key == -1:
            return True

        if key == 27:  # ESC
            if self.state in ("CHAT", "GROUP_CHAT", "GROUPS", "FRIENDS", "PROFILE", "THEMES", "CREDITS"):
                self.change_state("MENU", 0)
            elif self.state in ("PALETTE", "CREATE_THEME_WIZARD"):
                self.change_state("THEMES", 0)
            elif self.state in ("CREATE_GROUP_NAME", "CREATE_GROUP_PASS", "ENTER_GROUP_PASS"):
                self.input_buffer = ""
                self.change_state("GROUPS", 0)
            elif self.state == "ADD_FRIEND":
                self.input_buffer = ""
                self.change_state("FRIENDS", 0)
            elif self.state == "DM_CHAT":
                self.change_state("FRIENDS", 0)
            return True

        if self.state == "MENU":
            if key in (curses.KEY_UP, ord('k')):
                self.selected_menu = (self.selected_menu - 1) % len(self.menu_items)
            elif key in (curses.KEY_DOWN, ord('j')):
                self.selected_menu = (self.selected_menu + 1) % len(self.menu_items)
            elif key in (10, 13):
                choice = self.menu_items[self.selected_menu]
                if choice == "Chat":
                    self.change_state("CHAT", 1)
                elif choice == "Groups":
                    self.selected_group_idx = 0
                    self.change_state("GROUPS", 0)
                elif choice == "Friends":
                    self.selected_friend_idx = 0
                    self.change_state("FRIENDS", 0)
                elif choice == "Profile":
                    self.change_state("PROFILE", 1)
                elif choice == "Themes":
                    self.change_state("THEMES", 0)
                elif choice == "Credits":
                    self.change_state("CREDITS", 0)
                elif choice == "Exit":
                    return False

        elif self.state == "GROUPS":
            items = ["[ + CREATE NEW GROUP ]"] + self.groups
            if key in (curses.KEY_UP, ord('k')):
                self.selected_group_idx = (self.selected_group_idx - 1) % len(items)
            elif key in (curses.KEY_DOWN, ord('j')):
                self.selected_group_idx = (self.selected_group_idx + 1) % len(items)
            elif key in (10, 13):
                if self.selected_group_idx == 0:
                    self.input_buffer = ""
                    self.change_state("CREATE_GROUP_NAME", 1)
                else:
                    target = self.groups[self.selected_group_idx - 1]
                    if self.group_passwords.get(target):
                        self.target_group_join = target
                        self.input_buffer = ""
                        self.change_state("ENTER_GROUP_PASS", 1)
                    else:
                        self.current_group = target
                        self.change_state("GROUP_CHAT", 1)

        elif self.state == "CREATE_GROUP_NAME":
            if key in (10, 13):
                name = self.input_buffer.strip()
                if name:
                    self.temp_group_name = name
                    self.input_buffer = ""
                    self.change_state("CREATE_GROUP_PASS", 1)
            elif key in (curses.KEY_BACKSPACE, 127, 8):
                self.input_buffer = self.input_buffer[:-1]
            elif 32 <= key <= 126:
                self.input_buffer += chr(key)

        elif self.state == "CREATE_GROUP_PASS":
            if key in (10, 13):
                password = self.input_buffer.strip()
                if self.temp_group_name not in self.groups:
                    self.groups.append(self.temp_group_name)
                if password:
                    self.group_passwords[self.temp_group_name] = password
                self.current_group = self.temp_group_name
                self.save_config()
                self.input_buffer = ""
                self.change_state("GROUP_CHAT", 1)
            elif key in (curses.KEY_BACKSPACE, 127, 8):
                self.input_buffer = self.input_buffer[:-1]
            elif 32 <= key <= 126:
                self.input_buffer += chr(key)

        elif self.state == "ENTER_GROUP_PASS":
            if key in (10, 13):
                entered_pass = self.input_buffer.strip()
                real_pass = self.group_passwords.get(self.target_group_join, "")
                if entered_pass == real_pass:
                    self.current_group = self.target_group_join
                    self.change_state("GROUP_CHAT", 1)
                self.input_buffer = ""
            elif key in (curses.KEY_BACKSPACE, 127, 8):
                self.input_buffer = self.input_buffer[:-1]
            elif 32 <= key <= 126:
                self.input_buffer += chr(key)

        elif self.state == "FRIENDS":
            items = ["[ + ADD FRIEND BY ID ]"] + self.friends
            if key in (curses.KEY_UP, ord('k')):
                self.selected_friend_idx = (self.selected_friend_idx - 1) % len(items)
            elif key in (curses.KEY_DOWN, ord('j')):
                self.selected_friend_idx = (self.selected_friend_idx + 1) % len(items)
            elif key in (10, 13):
                if self.selected_friend_idx == 0:
                    self.input_buffer = ""
                    self.change_state("ADD_FRIEND", 1)
                else:
                    self.active_friend = self.friends[self.selected_friend_idx - 1]
                    self.load_dm(self.active_friend)
                    self.change_state("DM_CHAT", 1)

        elif self.state == "ADD_FRIEND":
            if key in (10, 13):
                friend_id = self.input_buffer.strip().upper()
                if friend_id and friend_id not in self.friends:
                    self.friends.append(friend_id)
                    self.save_config()
                self.input_buffer = ""
                self.change_state("FRIENDS", 0)
            elif key in (curses.KEY_BACKSPACE, 127, 8):
                self.input_buffer = self.input_buffer[:-1]
            elif 32 <= key <= 126:
                self.input_buffer += chr(key)

        elif self.state == "DM_CHAT":
            if key in (10, 13):
                text = self.input_buffer.strip()
                if text:
                    msg_fmt = f"[{time.strftime('%H:%M')}] {self.username}: {text}"
                    if self.active_friend not in self.dm_messages:
                        self.dm_messages[self.active_friend] = []
                    self.dm_messages[self.active_friend].append(msg_fmt)
                    self.save_dm(self.active_friend)
                    self.input_buffer = ""
            elif key in (curses.KEY_BACKSPACE, 127, 8):
                self.input_buffer = self.input_buffer[:-1]
            elif 32 <= key <= 126:
                self.input_buffer += chr(key)

        elif self.state == "THEMES":
            per_page = 7
            total_pages = math.ceil(len(self.theme_items) / per_page) or 1

            if key == curses.KEY_RIGHT:
                self.selected_theme_page = (self.selected_theme_page + 1) % total_pages
                self.selected_theme_idx = self.selected_theme_page * per_page
            elif key == curses.KEY_LEFT:
                self.selected_theme_page = (self.selected_theme_page - 1) % total_pages
                self.selected_theme_idx = self.selected_theme_page * per_page
            elif key in (curses.KEY_UP, ord('k')):
                if self.selected_theme_idx > 0:
                    self.selected_theme_idx -= 1
                    self.selected_theme_page = self.selected_theme_idx // per_page
            elif key in (curses.KEY_DOWN, ord('j')):
                if self.selected_theme_idx < len(self.theme_items) - 1:
                    self.selected_theme_idx += 1
                    self.selected_theme_page = self.selected_theme_idx // per_page
            elif key in (10, 13):
                selected = self.theme_items[self.selected_theme_idx]
                if selected == "[ COLOR PALETTE ]":
                    self.palette_page = 0
                    self.change_state("PALETTE", 0)
                elif selected == "[ CREATE THEME ]":
                    self.create_theme_step = 0
                    self.input_buffer = ""
                    self.change_state("CREATE_THEME_WIZARD", 1)
                else:
                    self.current_theme_name = selected
                    self.load_themes()
                    self.init_colors()
                    self.save_config()
                    self.change_state("MENU", 0)

        elif self.state == "CREATE_THEME_WIZARD":
            if key in (10, 13):
                val = self.input_buffer.strip()
                if self.create_theme_step == 0:
                    if val:
                        self.new_theme_name = val
                        self.create_theme_step = 1
                        self.input_buffer = ""
                elif self.create_theme_step == 1:
                    self.new_theme_primary = int(val) if val.isdigit() else 6
                    self.create_theme_step = 2
                    self.input_buffer = ""
                elif self.create_theme_step == 2:
                    self.new_theme_secondary = int(val) if val.isdigit() else 5
                    self.create_theme_step = 3
                    self.input_buffer = ""
                elif self.create_theme_step == 3:
                    self.new_theme_text = int(val) if val.isdigit() else 7
                    self.create_theme_step = 4
                    self.input_buffer = ""
                elif self.create_theme_step == 4:
                    grad_parts = val.split()
                    grad_list = [int(p) for p in grad_parts if p.isdigit()]
                    if not grad_list:
                        grad_list = [self.new_theme_primary, self.new_theme_secondary]
                    
                    theme_payload = {
                        "primary": self.new_theme_primary,
                        "secondary": self.new_theme_secondary,
                        "text": self.new_theme_text,
                        "gradient": grad_list
                    }
                    
                    filepath = os.path.join(THEMES_DIR, f"{self.new_theme_name}.json")
                    with open(filepath, "w", encoding="utf-8") as f:
                        json.dump(theme_payload, f, ensure_ascii=False, indent=4)

                    self.current_theme_name = self.new_theme_name
                    self.load_themes()
                    self.init_colors()
                    self.save_config()
                    self.input_buffer = ""
                    self.change_state("MENU", 0)
            elif key in (curses.KEY_BACKSPACE, 127, 8):
                self.input_buffer = self.input_buffer[:-1]
            elif 32 <= key <= 126:
                self.input_buffer += chr(key)

        elif self.state == "PALETTE":
            total_colors = min(curses.COLORS, 256)
            total_pages = math.ceil(total_colors / 48) or 1
            if key == curses.KEY_RIGHT:
                self.palette_page = (self.palette_page + 1) % total_pages
            elif key == curses.KEY_LEFT:
                self.palette_page = (self.palette_page - 1) % total_pages

        elif self.state == "PROFILE":
            if key in (10, 13):
                if self.input_buffer.strip():
                    self.username = self.input_buffer.strip()
                    self.save_config()
                self.input_buffer = ""
                self.change_state("MENU", 0)
            elif key in (curses.KEY_BACKSPACE, 127, 8):
                self.input_buffer = self.input_buffer[:-1]
            elif 32 <= key <= 126:
                self.input_buffer += chr(key)

        elif self.state == "CHAT":
            if key in (10, 13):
                text = self.input_buffer.strip()
                if text:
                    threading.Thread(
                        target=async_send_global_message,
                        args=(self.username, text),
                        daemon=True
                    ).start()
                    self.input_buffer = ""
            elif key in (curses.KEY_BACKSPACE, 127, 8):
                self.input_buffer = self.input_buffer[:-1]
            elif key == curses.KEY_UP:
                if self.scroll_offset < len(self.global_messages) - 1:
                    self.scroll_offset += 1
            elif key == curses.KEY_DOWN:
                if self.scroll_offset > 0:
                    self.scroll_offset -= 1
            elif 32 <= key <= 126:
                self.input_buffer += chr(key)

        elif self.state == "GROUP_CHAT":
            if key in (10, 13):
                text = self.input_buffer.strip()
                if text:
                    threading.Thread(
                        target=async_send_group_message,
                        args=(self.username, text, self.current_group),
                        daemon=True
                    ).start()
                    self.input_buffer = ""
            elif key in (curses.KEY_BACKSPACE, 127, 8):
                self.input_buffer = self.input_buffer[:-1]
            elif key == curses.KEY_UP:
                msgs = self.group_messages.get(self.current_group, [])
                if self.scroll_offset < len(msgs) - 1:
                    self.scroll_offset += 1
            elif key == curses.KEY_DOWN:
                if self.scroll_offset > 0:
                    self.scroll_offset -= 1
            elif 32 <= key <= 126:
                self.input_buffer += chr(key)

        return True


if __name__ == "__main__":
    app = EchoApp()
    curses.wrapper(app.run)
