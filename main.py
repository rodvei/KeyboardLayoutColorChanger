import ctypes
import threading
import time
import json
import os
import sys
import tkinter as tk
from tkinter import colorchooser, Toplevel, Scrollbar, Canvas, Frame, Label, Button
from functools import partial
import pystray
from PIL import Image, ImageTk
from PIL.Image import Resampling
import logging
import win32con
import copy

# Windows APIs
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# Constants
LOCALE_SNATIVELANGNAME = 0x00000004
LOCALE_SISO3166CTRYNAME = 0x0000005A
DATA_DIR = os.path.join(os.path.expanduser('~'), '.keyboard_layout_colors')
os.makedirs(DATA_DIR, exist_ok=True)
CONFIG_FILE = os.path.join(DATA_DIR, 'layout_colors.json')
DEFAULT_COLORS = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']

ICONS_PATH = 'icons'
if hasattr(sys, '_MEIPASS'):
    ICONS_PATH = os.path.join(sys._MEIPASS, 'icons')
LOGO_PATH = os.path.join(ICONS_PATH, 'logo')
FLAGS_PATH = os.path.join(ICONS_PATH, 'flags')

LOGLEVEL = logging.ERROR
logging.basicConfig(filename=os.path.join(DATA_DIR, 'app.log'), level=LOGLEVEL, format='%(asctime)s - %(levelname)s - %(message)s')


class ConfigManager:
    def __init__(self):
        self.config = {}
        self.layout_names = {}
        self.load()

    def load(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                self.config = json.load(f)
        layouts = self._get_installed_layouts()
        logging.info(f"Installed keyboard layouts LANGIDs: {layouts}")
        for lang_id in layouts:
            str_id = str(lang_id)
            if str_id not in self.config:
                self._set_default(lang_id)
            self.layout_names[str_id] = self._get_language_name(lang_id)

    def save(self):
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f)

    def get_color(self, state_id):
        return self.config.get(str(state_id), {}).get('color')

    def set_color(self, state_id, color):
        str_id = str(state_id)
        if str_id not in self.config:
            self._set_default(state_id)
        self.config[str_id]['color'] = color
        self.save()

    def get_icon(self, state_id):
        return self.config.get(str(state_id), {}).get('icon')

    def set_icon(self, state_id, icon):
        str_id = str(state_id)
        if str_id not in self.config:
            self._set_default(state_id)
        self.config[str_id]['icon'] = icon
        self.save()

    def update_config(self, new_config):
        self.config = new_config
        self.save()

    def _set_default(self, state_id):
        str_id = str(state_id)
        idx = len(self.config) % len(DEFAULT_COLORS)
        self.config[str_id] = {'color': DEFAULT_COLORS[idx], 'icon': self._get_country_code(state_id)}

    def _get_installed_layouts(self):
        count = user32.GetKeyboardLayoutList(0, None)
        logging.info(f"Total keyboard layouts count: {count}")
        if count == 0:
            return set()
        layouts = (ctypes.c_void_p * count)()
        actual_count = user32.GetKeyboardLayoutList(count, layouts)
        logging.info(f"Raw HKLs: {[hex(int(hkl)) for hkl in layouts[:actual_count]]}")
        return set(int(hkl) & 0xFFFF for hkl in layouts[:actual_count])

    def _get_language_name(self, lang_id):
        buffer = ctypes.create_unicode_buffer(100)
        kernel32.GetLocaleInfoW(lang_id, LOCALE_SNATIVELANGNAME, buffer, len(buffer))
        return buffer.value

    def _get_country_code(self, lang_id):
        buffer = ctypes.create_unicode_buffer(10)
        if kernel32.GetLocaleInfoW(lang_id, LOCALE_SISO3166CTRYNAME, buffer, len(buffer)):
            return buffer.value.upper()
        return None


class BackgroundSetter:
    def __init__(self):
        self.image_dir = DATA_DIR
        self.screen_size = self._get_screen_size()
        self.original_wallpaper = self._get_current_wallpaper()

    def set_to_color(self, color, state_id):
        file_path = self._create_color_image(color, state_id)
        self._set_wallpaper(file_path)

    def restore_original(self):
        if self.original_wallpaper:
            self._set_wallpaper(self.original_wallpaper)

    def _create_color_image(self, color, state_id):
        name = f"{state_id}_{color.replace('#', '')}"
        file_path = os.path.join(self.image_dir, f'{name}.png')
        if not os.path.exists(file_path):
            img = Image.new('RGB', self.screen_size, color)
            img.save(file_path)
        return file_path

    def _get_screen_size(self):
        return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)

    def _get_current_wallpaper(self):
        buffer = ctypes.create_unicode_buffer(260)
        ctypes.windll.user32.SystemParametersInfoW(win32con.SPI_GETDESKWALLPAPER, 260, buffer, 0)
        return buffer.value

    def _set_wallpaper(self, path):
        full_path = os.path.abspath(path)
        flags = win32con.SPIF_UPDATEINIFILE | win32con.SPIF_SENDCHANGE
        succeeded = False
        for attempt in range(3):
            success = ctypes.windll.user32.SystemParametersInfoW(win32con.SPI_SETDESKWALLPAPER, 0, full_path, flags)
            if success:
                logging.info(f"Wallpaper set to {full_path} succeeded on attempt {attempt + 1}")
                succeeded = True
                break
            logging.warning(f"Wallpaper set failed on attempt {attempt + 1}, retrying...")
            time.sleep(0.5)
        if not succeeded:
            logging.error(f"Failed to set wallpaper to {full_path} after 3 attempts")
        current = self._get_current_wallpaper()
        if os.path.normcase(current) != os.path.normcase(full_path):
            logging.warning(f"Wallpaper not matching after set, trying one more time")
            ctypes.windll.user32.SystemParametersInfoW(win32con.SPI_SETDESKWALLPAPER, 0, full_path, flags)


class KeyboardTrigger:
    def __init__(self):
        self.current_state = None

    def get_current_state(self):
        hwnd = user32.GetForegroundWindow()
        if hwnd == 0:
            return self.current_state  # No foreground, keep old
        thread_id = user32.GetWindowThreadProcessId(hwnd, None)
        hkl = user32.GetKeyboardLayout(thread_id)
        return hkl & 0xFFFF


class SettingsUI:
    def __init__(self, root):
        self.root = root
        self.image_refs = []  # To prevent GC
        self.flag_photos = []
        self.scroll_frame = None
        self.top = None
        self.copy_config = None
        self.layout_names = None
        self.result = None

    def show(self, config, layout_names):
        if self.top and tk.Toplevel.winfo_exists(self.top):
            self.top.lift()
            return None
        self.top = Toplevel(self.root)
        self.top.title('Settings')
        self.top.geometry("400x300")
        self.copy_config = copy.deepcopy(config)  # Deep copy
        self.layout_names = layout_names
        self.result = None

        # Use grid for main layout
        self.top.grid_columnconfigure(0, weight=1)
        self.top.grid_columnconfigure(1, weight=0)
        self.top.grid_rowconfigure(0, weight=1)
        self.top.grid_rowconfigure(1, weight=0)

        canvas = Canvas(self.top)
        scrollbar = Scrollbar(self.top, orient="vertical", command=canvas.yview)
        self.scroll_frame = Frame(canvas)

        self.scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        self._build_layout_list()

        btn_frame = Frame(self.top)
        btn_frame.grid(row=1, column=0, columnspan=2, sticky="ew")
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)
        Button(btn_frame, text="Save", command=self._save).grid(row=0, column=0, sticky="ew", padx=(5, 2))
        Button(btn_frame, text="Cancel", command=self._cancel).grid(row=0, column=1, sticky="ew", padx=(2, 5))

        self.top.wait_window(self.top)
        return self.result

    def _build_layout_list(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        self.image_refs.clear()

        if not self.layout_names:
            Label(self.scroll_frame, text="No keyboard layouts detected.").pack(pady=10)
            return

        header_font = ("Arial", 10, "bold")
        Label(self.scroll_frame, text="Name", font=header_font).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        Label(self.scroll_frame, text="Color", font=header_font).grid(row=0, column=1, padx=5, pady=5)
        Label(self.scroll_frame, text="Flag", font=header_font).grid(row=0, column=2, padx=5, pady=5)

        button_width, button_height = 80, 40
        small_font = ("Arial", 8)

        items = sorted(self.layout_names.items(), key=lambda x: x[1])
        for i, (str_id, name) in enumerate(items, start=1):
            data = self.copy_config[str_id]
            color = data['color']
            icon = data['icon']

            Label(self.scroll_frame, text=f"{name} ({int(str_id)}): ").grid(row=i, column=0, padx=5, pady=5, sticky="w")

            # Color column subframe
            color_subframe = Frame(self.scroll_frame)
            color_subframe.grid(row=i, column=1, padx=5, pady=5)
            color_frame = Frame(color_subframe, width=button_width, height=button_height, bg=color)
            color_frame.grid(row=0, column=0)
            color_frame.pack_propagate(False)
            Button(color_frame, bg=color, relief="raised",
                   command=partial(self._change_color, str_id)).place(relwidth=1.0, relheight=1.0)
            Label(color_subframe, text=color, font=small_font).grid(row=1, column=0)

            # Flag column subframe
            flag_subframe = Frame(self.scroll_frame)
            flag_subframe.grid(row=i, column=2, padx=5, pady=5)
            try:
                flag_path = os.path.join(FLAGS_PATH, f"{icon}.png")
                img = Image.open(flag_path)
                img.thumbnail((button_width, button_height), Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.image_refs.append(photo)
                Button(flag_subframe, image=photo, width=button_width, height=button_height, relief="raised",
                       command=partial(self._change_icon, str_id)).grid(row=0, column=0)
            except Exception:
                Button(flag_subframe, text="No Icon", width=button_width, height=button_height, relief="raised",
                       command=partial(self._change_icon, str_id)).grid(row=0, column=0)
            Label(flag_subframe, text=icon, font=small_font).grid(row=1, column=0)

    def _change_color(self, str_id):
        new_color = colorchooser.askcolor()[1]
        if new_color:
            self.copy_config[str_id]['color'] = new_color
            self._build_layout_list()

    def _change_icon(self, str_id):
        dialog = Toplevel(self.top)
        dialog.title('Change Icon Emoji')
        dialog.geometry("700x400")

        main_frame = Frame(dialog)
        main_frame.pack(fill="both", expand=True)

        canvas_frame = Frame(main_frame)
        canvas_frame.pack(fill="both", expand=True)

        canvas = Canvas(canvas_frame, borderwidth=0)
        scrollbar = Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        scroll_frame = Frame(canvas)
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        photos = []
        flag_files = sorted([f for f in os.listdir(FLAGS_PATH) if f.lower().endswith('.png')])
        num_columns = 10
        for i, filename in enumerate(flag_files):
            flag_path = os.path.join(FLAGS_PATH, filename)
            code = filename[:-4].upper()
            try:
                img = Image.open(flag_path)
                img.thumbnail((48, 48), Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                photos.append(photo)
                btn = Button(scroll_frame, image=photo,
                             command=partial(self._select_flag, code, str_id, dialog))
                btn.grid(row=i // num_columns, column=i % num_columns, padx=5, pady=5)
            except Exception as e:
                logging.error(f"Failed loading {flag_path}: {e}")
        self.flag_photos = photos

    def _select_flag(self, code, str_id, dialog):
        self.copy_config[str_id]['icon'] = code
        dialog.destroy()
        self._build_layout_list()

    def _save(self):
        self.result = self.copy_config
        self.top.destroy()

    def _cancel(self):
        self.result = None
        self.top.destroy()


class App:
    def __init__(self):
        self.config = ConfigManager()
        self.bg_setter = BackgroundSetter()
        self.trigger = KeyboardTrigger()
        self.monitoring = True
        self.root = tk.Tk()
        self.root.withdraw()
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        self.tray_thread = threading.Thread(target=self._create_tray_icon, daemon=True)
        self.tray_thread.start()
        self._monitor_interval = 0.1
        self.icon = None
        self.settings_ui = SettingsUI(self.root)

    def _monitor_loop(self):
        self._check_and_update()
        self._update_tray_icon(country_code=None, grey=False)
        while True:
            if self.monitoring:
                self._check_and_update()
            time.sleep(self._monitor_interval)

    def _update_tray_icon(self, country_code=None, grey=False):
        if country_code:
            path = os.path.join(FLAGS_PATH, f"{country_code}.png")
            image = Image.open(path).resize((32, 32), Image.LANCZOS)
            if grey:
                image = image.convert('L').convert('RGB')
        else:
            if grey:    
                path = os.path.join(LOGO_PATH, 'app_grey.png')
            else:
                path = os.path.join(LOGO_PATH, 'app.png')
            image = Image.open(path).resize((32, 32), Image.LANCZOS)

        if self.icon:
            self.icon.icon = image

    def _check_and_update(self, force=False):
        state = self.trigger.get_current_state()
        if state != self.trigger.current_state and state is not None or force:
            logging.info(f"Keyboard layout changed to {state}")
            self.trigger.current_state = state
            self._update_layout(state)

    def _update_layout(self, state):
        color = self.config.get_color(state)
        if color:
            self.bg_setter.set_to_color(color, state)
        country_code = self.config.get_icon(state)
        self._update_tray_icon(country_code, grey=False)

    def toggle_monitoring(self):
        self.monitoring = not self.monitoring
        if self.monitoring:
            self._check_and_update()
            self._monitor_interval = 0.1
            self._update_tray_icon(country_code=None, grey=False)
        else:
            self.bg_setter.restore_original()
            self._monitor_interval = 1
            self._update_tray_icon(country_code=None, grey=True)

    def show_settings(self):
        new_config = self.settings_ui.show(self.config.config, self.config.layout_names)
        if new_config is not None:
            self.config.update_config(new_config)
            self._check_and_update(force=True)

    def quit(self):
        self.icon.stop()
        self.root.quit()
        os._exit(0)

    def _create_tray_icon(self):
        try:
            image = Image.open(os.path.join(LOGO_PATH, 'app.png'))
        except Exception as e:
            logging.error(f"Failed to load tray icon: {str(e)}")
            image = Image.new('RGB', (16, 16), color=(0, 0, 0))
        self.icon = pystray.Icon('Keyboard Color', image, 'Keyboard Layout Color')
        self.icon.menu = pystray.Menu(
            pystray.MenuItem('Toggle On/Off', self.toggle_monitoring, checked=lambda item: self.monitoring),
            pystray.MenuItem('Settings', self.show_settings),
            pystray.MenuItem('Quit', self.quit)
        )
        self.icon.run()


if __name__ == '__main__':
    app = App()
    app.root.mainloop()