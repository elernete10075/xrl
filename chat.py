import os
import time
import random
import threading
import curses
import firebase_admin
import re
import ssl
import logging
import requests
import locale
import json
import sys

from firebase_admin import credentials, db
from cryptography.fernet import Fernet

if sys.platform == "win32":
    import winsound

try:
    locale.setlocale(locale.LC_ALL, '')
except Exception:
    pass

# ИСПРАВЛЕНО: Убраны лишние слэши \ из параметра format
logging.basicConfig(filename="xrl_error.log", level=logging.ERROR, 
                    format="%(asctime)s - %(levelname)s - %(message)s")

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError: 
    pass
else: 
    ssl._create_default_https_context = _create_unverified_https_context

# --- КОНФИГУРАЦИЯ ---
FIREBASE_WEB_API_KEY = "AIzaSyAQzzGsmH4o3ZgFFZM017kw9zG0HRe7ZBg"
KEY = b'uX7Y8Z9a1B2c3D4e5F6g7H8i9J0k1L2m3N4o5P6q7R8=' 
cipher = Fernet(KEY)
CRED_PATH = "Server_1.json"
DB_URL = "https://xrl-chat-default-rtdb.europe-west1.firebasedatabase.app/"

if not firebase_admin._apps:
    try:
        if os.path.exists(CRED_PATH):
            cred = credentials.Certificate(CRED_PATH)
            firebase_admin.initialize_app(cred, {'databaseURL': DB_URL})
            print("Инициализация через Service Account успешна.")
        else:
            firebase_admin.initialize_app(options={'databaseURL': DB_URL})
            print("Анонимный режим.")
    except Exception as e:
        logging.error(f"Ошибка инициализации Firebase: {e}")

class XRLChat:
    def __init__(self):
        self.session = "Loading..."
        self.nick = "thoned"
        self.sound_enabled = False
        self.running = True
        self.cache_file = "xrl_cache.txt"
        self.config_file = "xrl_config.txt"
        self.themes_dir = "themes"
        self.themes_config_file = "themes_config.txt"
        self.account_file = "chat_ac.txt"
        
        self.my_uid = None
        self.my_pwd = None
        
        self.messages_history = []
        self.raw_messages_keys = []  
        self.groups_raw = {} 
        self.current_path = "messages/chat"
        self.needs_update = True
        self.listener_obj = None
        self.in_chat = False
        self.data_lock = threading.Lock()

        self.header_text = " - E C H O - "
        self.separator_char = "="
        self.msg_prefix = " {name} : "
        self.input_prefix = " > "
        self.logo_gradient = True 

        self.default_logo = [
            "░▒▓████████▓▒ ░▒▓██████▓▒░ ▒▓█▓▒░░▒▓█▓▒  ▒▓██████▓▒░  ",
            "░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒ ▒▓█▓▒░░▒▓█▓▒ ▒▓█▓▒░░▒▓█▓▒░ ",
            "░▒▓█▓▒░      ░▒▓█▓▒░       ▒▓█▓▒░░▒▓█▓▒ ▒▓█▓▒░░▒▓█▓▒░ ",
            "░▒▓██████▓▒░ ░▒▓█▓▒░       ▒▓████████▓▒ ▒▓█▓▒░░▒▓█▓▒░ ",
            "░▒▓█▓▒░      ░▒▓█▓▒░       ▒▓█▓▒░░▒▓█▓▒ ▒▓█▓▒░░▒▓█▓▒░ ",
            "░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒ ▒▓█▓▒░░▒▓█▓▒ ▒▓█▓▒░░▒▓█▓▒░ ",
            "░▒▓████████▓▒ ░▒▓██████▓▒░ ▒▓█▓▒░░▒▓█▓▒  ▒▓██████▓▒░  ",
            "──────────────────────────────────────────────────────"
        ]
        self.current_logo = list(self.default_logo)

        self.theme_colors = {
            "text_background": {"color": 16, "gradient": False},
            "text_primary": {"color": 255, "gradient": True},
            "text_accent": {"color": 255, "gradient": False},
            "gradient": [160, 196, 160, 196, 160, 160, 160, 160]
        }

        if not os.path.exists(self.cache_file): 
            open(self.cache_file, 'w', encoding="utf-8").close()
        
        self.load_settings()
        self.init_themes_system()
        self.load_msg_cache()
        self.load_local_account()

    def encrypt(self, text): 
        return cipher.encrypt(text.encode('utf-8')).decode('utf-8')
        
    def decrypt(self, token):
        try: 
            return cipher.decrypt(token.encode('utf-8')).decode('utf-8')
        except Exception: 
            return None

    def play_notification_sound(self):
        if not self.sound_enabled:
            return
            
        def async_sound():
            try:
                if sys.platform == "win32":
                    winsound.MessageBeep(winsound.MB_ICONASTERISK)
                else:
                    linux_sound_paths = [
                        "/usr/share/sounds/freedesktop/stereo/bell.oga",
                        "/usr/share/sounds/freedesktop/stereo/message-new-instant.oga",
                        "/usr/share/sounds/gnome/default/alerts/glass.ogg",
                        "/usr/share/sounds/ubuntu/audio/bell.ogg"
                    ]
                    played = False
                    for path in linux_sound_paths:
                        if os.path.exists(path):
                            os.system(f"paplay {path} > /dev/null 2>&1 &")
                            played = True
                            break
                    
                    if not played:
                        sys.stdout.write("\t\a")
                        sys.stdout.flush()
            except Exception as e:
                logging.error(f"Ошибка воспроизведения звука: {e}")

        threading.Thread(target=async_sound, daemon=True).start()

    def check_and_trim_chat_limit(self, path):
        def async_trim():
            time.sleep(random.uniform(1.0, 2.0))
            try:
                snap = db.reference(path).get()
                if snap and isinstance(snap, dict) and len(snap) > 15:
                    sorted_keys = sorted(list(snap.keys()))
                    to_delete_count = len(sorted_keys) - 15
                    
                    for i in range(to_delete_count):
                        target_key = sorted_keys[i]
                        check_exists = db.reference(f"{path}/{target_key}").get()
                        if check_exists:
                            db.reference(f"{path}/{target_key}").delete()
            except Exception as e:
                logging.error(f"Ошибка автоматического тримминга базы: {e}")

        threading.Thread(target=async_trim, daemon=True).start()

    def clear_my_messages_on_server(self):
        try:
            path = self.current_path
            snap = db.reference(path).get()
            if snap and isinstance(snap, dict):
                for k, v in snap.items():
                    raw = v.get('payload') if isinstance(v, dict) else v
                    dec = self.decrypt(raw)
                    if dec:
                        match = re.search(r"\(.*?\)\s\((.*?)\)\s\((.*?)\)\s>(.*)<", dec)
                        if match:
                            _, name, _ = match.groups()
                            if name == self.nick:
                                db.reference(f"{path}/{k}").delete()
            return True
        except Exception as e:
            logging.error(f"Ошибка при очистке сообщений пользователя: {e}")
            return False

    def load_settings(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if ":" in content:
                        saved_nick, saved_sound = content.split(":", 1)
                        self.nick = saved_nick
                        self.sound_enabled = saved_sound == "True"
                    else:
                        if content:
                            self.nick = content
            except Exception as e:
                logging.error(f"Ошибка загрузки настроек: {e}")

    def save_settings(self):
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                f.write(f"{self.nick}:{self.sound_enabled}")
        except Exception as e:
            logging.error(f"Ошибка сохранения настроек: {e}")

    def load_local_account(self):
        if os.path.exists(self.account_file):
            try:
                with open(self.account_file, "r", encoding="utf-8") as f:
                    data = f.read().strip().split(":")
                    if len(data) == 2:
                        self.my_uid = data[0]
                        self.my_pwd = data[1]
            except Exception as e:
                logging.error(f"Ошибка чтения chat_ac.txt: {e}")

    def save_local_account(self):
        try:
            with open(self.account_file, "w", encoding="utf-8") as f:
                f.write(f"{self.my_uid}:{self.my_pwd}")
        except Exception as e:
            logging.error(f"Ошибка сохранения chat_ac.txt: {e}")

    def register_firebase_account(self, stdscr):
        stdscr.erase()
        self.draw_small_header(stdscr)
        stdscr.addstr(5, 2, " [ GENERATING UNIQUE ID... ] ", curses.A_REVERSE)
        stdscr.refresh()

        pwd = self.safe_input(stdscr, 7, 2, " Enter Password for New Account: ")
        if not pwd:
            return False

        def registration_transaction(current_data):
            if current_data is None:
                current_data = {}
            
            chosen = 1
            while str(chosen) in current_data:
                chosen += 1
                
            current_data[str(chosen)] = {
                "password": self.encrypt(pwd),
                "nick": self.encrypt(self.nick)
            }
            registration_transaction.allocated_id = str(chosen)
            return current_data

        registration_transaction.allocated_id = None

        try:
            ref = db.reference("accounts")
            ref.transaction(registration_transaction)
            
            allocated_id = registration_transaction.allocated_id
            if allocated_id:
                self.my_uid = allocated_id
                self.my_pwd = pwd
                self.save_local_account()
                
                stdscr.addstr(9, 2, f" Account successfully created! ID: {allocated_id} ", curses.A_REVERSE)
                stdscr.refresh()
                time.sleep(2)
                return True
            else:
                stdscr.addstr(9, 2, " Transaction error. Try again. ", curses.color_pair(1))
                stdscr.refresh()
                time.sleep(2)
                return False
        except Exception as e:
            logging.error(f"Ошибка транзакции при регистрации: {e}")
            return False

    def write_theme_to_file(self, path):
        theme_structure = {
            "colors": {
                "text_background": {"color": 16, "gradient": False},
                "text_primary": {"color": 255, "gradient": True},
                "text_accent": {"color": 255, "gradient": False},
                "gradient": [160, 196, 160, 196, 160, 160, 160, 160]
            },
            "ui": {
                "header_text": " - E C H O - ",
                "separator_char": "=",
                "msg_prefix": " {name} : ",
                "input_prefix": " > ",
                "logo_gradient": True,
                "logo": self.default_logo
            }
        }
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(theme_structure, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logging.error(f"Ошибка записи JSON темы: {e}")

    def init_themes_system(self):
        if not os.path.exists(self.themes_dir):
            os.makedirs(self.themes_dir)
        
        default_theme_path = os.path.join(self.themes_dir, "default.json")
        if not os.path.exists(default_theme_path):
            self.write_theme_to_file(default_theme_path)

        if not os.path.exists(self.themes_config_file):
            with open(self.themes_config_file, "w", encoding="utf-8") as f:
                f.write("default")
            self.load_theme("default")
        else:
            try:
                with open(self.themes_config_file, "r", encoding="utf-8") as f:
                    active_theme = f.read().strip()
                if not active_theme:
                    active_theme = "default"
                self.load_theme(active_theme)
            except:
                self.load_theme("default")

    def load_theme(self, theme_name):
        path = os.path.join(self.themes_dir, f"{theme_name}.json")
        if not os.path.exists(path) and os.path.exists(os.path.join(self.themes_dir, f"{theme_name}.txt")):
            path = os.path.join(self.themes_dir, f"{theme_name}.txt")

        if not os.path.exists(path):
            return False
        try:
            with open(path, "r", encoding="utf-8") as f:
                raw_content = f.read()

            data = json.loads(raw_content)
            
            if "colors" in data:
                colors = data["colors"]
                for key in ["text_background", "text_primary", "text_accent"]:
                    if key in colors:
                        if isinstance(colors[key], dict):
                            self.theme_colors[key]["color"] = int(colors[key].get("color", 255))
                            self.theme_colors[key]["gradient"] = bool(colors[key].get("gradient", False))
                        else:
                            self.theme_colors[key]["color"] = int(colors[key])
                            self.theme_colors[key]["gradient"] = False
                            
                if "gradient" in colors: 
                    self.theme_colors["gradient"] = colors["gradient"]

            if "ui" in data:
                ui = data["ui"]
                if "header_text" in ui: self.header_text = ui["header_text"]
                if "separator_char" in ui: self.separator_char = ui["separator_char"]
                if "msg_prefix" in ui: self.msg_prefix = ui["msg_prefix"]
                if "input_prefix" in ui: self.input_prefix = ui["input_prefix"]
                if "logo_gradient" in ui: self.logo_gradient = bool(ui["logo_gradient"])
                if "logo" in ui: self.current_logo = ui["logo"]

            self.update_curses_colors()
            return True
        except Exception as e:
            logging.error(f"Ошибка загрузки JSON темы {theme_name}: {e}")
            return False

    def update_curses_colors(self):
        try:
            bg_id = self.theme_colors["text_background"]["color"]
            primary_id = self.theme_colors["text_primary"]["color"]
            accent_id = self.theme_colors["text_accent"]["color"]

            curses.init_pair(1, primary_id, bg_id)
            curses.init_pair(2, accent_id, bg_id)
            curses.init_pair(3, accent_id, bg_id)
            curses.init_pair(4, primary_id, bg_id)
            
            gradient_list = self.theme_colors["gradient"]
            for idx, color_id in enumerate(gradient_list):
                curses.init_pair(50 + idx, color_id, bg_id)
        except Exception as e:
            logging.error(f"Ошибка применения цветов curses: {e}")

    def draw_text_with_gradient(self, stdscr, y, x, text, default_pair, is_gradient_active, extra_attr=0):
        if not text: return
        gradient_list = self.theme_colors["gradient"]
        
        if is_gradient_active and gradient_list:
            current_x = x
            for i, char in enumerate(text):
                grad_pair_idx = 50 + (i % len(gradient_list))
                try:
                    stdscr.addstr(y, current_x, char, curses.color_pair(grad_pair_idx) | extra_attr)
                except:
                    pass
                current_x += len(char.encode('utf-8', 'replace').decode('utf-8', 'replace'))
        else:
            try:
                stdscr.addstr(y, x, text, curses.color_pair(default_pair) | extra_attr)
            except:
                pass

    def draw_element_str(self, stdscr, y, x, text, color_pair_id, extra_attr=0):
        is_grad = False
        if color_pair_id == 1: 
            is_grad = self.theme_colors["text_primary"]["gradient"]
        elif color_pair_id in [2, 3]: 
            is_grad = self.theme_colors["text_accent"]["gradient"]
        elif color_pair_id == 4:
            is_grad = self.logo_gradient
        
        self.draw_text_with_gradient(stdscr, y, x, text, color_pair_id, is_grad, extra_attr)

    def draw_big_logo(self, stdscr):
        for i, line in enumerate(self.current_logo):
            self.draw_text_with_gradient(stdscr, i + 2, 2, line, 4, self.logo_gradient, curses.A_BOLD)

    def draw_small_header(self, stdscr):
        self.draw_element_str(stdscr, 1, 2, self.header_text, 4, curses.A_BOLD)
        sep_line = " " + self.separator_char * 56 + " "
        stdscr.addstr(2, 2, sep_line, curses.color_pair(3)) 
        
        my_id_display = self.my_uid if self.my_uid else "No Account"
        status_line = f" session : {self.session} | ID: {my_id_display} | nick : {self.nick}"
        self.draw_element_str(stdscr, 3, 2, status_line, 3)

    def safe_input(self, stdscr, y, x, prompt):
        stdscr.addstr(y, x, prompt, curses.color_pair(3))
        curses.curs_set(1)
        input_str = ""
        while True:
            stdscr.move(y, x + len(prompt))
            stdscr.clrtoeol()
            stdscr.addstr(y, x + len(prompt), input_str + "_ ")
            stdscr.refresh()
            try:
                ch = stdscr.get_wch()
            except:
                continue

            if ch in [10, 13, '\n', '\r']:
                break
            elif ch in [8, 127, 263, '\b', '\x7f', curses.KEY_BACKSPACE, 'KEY_BACKSPACE']:
                input_str = input_str[:-1]
            elif isinstance(ch, str):
                input_str += ch
                
        curses.curs_set(0)
        return input_str.strip()

    def open_color_palette_viewer(self, stdscr):
        while True:
            stdscr.erase()
            stdscr.bkgd(' ', curses.color_pair(1))
            self.draw_small_header(stdscr)
            stdscr.addstr(5, 2, " [ AVAILABLE 256 COLORS PALETTE ] ", curses.A_BOLD)
            
            bg_id = self.theme_colors["text_background"]["color"]
            start_y = 7
            cols_count = 12
            
            for c_num in range(256):
                row = c_num // cols_count
                col = c_num % cols_count
                
                pair_id = 100 + (c_num % 150)
                try:
                    curses.init_pair(pair_id, c_num, bg_id)
                except:
                    pass
                
                cell_str = f"{c_num:3}"
                try:
                    stdscr.addstr(start_y + row, 2 + (col * 6), cell_str, curses.color_pair(pair_id) | curses.A_BOLD)
                except:
                    pass

            stdscr.addstr(start_y + 23, 2, "Press any key to back...", curses.color_pair(2) | curses.A_REVERSE)
            stdscr.refresh()
            try:
                stdscr.get_wch()
            except:
                pass
            break

    def open_themes_menu(self, stdscr):
        page = 0
        idx = 0
        
        while True:
            theme_files = []
            if os.path.exists(self.themes_dir):
                for f in os.listdir(self.themes_dir):
                    if f.endswith(".json"):
                        theme_files.append(f[:-5])
            theme_files.sort()

            fixed_options = ["[ Create Theme + ]", "[ View Color Palette ]"]
            
            max_per_page = 7
            start_i = page * max_per_page
            end_i = start_i + max_per_page
            page_themes = theme_files[start_i:end_i]
            
            has_next = end_i < len(theme_files)
            
            menu_items = []
            menu_items.extend(fixed_options)
            menu_items.extend(page_themes)
            
            if has_next:
                menu_items.append("> 2page" if page == 0 else f"> {page + 2}page")
            menu_items.append("< Back")

            if idx >= len(menu_items):
                idx = len(menu_items) - 1
            if idx < 0:
                idx = 0

            stdscr.erase()
            stdscr.bkgd(' ', curses.color_pair(1))
            self.draw_small_header(stdscr)
            
            try:
                with open(self.themes_config_file, "r", encoding="utf-8") as f:
                    curr_t = f.read().strip()
            except:
                curr_t = "unknown"
                
            stdscr.addstr(5, 2, f" [ THEMES MENU ] | Active: {curr_t} | Page: {page + 1}", curses.color_pair(3))

            for i, item in enumerate(menu_items):
                style = curses.A_REVERSE if i == idx else 0
                if item in theme_files and item == curr_t:
                    display_text = f" * {item} (Active) "
                else:
                    display_text = f" > {item} "
                
                self.draw_element_str(stdscr, 7 + i, 4, display_text, 2, style)
            
            stdscr.refresh()
            try:
                key = stdscr.get_wch()
            except:
                continue

            if key == curses.KEY_UP or key == 'k':
                if idx > 0: idx -= 1
            elif key == curses.KEY_DOWN or key == 'j':
                if idx < len(menu_items) - 1: idx += 1
            elif key in [10, 13, '\n', '\r']:
                selected = menu_items[idx]
                
                if selected == "[ Create Theme + ]":
                    t_name = self.safe_input(stdscr, 18, 2, " Enter new theme name: ")
                    if t_name:
                        t_path = os.path.join(self.themes_dir, f"{t_name}.json")
                        if not os.path.exists(t_path):
                            self.write_theme_to_file(t_path)
                    idx = 0
                    
                elif selected == "[ View Color Palette ]":
                    self.open_color_palette_viewer(stdscr)
                    
                elif selected == "< Back":
                    if page > 0:
                        page = 0  
                        idx = 0
                    else:
                        break  
                        
                elif "page" in selected and ">" in selected:
                    page += 1
                    idx = 0
                     
                elif selected in theme_files:
                    if self.load_theme(selected):
                        with open(self.themes_config_file, "w", encoding="utf-8") as f:
                            f.write(selected)
                        stdscr.addstr(19, 2, f" Theme '{selected}' applied! ", curses.A_REVERSE)
                        stdscr.refresh()
                        time.sleep(1)

    def open_friends_menu(self, stdscr):
        if not self.my_uid:
            stdscr.erase()
            self.draw_small_header(stdscr)
            stdscr.addstr(6, 2, "You don't have a registered Account ID yet!", curses.color_pair(1))
            stdscr.addstr(8, 2, "[1] Generate Auto ID Account (Protected)", curses.color_pair(2))
            stdscr.addstr(9, 2, "[2] Relogin Existing Account", curses.color_pair(2))
            stdscr.addstr(11, 2, "Press any other key to back...", curses.color_pair(3))
            stdscr.refresh()
            try:
                sel = stdscr.get_wch()
                if sel == '1':
                    self.register_firebase_account(stdscr)
                elif sel == '2':
                    r_id = self.safe_input(stdscr, 13, 2, " Enter ID: ")
                    r_pw = self.safe_input(stdscr, 14, 2, " Enter Password: ")
                    if r_id and r_pw:
                        data = db.reference(f"accounts/{r_id}").get()
                        if data and self.decrypt(data.get("password", "")) == r_pw:
                            self.my_uid = r_id
                            self.my_pwd = r_pw
                            self.save_local_account()
                            stdscr.addstr(16, 2, " Logged in successfully! ", curses.A_REVERSE)
                        else:
                            stdscr.addstr(16, 2, " Invalid ID or Password! ", curses.color_pair(1))
                        stdscr.refresh()
                        time.sleep(1.5)
            except:
                pass
            return

        page = 0
        idx = 0

        while True:
            friends_list = []
            requests_list = []
            
            try:
                f_data = db.reference(f"accounts/{self.my_uid}/friends").get()
                if f_data and isinstance(f_data, dict):
                    friends_list = sorted(list(f_data.keys()))
                
                req_data = db.reference("friends_requests").get() or {}
                for r_id, payload in req_data.items():
                    if isinstance(payload, dict):
                        if payload.get("to") == self.my_uid:
                            requests_list.append({"req_id": r_id, "from": payload.get("from")})
            except Exception as e:
                logging.error(f"Ошибка загрузки данных друзей: {e}")

            max_per_page = 7
            start_i = page * max_per_page
            end_i = start_i + max_per_page
            page_friends = friends_list[start_i:end_i]
            has_next = end_i < len(friends_list)

            menu_items = []
            menu_items.append("Add Friend [ID]")
            menu_items.append("Relogin [ID]")
            
            if requests_list:
                menu_items.append("--- REQUESTS ---")
                for r in requests_list:
                    menu_items.append(f"Request from ID:{r['from']}")
            
            menu_items.append("--- FRIENDS LIST ---")
            if not page_friends:
                menu_items.append("(No friends yet)")
            else:
                for f_id in page_friends:
                    menu_items.append(f"Friend ID:{f_id}")
            
            if has_next:
                menu_items.append("Next Page >")
            if page > 0:
                menu_items.append("< Previous Page")
                
            menu_items.append("Back")

            if idx >= len(menu_items): idx = len(menu_items) - 1
            if idx < 0: idx = 0

            stdscr.erase()
            stdscr.bkgd(' ', curses.color_pair(1))
            self.draw_small_header(stdscr)
            stdscr.addstr(5, 2, f" [ FRIENDS SYSTEM ] | My ID: {self.my_uid} | Page: {page + 1}", curses.color_pair(3))

            for i, item in enumerate(menu_items):
                is_clickable = not item.startswith("---") and item != "(No friends yet)"
                style = curses.A_REVERSE if (i == idx and is_clickable) else 0
                
                if item.startswith("---"):
                    stdscr.addstr(7 + i, 2, item, curses.color_pair(3) | curses.A_BOLD)
                else:
                    prefix = " > " if is_clickable else "   "
                    self.draw_element_str(stdscr, 7 + i, 2, f"{prefix}{item}", 2, style)

            stdscr.refresh()
            try:
                key = stdscr.get_wch()
            except:
                continue

            if key == curses.KEY_UP or key == 'k':
                idx -= 1
                while idx >= 0 and (menu_items[idx].startswith("---") or menu_items[idx] == "(No friends yet)"):
                    idx -= 1
            elif key == curses.KEY_DOWN or key == 'j':
                idx += 1
                while idx < len(menu_items) - 1 and (menu_items[idx].startswith("---") or menu_items[idx] == "(No friends yet)"):
                    idx += 1
            elif key in [10, 13, '\n', '\r']:
                selected = menu_items[idx]
                
                if selected == "Back":
                    break
                    
                elif selected == "Next Page >":
                    page += 1
                    idx = 0
                    
                elif selected == "< Previous Page":
                    page -= 1
                    idx = 0
                    
                elif selected == "Add Friend [ID]":
                    target_id = self.safe_input(stdscr, 18, 2, " Target User ID: ")
                    if target_id == self.my_uid:
                        stdscr.addstr(20, 2, "You can't add yourself!", curses.color_pair(1))
                    elif target_id:
                        target_check = db.reference(f"accounts/{target_id}").get()
                        if target_check:
                            db.reference("friends_requests").push({
                                "from": self.my_uid,
                                "to": target_id
                            })
                            stdscr.addstr(20, 2, " Friend request sent successfully! ", curses.A_REVERSE)
                        else:
                            stdscr.addstr(20, 2, " User ID not found on server! ", curses.color_pair(1))
                    stdscr.refresh()
                    time.sleep(1.5)
                    
                elif selected == "Relogin [ID]":
                    r_id = self.safe_input(stdscr, 18, 2, " Account ID: ")
                    r_pw = self.safe_input(stdscr, 19, 2, " Password: ")
                    if r_id and r_pw:
                        data = db.reference(f"accounts/{r_id}").get()
                        if data and self.decrypt(data.get("password", "")) == r_pw:
                            self.my_uid = r_id
                            self.my_pwd = r_pw
                            self.save_local_account()
                            stdscr.addstr(21, 2, " Relogin Successful! ", curses.A_REVERSE)
                            page = 0
                            idx = 0
                        else:
                            stdscr.addstr(21, 2, " Verification Error! ", curses.color_pair(1))
                    stdscr.refresh()
                    time.sleep(1.5)
                    
                elif selected.startswith("Request from ID:"):
                    from_id = selected.split(":")[-1]
                    req_obj = next((r for r in requests_list if r['from'] == from_id), None)
                    if req_obj:
                        stdscr.addstr(18, 2, f"Accept request from {from_id}? [y - Accept / n - Reject]: ", curses.color_pair(3))
                        stdscr.refresh()
                        try:
                            choice = stdscr.get_wch()
                            if choice in ['y', 'Y']:
                                db.reference(f"accounts/{self.my_uid}/friends/{from_id}").set(True)
                                db.reference(f"accounts/{from_id}/friends/{self.my_uid}").set(True)
                                stdscr.addstr(20, 2, " Friend request Accepted! ", curses.A_REVERSE)
                            else:
                                stdscr.addstr(20, 2, " Request Rejected. ", curses.color_pair(1))
                            db.reference(f"friends_requests/{req_obj['req_id']}").delete()
                            stdscr.refresh()
                            time.sleep(1.5)
                        except:
                            pass
                            
                elif selected.startswith("Friend ID:"):
                    friend_id = selected.split(":")[-1]
                    chat_room = f"messages/p2p/{min(self.my_uid, friend_id)}_{max(self.my_uid, friend_id)}"
                    self.open_p2p_chat(stdscr, chat_room, friend_id)

    def open_p2p_chat(self, stdscr, path, friend_id):
        self.in_chat = True
        self.current_path = path
        self.messages_history = []
        
        try:
            snap = db.reference(path).get() 
            if snap and isinstance(snap, dict):
                for k in snap:
                    raw = snap[k].get('payload') if isinstance(snap[k], dict) else snap[k]
                    dec = self.decrypt(raw)
                    if dec: 
                        self.process_msg(dec)
        except Exception as e:
            logging.error(f"Не удалось открыть приватный чат: {e}")
            
        self.start_msg_listener(path)
        user_input = ""
        stdscr.nodelay(True)
        self.needs_update = True

        while self.in_chat:
            if self.needs_update:
                stdscr.erase()
                stdscr.bkgd(' ', curses.color_pair(1))
                self.draw_small_header(stdscr)
                stdscr.addstr(6, 2, f" --- PRIVATE WITH ID: {friend_id} (/exit или /unfriend) ---", curses.A_REVERSE)
                
                for i, msg in enumerate(self.messages_history[-14:]):
                    self.draw_element_str(stdscr, 8 + i, 2, msg[:75], 1)
                
                try:
                    stdscr.move(23, 2)
                    stdscr.clrtoeol()
                    display_input = f"{self.nick}{self.input_prefix}{user_input}_"
                    self.draw_element_str(stdscr, 23, 2, display_input, 1, curses.A_BOLD)
                except:
                    pass
                stdscr.refresh()
                self.needs_update = False

            try:
                key = stdscr.get_wch()
            except curses.error:
                time.sleep(0.02)
                continue

            self.needs_update = True
            
            if key in [10, 13, '\n', '\r']:
                if user_input == "/exit": 
                    self.in_chat = False
                    break
                elif user_input == "/unfriend":
                    db.reference(f"accounts/{self.my_uid}/friends/{friend_id}").delete()
                    db.reference(f"accounts/{friend_id}/friends/{self.my_uid}").delete()
                    self.in_chat = False
                    break
                if user_input.strip():
                    pkt = f"send-message ({path}) ({self.session}) ({self.nick}) >{user_input}<"
                    try:
                        db.reference(path).push({'payload': self.encrypt(pkt)})
                        self.check_and_trim_chat_limit(path)
                    except Exception as e:
                        logging.error(f"Ошибка отправки сообщения: {e}")
                    user_input = ""
                    
            elif key in [8, 127, 263, '\b', '\x7f', curses.KEY_BACKSPACE, 'KEY_BACKSPACE']: 
                user_input = user_input[:-1]
                
            elif isinstance(key, str): 
                user_input += key

        self.in_chat = False
        self.stop_msg_listener()
        stdscr.nodelay(False)

    def authenticate_anonymously(self):
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_WEB_API_KEY}"
        payload = {"returnSecureToken": True}
        try:
            response = requests.post(url, json=payload, timeout=10)
            res_data = response.json()
            if response.status_code == 200 and "localId" in res_data:
                full_uid = res_data["localId"]
                self.session = full_uid[:8] + "..."
                return True
            else:
                logging.error(f"Firebase Auth Error: {res_data.get('error', {}).get('message', 'Unknown error')}")
                return False
        except Exception as e:
            logging.error(f"Исключение при авторизации Auth: {e}")
            return False

    def load_msg_cache(self):
        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                for line in f:
                    dec = line.strip()
                    if "send-message" in dec: 
                        self.process_msg(dec)
        except Exception as e:
            logging.error(f"Ошибка загрузки кэша: {e}")

    def groups_observer(self):
        def handler(event):
            try:
                data = db.reference('messages/groups_list').get()
                new_groups = {}
                if data and isinstance(data, dict):
                    for k, v in data.items():
                        raw = v.get('payload') if isinstance(v, dict) else v
                        dec = self.decrypt(raw)
                        if dec: 
                            new_groups[k] = dec
                
                with self.data_lock:
                    self.groups_raw = new_groups
                self.needs_update = True
            except Exception as e:
                logging.error(f"Ошибка в обработчике групп: {e}")

        try: 
            db.reference('messages/groups_list').listen(handler)
        except Exception as e: 
            logging.error(f"Ошибка подписки на группы: {e}")

    def start_msg_listener(self, path):
        if self.listener_obj:
            try:
                self.listener_obj.close()
            except:
                pass

        def handler(event):
            if not self.in_chat: 
                return
            if event.data:
                data = event.data
                items = data if isinstance(data, dict) else {'new': data}
                is_new_message = False
                for k in items:
                    val = items[k]
                    raw = val.get('payload') if isinstance(val, dict) else val
                    dec = self.decrypt(raw)
                    if dec and "send-message" in dec: 
                        self.process_msg(dec, save=True)
                        is_new_message = True
                
                if is_new_message:
                    self.play_notification_sound()
                    self.check_and_trim_chat_limit(path)
                self.needs_update = True

        try: 
            self.listener_obj = db.reference(path).listen(handler)
        except Exception as e: 
            logging.error(f"Ошибка подписки на сообщения ({path}): {e}")

    def stop_msg_listener(self):
        """Гарантированное закрытие слушателя при выходе из комнаты"""
        if self.listener_obj:
            try:
                self.listener_obj.close()
                self.listener_obj = None
            except Exception as e:
                logging.error(f"Ошибка закрытия слушателя: {e}")

    def process_msg(self, dec, save=False):
        match = re.search(r"\(.*?\)\s\((.*?)\)\s\((.*?)\)\s>(.*)<", dec)
        if match:
            ses, name, txt = match.groups()
            prefix = self.msg_prefix.format(name=name)
            m = f"| {prefix}{txt}"
            
            self.messages_history.append(m)
            if save:
                try:
                    with open(self.cache_file, "a", encoding="utf-8") as f: 
                        f.write(dec + "\n")
                except Exception as e:
                    logging.error(f"Ошибка записи кэша: {e}")

    def open_chat(self, stdscr, path):
        self.in_chat = True
        self.current_path = path
        self.messages_history = []
        
        try:
            snap = db.reference(path).get() 
            if snap and isinstance(snap, dict):
                for k in snap:
                    raw = snap[k].get('payload') if isinstance(snap[k], dict) else snap[k]
                    dec = self.decrypt(raw)
                    if dec: 
                        self.process_msg(dec)
        except Exception as e:
            logging.error(f"Не удалось получить доступ к чату ({path}): {e}")
            self.messages_history.append("!! ОШИБКА ДОСТУПА К БАЗЕ !!")
            
        self.start_msg_listener(path)
        user_input = ""
        stdscr.nodelay(True)
        self.needs_update = True

        while self.in_chat:
            if self.needs_update:
                stdscr.erase()
                stdscr.bkgd(' ', curses.color_pair(1))
                self.draw_small_header(stdscr)
                stdscr.addstr(6, 2, f" --- ROOM: {path} (type '/exit') ---", curses.A_REVERSE)
                
                for i, msg in enumerate(self.messages_history[-14:]):
                    self.draw_element_str(stdscr, 8 + i, 2, msg[:75], 1)
                
                try:
                    stdscr.move(23, 2)
                    stdscr.clrtoeol()
                    display_input = f"{self.nick}{self.input_prefix}{user_input}_"
                    self.draw_element_str(stdscr, 23, 2, display_input, 1, curses.A_BOLD)
                except:
                    pass
                stdscr.refresh()
                self.needs_update = False

            try:
                key = stdscr.get_wch()
            except curses.error:
                time.sleep(0.02)
                continue

            self.needs_update = True
            
            if key in [10, 13, '\n', '\r']:
                if user_input == "/exit": 
                    self.in_chat = False
                    break
                if user_input.strip():
                    pkt = f"send-message ({path}) ({self.session}) ({self.nick}) >{user_input}<"
                    try:
                        db.reference(path).push({'payload': self.encrypt(pkt)})
                        self.check_and_trim_chat_limit(path)
                    except Exception as e:
                        logging.error(f"Ошибка отправки сообщения: {e}")
                    user_input = ""
                    
            elif key in [8, 127, 263, '\b', '\x7f', curses.KEY_BACKSPACE, 'KEY_BACKSPACE']: 
                user_input = user_input[:-1]
                
            elif isinstance(key, str): 
                user_input += key

        self.in_chat = False
        self.stop_msg_listener()
        stdscr.nodelay(False)

    def open_groups(self, stdscr):
        while True:
            parsed = []
            with self.data_lock:
                current_groups = dict(self.groups_raw)

            for db_key, dec in current_groups.items():
                m = re.search(r"create-group \((.*?)\) \((.*?)\) \((.*?)\)", dec)
                if m: 
                    parsed.append({'pw': m.group(1), 'id': m.group(2), 'name': m.group(3)})
            
            opts = ["+ Refresh", "+ Create", "+ Connect ID"] + [f"ID:{p['id']} | {p['name']}" for p in parsed] + ["Back"]
            idx = 0
            while True:
                stdscr.erase()
                stdscr.bkgd(' ', curses.color_pair(1))
                self.draw_small_header(stdscr)
                stdscr.addstr(6, 2, " [ GROUPS ] ", curses.color_pair(1))
                for i, opt in enumerate(opts):
                    style = curses.A_REVERSE if i == idx else 0
                    self.draw_element_str(stdscr, 8 + i, 4, f" > {opt} ", 2, style)
                stdscr.refresh()
                try:
                    key = stdscr.get_wch()
                except:
                    continue

                if key == curses.KEY_UP or key == 'k': 
                    if idx > 0: idx -= 1
                elif key == curses.KEY_DOWN or key == 'j': 
                    if idx < len(opts)-1: idx += 1
                elif key in [10, 13, '\n', '\r']: 
                    break
                elif key in ['b', 'B']: 
                    idx = len(opts)-1
                    break

            res = opts[idx]
            if res == "+ Refresh": 
                self.needs_update = True
                continue
            elif res == "+ Create":
                name = self.safe_input(stdscr, 18, 2, " Name: ")
                pw = self.safe_input(stdscr, 19, 2, " Pass: ")
                if name and pw:
                    gid = str(random.randint(1, 99999))
                    pkt = f"create-group ({pw}) ({gid}) ({name})"
                    try:
                        db.reference('messages/groups_list').push({'payload': self.encrypt(pkt)})
                    except Exception as e:
                        logging.error(f"Ошибка создания группы: {e}")
                break
            elif res == "+ Connect ID":
                target_id = self.safe_input(stdscr, 18, 2, " Enter ID: ")
                group = next((p for p in parsed if p['id'] == target_id), None)
                if group:
                    input_pw = self.safe_input(stdscr, 19, 2, " Enter Pass: ")
                    if input_pw == group['pw']: 
                        self.open_chat(stdscr, f"messages/groups/{target_id}")
                    else: 
                        stdscr.addstr(21, 2, "!! WRONG PASS !!", curses.color_pair(1))
                        stdscr.refresh()
                        time.sleep(1)
                else: 
                    stdscr.addstr(19, 2, "!! ID NOT FOUND !!", curses.color_pair(1))
                    stdscr.refresh()
                    time.sleep(1)
                break
            elif "ID:" in res:
                g = parsed[idx-3]
                pw = self.safe_input(stdscr, 18, 2, f" Pass for {g['name']}: ")
                if pw == g['pw']: 
                    self.open_chat(stdscr, f"messages/groups/{g['id']}")
                    break
                else: 
                    stdscr.addstr(20, 2, "!! WRONG !!")
                    stdscr.refresh()
                    time.sleep(1)
                    break
            elif res == "Back": 
                break

    def open_settings(self, stdscr):
        s_idx = 0
        while True:
            sound_status = "[ON]" if self.sound_enabled else "[OFF]"
            s_opts = ["Change Nick", f"Sound Notifications {sound_status}", "Clear Your Messages", "Reset Session", "Back"]
            
            stdscr.erase()
            stdscr.bkgd(' ', curses.color_pair(1))
            self.draw_small_header(stdscr)
            stdscr.addstr(6, 2, " [ SETTINGS ] ", curses.color_pair(1))
            for i, o in enumerate(s_opts):
                style = curses.A_REVERSE if i == s_idx else 0
                self.draw_element_str(stdscr, 8+i, 4, f" > {o} ", 2, style)
            stdscr.refresh()
            try:
                k = stdscr.get_wch()
            except:
                continue

            if k == curses.KEY_UP or k == 'k': 
                if s_idx > 0: s_idx -= 1
            elif k == curses.KEY_DOWN or k == 'j': 
                if s_idx < len(s_opts)-1: s_idx += 1
            elif k in [10, 13, '\n', '\r']:
                sel_opt = s_opts[s_idx]
                if sel_opt == "Change Nick":
                    new_nick = self.safe_input(stdscr, 14, 4, " New Nick: ")
                    if new_nick:
                        self.nick = new_nick
                        self.save_settings()
                    break
                elif "Sound Notifications" in sel_opt:
                    self.sound_enabled = not self.sound_enabled
                    self.save_settings()
                    if self.sound_enabled:
                        self.play_notification_sound()
                elif sel_opt == "Clear Your Messages":
                    stdscr.erase()
                    self.draw_small_header(stdscr)
                    stdscr.addstr(10, 4, " Clearing your messages from server... ", curses.A_REVERSE)
                    stdscr.refresh()
                    if self.clear_my_messages_on_server():
                        stdscr.addstr(12, 4, " Done! Your messages deleted. ", curses.A_REVERSE)
                    else:
                        stdscr.addstr(12, 4, " Error accessing database! ", curses.color_pair(1))
                    stdscr.refresh()
                    time.sleep(1.5)
                    break
                elif sel_opt == "Reset Session":
                    stdscr.erase()
                    self.draw_small_header(stdscr)
                    stdscr.addstr(10, 4, " Получение нового ID от сервера Firebase... ", curses.A_REVERSE)
                    stdscr.refresh()
                    
                    if self.authenticate_anonymously():
                        stdscr.addstr(12, 4, " Сессия успешно обновлена! ", curses.color_pair(1))
                    else:
                        stdscr.addstr(12, 4, " Ошибка сети! Сгенерирован временный ID... ", curses.color_pair(1))
                        self.session = f"{random.randint(1, 99999)}"
                    
                    self.needs_update = True
                    stdscr.refresh()
                    time.sleep(1.5)
                    break
                elif sel_opt == "Back": 
                    break
            elif k in ['b', 'B']: 
                break

    def open_credits(self, stdscr):
        while True:
            stdscr.erase()
            stdscr.bkgd(' ', curses.color_pair(1))
            self.draw_small_header(stdscr)
            stdscr.addstr(8, 4, "_____ E C H O C H A T _____", curses.A_BOLD)
            stdscr.addstr(10, 6, " Main Developer : xrl-def ", curses.color_pair(1))
            stdscr.addstr(11, 6, " Admin   :    Bogdanchick ", curses.color_pair(1))
            stdscr.addstr(13, 6, " Version    :    1.6.0(A) ", curses.color_pair(1))
            stdscr.addstr(16, 4, " Press any key to return. ", curses.A_REVERSE)
            stdscr.refresh()
            try:
                stdscr.get_wch()
            except:
                pass
            break

    def run(self, stdscr):
        curses.start_color()
        curses.use_default_colors()
        self.update_curses_colors()
        
        curses.curs_set(0)
        stdscr.keypad(True)
        
        stdscr.erase()
        stdscr.bkgd(' ', curses.color_pair(1))
        self.draw_big_logo(stdscr)
        stdscr.addstr(10, 4, " Подключение к защищенной сети Firebase Auth... ", curses.A_REVERSE)
        stdscr.refresh()
        
        if not self.authenticate_anonymously():
            stdscr.addstr(12, 4, " ОШИБКА АВТОРИЗАЦИИ! Проверь Web API Key или сеть. ", curses.color_pair(1))
            stdscr.refresh()
            time.sleep(3)
            return

        threading.Thread(target=self.groups_observer, daemon=True).start()

        main_sel = 0
        main_opts = ["Chat", "Groups", "Friends", "Themes", "Settings", "Credits", "Exit"]
        
        while self.running:
            stdscr.erase()
            stdscr.bkgd(' ', curses.color_pair(1))
            self.draw_big_logo(stdscr) 
            
            status_line = f" session : {self.session} (Auth OK) | nick : {self.nick}"
            self.draw_element_str(stdscr, 10, 4, status_line, 3)

            for i, o in enumerate(main_opts):
                style = curses.A_REVERSE | curses.A_BOLD if i == main_sel else 0
                self.draw_element_str(stdscr, 11 + i, 8, f" [ {o} ] ", 2, style)
            stdscr.refresh()
            try:
                k = stdscr.get_wch()
            except:
                continue

            if (k == curses.KEY_UP or k == 'k') and main_sel > 0: 
                main_sel -= 1
            elif (k == curses.KEY_DOWN or k == 'j') and main_sel < len(main_opts)-1: 
                main_sel += 1
            elif k in [10, 13, '\n', '\r']:
                if main_sel == 0: self.open_chat(stdscr, "messages/chat")
                elif main_sel == 1: self.open_groups(stdscr)
                elif main_sel == 2: self.open_friends_menu(stdscr)
                elif main_sel == 3: self.open_themes_menu(stdscr)
                elif main_sel == 4: self.open_settings(stdscr)
                elif main_sel == 5: self.open_credits(stdscr)
                elif main_sel == 6: self.running = False

if __name__ == "__main__":
    curses.wrapper(XRLChat().run)
