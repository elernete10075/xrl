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
import firebase_admin
from firebase_admin import credentials, db

# ==========================================
# FIREBASE & ASYNC ENGINE
# ==========================================
DB_URL = "https://xrl-chat-default-rtdb.europe-west1.firebasedatabase.app/"

messages_ref = None
users_ref = None
msg_queue = queue.Queue()

def init_firebase():
    global messages_ref, users_ref
    cred_file = "Server_1.json"
    if os.path.exists(cred_file):
        try:
            if not firebase_admin._apps:
                cred = credentials.Certificate(cred_file)
                firebase_admin.initialize_app(cred, {'databaseURL': DB_URL})
            messages_ref = db.reference("messages")
            users_ref = db.reference("users")
        except Exception:
            pass

init_firebase()

def generate_unique_id():
    ID_FILE = "ac_id"
    if os.path.exists(ID_FILE):
        with open(ID_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()

    new_id = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
    if users_ref:
        try:
            existing_users = users_ref.get() or {}
            while new_id in existing_users:
                new_id = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
            users_ref.child(new_id).set({"created_at": time.time()})
        except Exception:
            pass

    with open(ID_FILE, "w", encoding="utf-8") as f:
        f.write(new_id)

    return new_id

def async_send_message(username, text, group="Global"):
    if not messages_ref:
        return
    try:
        messages_ref.push({
            'username': username,
            'text': text,
            'group': group,
            'timestamp': time.time()
        })
    except Exception as e:
        msg_queue.put({"type": "error", "content": f"[System Error]: {e}"})

def background_fetch_loop():
    last_seen_keys = set()
    while True:
        try:
            if messages_ref:
                data = messages_ref.order_by_key().limit_to_last(50).get()
                if data and isinstance(data, dict):
                    for key, val in data.items():
                        if key not in last_seen_keys:
                            last_seen_keys.add(key)
                            if isinstance(val, dict) and 'text' in val and 'username' in val:
                                msg_queue.put({
                                    "type": "chat",
                                    "username": val.get('username'),
                                    "text": val.get('text'),
                                    "group": val.get('group', 'Global')
                                })
        except Exception:
            pass
        time.sleep(0.4)

def start_firebase_stream():
    threading.Thread(target=background_fetch_loop, daemon=True).start()


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
        self.user_id = generate_unique_id()
        self.username = "User"
        self.current_group = "Global"
        self.current_theme_name = "default"
        self.active_theme = DEFAULT_THEME_DATA["default"]
        self.messages = []
        self.groups = ["Global"]
        self.group_passwords = {}
        self.friends = []
        self.active_friend = None
        self.dm_messages = {}

        self.menu_items = ["Chat", "Groups", "Friends", "Profile", "Themes", "Exit"]
        self.selected_menu = 0
        self.selected_group_idx = 0
        self.selected_friend_idx = 0
        
        self.theme_items = []
        self.selected_theme_page = 0
        self.selected_theme_idx = 0
        
        self.palette_page = 0
        
        # Переменные для создания темы
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
        self.clean_junk_groups()
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

    def clean_junk_groups(self):
        junk = ["Random", "VIP", "Developers"]
        self.groups = [g for g in self.groups if g not in junk]
        if "Global" not in self.groups:
            self.groups.insert(0, "Global")
        for j in junk:
            self.group_passwords.pop(j, None)
        self.save_config()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    self.username = cfg.get("username", self.username)
                    self.current_theme_name = cfg.get("theme", self.current_theme_name)
                    self.groups = cfg.get("groups", ["Global"])
                    self.group_passwords = cfg.get("group_passwords", {})
                    self.friends = cfg.get("friends", self.friends)
            except Exception:
                pass

    def save_config(self):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "username": self.username,
                "theme": self.current_theme_name,
                "groups": self.groups,
                "group_passwords": self.group_passwords,
                "friends": self.friends
            }, f, ensure_ascii=False, indent=4)

    def load_dm(self, friend_id):
        filepath = os.path.join(FRIENDS_DIR, f"{friend_id}.json")
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    self.dm_messages[friend_id] = json.load(f)
            except Exception:
                self.dm_messages[friend_id] = []
        else:
            self.dm_messages[friend_id] = []

    def save_dm(self, friend_id):
        filepath = os.path.join(FRIENDS_DIR, f"{friend_id}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.dm_messages.get(friend_id, []), f, ensure_ascii=False, indent=4)

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

            # Инициализируем пары для 256 цветов палитры (диапазон пара 20..275)
            max_colors = min(curses.COLORS, 256)
            for c in range(max_colors):
                try:
                    curses.init_pair(20 + c, curses.COLOR_BLACK, c)
                except Exception:
                    pass

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

        start_firebase_stream()

        while True:
            while not msg_queue.empty():
                item = msg_queue.get()
                if item.get("type") == "chat":
                    formatted = f"[{item['group']}] {item['username']}: {item['text']}"
                    self.messages.append(formatted)

            self.draw()
            if not self.handle_input():
                break
            time.sleep(0.02)

    def draw(self):
        self.stdscr.erase()
        height, width = self.stdscr.getmaxyx()

        if self.state == "MENU":
            self.draw_menu(height, width)
        elif self.state == "CHAT":
            self.draw_chat(height, width)
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

    def draw_chat(self, height, width):
        header = f"=== ECHO CHAT | Group: {self.current_group} | User: {self.username} ==="
        try:
            self.stdscr.addstr(0, 0, header[:width-1], curses.color_pair(1) | curses.A_BOLD)
            self.stdscr.addstr(1, 0, "-" * (width-1), curses.color_pair(2))
        except curses.error:
            pass

        chat_height = height - 4
        if chat_height > 0:
            visible = [m for m in self.messages if m.startswith(f"[{self.current_group}]")]
            visible = visible[-(chat_height + self.scroll_offset): len(visible) - self.scroll_offset if self.scroll_offset > 0 else None]
            for idx, msg in enumerate(visible[:chat_height]):
                try:
                    self.stdscr.addstr(2 + idx, 0, msg[:width-1], curses.color_pair(3))
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
            self.stdscr.addstr(start_y, 0, "=== SELECT GROUP ===", curses.color_pair(1) | curses.A_BOLD)
            self.stdscr.addstr(start_y + 1, 0, "[Press 'C' to Create New Group]", curses.color_pair(2))
        except curses.error:
            pass

        for idx, grp in enumerate(self.groups):
            y = start_y + 3 + idx
            is_locked = " [LOCKED]" if self.group_passwords.get(grp) else ""
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
                self.stdscr.addstr(start_y + 3, 0, f"Set Password (leave empty for none): {self.input_buffer}", curses.color_pair(1) | curses.A_BOLD)
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
            self.stdscr.addstr(start_y + 1, 0, "[Press 'A' to Add Friend by ID]", curses.color_pair(2))
        except curses.error:
            pass

        if not self.friends:
            try:
                self.stdscr.addstr(start_y + 3, 3, "No friends added yet.", curses.color_pair(3))
            except curses.error:
                pass
        else:
            for idx, fr in enumerate(self.friends):
                y = start_y + 3 + idx
                if idx == self.selected_friend_idx:
                    attr = curses.color_pair(4) | curses.A_BOLD
                    prefix = " > "
                else:
                    attr = curses.color_pair(3)
                    prefix = "   "
                try:
                    self.stdscr.addstr(y, 0, f"{prefix}{fr}", attr)
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
        header = f"=== Friend ID: {self.active_friend} | Local Save Active ==="
        try:
            self.stdscr.addstr(0, 0, header[:width-1], curses.color_pair(1) | curses.A_BOLD)
            self.stdscr.addstr(1, 0, "-" * (width-1), curses.color_pair(2))
        except curses.error:
            pass

        chat_height = height - 4
        msgs = self.dm_messages.get(self.active_friend, [])
        if chat_height > 0:
            visible = msgs[-(chat_height + self.scroll_offset): len(msgs) - self.scroll_offset if self.scroll_offset > 0 else None]
            for idx, msg in enumerate(visible[:chat_height]):
                try:
                    self.stdscr.addstr(2 + idx, 0, msg[:width-1], curses.color_pair(3))
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
                self.stdscr.addstr(start_y + 2, 0, f"Gradient Color IDs (space-separated, e.g. '5 1 6'): {self.input_buffer}", curses.color_pair(3))
                self.stdscr.addstr(start_y + 4, 0, "[Enter] Finish & Save Theme", curses.color_pair(2))
        except curses.error:
            pass

    def draw_palette(self, height, width):
        self.draw_logo(self.stdscr)
        start_y = len(LOGO) + 2
        
        total_colors = min(curses.COLORS, 256)
        per_page = 16
        total_pages = math.ceil(total_colors / per_page) or 1
        
        start_c = self.palette_page * per_page
        end_c = min(start_c + per_page, total_colors)

        try:
            self.stdscr.addstr(start_y, 0, f"=== 256 COLOR PALETTE (Page {self.palette_page + 1}/{total_pages}) ===", curses.color_pair(1) | curses.A_BOLD)
            self.stdscr.addstr(start_y + 1, 0, "[Left/Right] Page  |  [Esc] Back", curses.color_pair(2))

            for idx, c in enumerate(range(start_c, end_c)):
                y = start_y + 3 + idx
                sample = "  "
                attr = curses.color_pair(20 + c)
                self.stdscr.addstr(y, 0, f" Color ID {c:3d}: ", curses.color_pair(3))
                self.stdscr.addstr(y, 16, "[", curses.color_pair(3))
                self.stdscr.addstr(y, 17, sample, attr)
                self.stdscr.addstr(y, 19, "]", curses.color_pair(3))
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
            if self.state in ("CHAT", "GROUPS", "FRIENDS", "PROFILE", "THEMES"):
                self.state = "MENU"
                curses.curs_set(0)
            elif self.state in ("PALETTE", "CREATE_THEME_WIZARD"):
                self.state = "THEMES"
                curses.curs_set(0)
            elif self.state in ("CREATE_GROUP_NAME", "CREATE_GROUP_PASS", "ENTER_GROUP_PASS"):
                self.input_buffer = ""
                self.state = "GROUPS"
                curses.curs_set(0)
            elif self.state == "ADD_FRIEND":
                self.input_buffer = ""
                self.state = "FRIENDS"
                curses.curs_set(0)
            elif self.state == "DM_CHAT":
                self.state = "FRIENDS"
                curses.curs_set(0)
            return True

        if self.state == "MENU":
            if key in (curses.KEY_UP, ord('k')):
                self.selected_menu = (self.selected_menu - 1) % len(self.menu_items)
            elif key in (curses.KEY_DOWN, ord('j')):
                self.selected_menu = (self.selected_menu + 1) % len(self.menu_items)
            elif key in (10, 13):
                choice = self.menu_items[self.selected_menu]
                if choice == "Chat":
                    self.state = "CHAT"
                    curses.curs_set(1)
                elif choice == "Groups":
                    self.state = "GROUPS"
                elif choice == "Friends":
                    self.state = "FRIENDS"
                elif choice == "Profile":
                    self.state = "PROFILE"
                    curses.curs_set(1)
                elif choice == "Themes":
                    self.state = "THEMES"
                elif choice == "Exit":
                    return False

        elif self.state == "GROUPS":
            if key in (ord('c'), ord('C')):
                self.state = "CREATE_GROUP_NAME"
                self.input_buffer = ""
                curses.curs_set(1)
            elif key in (curses.KEY_UP, ord('k')):
                self.selected_group_idx = (self.selected_group_idx - 1) % len(self.groups)
            elif key in (curses.KEY_DOWN, ord('j')):
                self.selected_group_idx = (self.selected_group_idx + 1) % len(self.groups)
            elif key in (10, 13):
                target = self.groups[self.selected_group_idx]
                if self.group_passwords.get(target):
                    self.target_group_join = target
                    self.state = "ENTER_GROUP_PASS"
                    self.input_buffer = ""
                    curses.curs_set(1)
                else:
                    self.current_group = target
                    self.state = "CHAT"
                    curses.curs_set(1)

        elif self.state == "CREATE_GROUP_NAME":
            if key in (10, 13):
                name = self.input_buffer.strip()
                if name:
                    self.temp_group_name = name
                    self.input_buffer = ""
                    self.state = "CREATE_GROUP_PASS"
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
                self.state = "CHAT"
                curses.curs_set(1)
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
                    self.state = "CHAT"
                    curses.curs_set(1)
                self.input_buffer = ""
            elif key in (curses.KEY_BACKSPACE, 127, 8):
                self.input_buffer = self.input_buffer[:-1]
            elif 32 <= key <= 126:
                self.input_buffer += chr(key)

        elif self.state == "FRIENDS":
            if key in (ord('a'), ord('A')):
                self.state = "ADD_FRIEND"
                self.input_buffer = ""
                curses.curs_set(1)
            elif self.friends:
                if key in (curses.KEY_UP, ord('k')):
                    self.selected_friend_idx = (self.selected_friend_idx - 1) % len(self.friends)
                elif key in (curses.KEY_DOWN, ord('j')):
                    self.selected_friend_idx = (self.selected_friend_idx + 1) % len(self.friends)
                elif key in (10, 13):
                    self.active_friend = self.friends[self.selected_friend_idx]
                    self.load_dm(self.active_friend)
                    self.state = "DM_CHAT"
                    curses.curs_set(1)

        elif self.state == "ADD_FRIEND":
            if key in (10, 13):
                friend_id = self.input_buffer.strip().upper()
                if friend_id and friend_id not in self.friends:
                    self.friends.append(friend_id)
                    self.save_config()
                self.input_buffer = ""
                self.state = "FRIENDS"
                curses.curs_set(0)
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
                    self.state = "PALETTE"
                    self.palette_page = 0
                elif selected == "[ CREATE THEME ]":
                    self.state = "CREATE_THEME_WIZARD"
                    self.create_theme_step = 0
                    self.input_buffer = ""
                    curses.curs_set(1)
                else:
                    self.current_theme_name = selected
                    self.load_themes()
                    self.init_colors()
                    self.save_config()
                    self.state = "MENU"

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
                    self.state = "MENU"
                    curses.curs_set(0)
            elif key in (curses.KEY_BACKSPACE, 127, 8):
                self.input_buffer = self.input_buffer[:-1]
            elif 32 <= key <= 126:
                self.input_buffer += chr(key)

        elif self.state == "PALETTE":
            total_colors = min(curses.COLORS, 256)
            total_pages = math.ceil(total_colors / 16) or 1
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
                self.state = "MENU"
                curses.curs_set(0)
            elif key in (curses.KEY_BACKSPACE, 127, 8):
                self.input_buffer = self.input_buffer[:-1]
            elif 32 <= key <= 126:
                self.input_buffer += chr(key)

        elif self.state == "CHAT":
            if key in (10, 13):
                text = self.input_buffer.strip()
                if text:
                    threading.Thread(
                        target=async_send_message,
                        args=(self.username, text, self.current_group),
                        daemon=True
                    ).start()
                    self.input_buffer = ""
            elif key in (curses.KEY_BACKSPACE, 127, 8):
                self.input_buffer = self.input_buffer[:-1]
            elif key == curses.KEY_UP:
                if self.scroll_offset < len(self.messages) - 1:
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
