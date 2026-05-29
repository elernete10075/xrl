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

from firebase_admin import credentials, db
# ИСПРАВЛЕНО: Добавлен пропущенный импорт Fernet
from cryptography.fernet import Fernet

try:
    locale.setlocale(locale.LC_ALL, '')
except Exception:
    pass

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
        self.running = True
        self.cache_file = "xrl_cache.txt"
        self.config_file = "xrl_config.txt"
        self.themes_dir = "themes"
        self.themes_config_file = "themes_config.txt"
        
        self.messages_history = []
        self.groups_raw = {} 
        self.current_path = "messages/chat"
        self.needs_update = True
        self.listener_obj = None
        self.in_chat = False
        self.data_lock = threading.Lock()

        # Параметры интерфейса по умолчанию
        self.header_text = " - E C H O - "
        self.separator_char = "="
        self.msg_prefix = " {name} : "
        self.input_prefix = " > "

        self.default_logo = [
            "░▒▓████████▓▒ ░▒▓██████▓▒░░▒▓█▓▒░░▒▓█▓▒░░▒▓██████▓▒░  ",
            "░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ ",
            "░▒▓█▓▒░      ░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ ",
            "░▒▓██████▓▒░ ░▒▓█▓▒░      ░▒▓████████▓▒░▒▓█▓▒░░▒▓█▓▒░ ",
            "░▒▓█▓▒░      ░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ ",
            "░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ ",
            "░▒▓████████▓▒ ░▒▓██████▓▒░░▒▓█▓▒░░▒▓█▓▒░░▒▓██████▓▒░  ",
            "──────────────────────────────────────────────────────"
        ]
        self.current_logo = list(self.default_logo)

        # Цвета по умолчанию из твоей структуры JSON
        self.theme_colors = {
            "text_background": 196,
            "text_primary": 255,
            "text_accent": 255,
            "gradient": [255, 255, 255, 255, 255, 255, 255, 255]
        }

        if not os.path.exists(self.cache_file): 
            open(self.cache_file, 'w', encoding="utf-8").close()
        
        self.load_settings()
        self.init_themes_system()
        self.load_msg_cache()

    def encrypt(self, text): 
        return cipher.encrypt(text.encode('utf-8')).decode('utf-8')
        
    def decrypt(self, token):
        try: 
            return cipher.decrypt(token.encode('utf-8')).decode('utf-8')
        except Exception: 
            return None

    def load_settings(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    saved_nick = f.read().strip()
                    if saved_nick:
                        self.nick = saved_nick
            except Exception as e:
                logging.error(f"Ошибка загрузки настроек: {e}")

    def save_settings(self):
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                f.write(self.nick)
        except Exception as e:
            logging.error(f"Ошибка сохранения настроек: {e}")

    def write_theme_to_file(self, path):
        theme_structure = {
            "colors": {
                "text_background": 16,
                "text_primary": 255,
                "text_accent": 255,
                "gradient": [196, 160, 124, 88, 124, 160, 194, 160]
            },
            "ui": {
                "header_text": " - E C H O - ",
                "separator_char": "=",
                "msg_prefix": " {name} : ",
                "input_prefix": " > ",
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

            # Обработка возможных ручных опечаток в структуре JSON
            fixed_content = re.sub(r',?\s*gradient\s*"\s*\w+\s*"', '', raw_content)
            data = json.loads(fixed_content)
            
            if "colors" in data:
                colors = data["colors"]
                if "text_background" in colors: self.theme_colors["text_background"] = int(colors["text_background"])
                if "text_primary" in colors: self.theme_colors["text_primary"] = int(colors["text_primary"])
                if "text_accent" in colors: self.theme_colors["text_accent"] = int(colors["text_accent"])
                if "gradient" in colors: self.theme_colors["gradient"] = colors["gradient"]

            if "ui" in data:
                ui = data["ui"]
                if "header_text" in ui: self.header_text = ui["header_text"]
                if "separator_char" in ui: self.separator_char = ui["separator_char"]
                if "msg_prefix" in ui: self.msg_prefix = ui["msg_prefix"]
                if "input_prefix" in ui: self.input_prefix = ui["input_prefix"]
                if "logo" in ui: self.current_logo = ui["logo"]

            self.update_curses_colors()
            return True
        except Exception as e:
            logging.error(f"Ошибка загрузки JSON темы {theme_name}: {e}")
            return False

    def update_curses_colors(self):
        try:
            bg_id = self.theme_colors["text_background"]
            primary_id = self.theme_colors["text_primary"]
            accent_id = self.theme_colors["text_accent"]

            curses.init_pair(1, primary_id, bg_id)
            curses.init_pair(2, accent_id, bg_id)
            curses.init_pair(3, accent_id, bg_id)
            curses.init_pair(4, primary_id, bg_id)
        except Exception as e:
            logging.error(f"Ошибка применения цветов curses: {e}")

    def draw_element_str(self, stdscr, y, x, text, color_pair_id, extra_attr=0):
        if not text: return
        try:
            stdscr.addstr(y, x, text, curses.color_pair(color_pair_id) | extra_attr)
        except:
            pass

    def draw_big_logo(self, stdscr):
        for i, line in enumerate(self.current_logo):
            self.draw_element_str(stdscr, i + 2, 2, line, 4, curses.A_BOLD)

    def draw_small_header(self, stdscr):
        self.draw_element_str(stdscr, 1, 2, self.header_text, 4, curses.A_BOLD)
        sep_line = " " + self.separator_char * 56 + " "
        stdscr.addstr(2, 2, sep_line, curses.color_pair(3)) 
        
        room = self.current_path.split('/')[-1]
        status_line = f" session : {self.session} | room: {room} | nick : {self.nick}"
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
            
            bg_id = self.theme_colors["text_background"]
            start_y = 7
            cols_count = 12
            
            for c_num in range(256):
                row = c_num // cols_count
                col = c_num % cols_count
                
                pair_id = 20 + (c_num % 230)
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
                for k in items:
                    val = items[k]
                    raw = val.get('payload') if isinstance(val, dict) else val
                    dec = self.decrypt(raw)
                    if dec and "send-message" in dec: 
                        self.process_msg(dec, save=True)
                self.needs_update = True

        try: 
            self.listener_obj = db.reference(path).listen(handler)
        except Exception as e: 
            logging.error(f"Ошибка подписки на сообщения ({path}): {e}")

    def process_msg(self, dec, save=False):
        match = re.search(r"\(.*?\)\s\((.*?)\)\s\((.*?)\)\s>(.*)<", dec)
        if match:
            ses, name, txt = match.groups()
            prefix = self.msg_prefix.format(name=name)
            m = f"| {prefix}{txt}"
            if m not in self.messages_history: 
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
                    except Exception as e:
                        logging.error(f"Ошибка отправки сообщения: {e}")
                    user_input = ""
                    
            elif key in [8, 127, 263, '\b', '\x7f', curses.KEY_BACKSPACE, 'KEY_BACKSPACE']: 
                user_input = user_input[:-1]
                
            elif isinstance(key, str): 
                user_input += key

        self.in_chat = False
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
        s_opts = ["Change Nick", "Reset Session", "Back"]
        s_idx = 0
        while True:
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
                    new_nick = self.safe_input(stdscr, 12, 4, " New Nick: ")
                    if new_nick:
                        self.nick = new_nick
                        self.save_settings()
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
            stdscr.addstr(8, 4, "--- XRL-CHAT PROJECT ---", curses.A_BOLD)
            stdscr.addstr(10, 6, "Main Developer: xrl-def", curses.color_pair(1))
            stdscr.addstr(11, 6, "Admin   :    Bogdanchick", curses.color_pair(1))
            stdscr.addstr(13, 6, "Version         : 1.2.0 (JSON-Themes)", curses.color_pair(1))
            stdscr.addstr(16, 4, "Press any key to return", curses.A_REVERSE)
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
        main_opts = ["Chat", "Groups", "Themes", "Settings", "Credits", "Exit"]
        
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
                elif main_sel == 2: self.open_themes_menu(stdscr)
                elif main_sel == 3: self.open_settings(stdscr)
                elif main_sel == 4: self.open_credits(stdscr)
                elif main_sel == 5: self.running = False

if __name__ == "__main__":
    curses.wrapper(XRLChat().run)
