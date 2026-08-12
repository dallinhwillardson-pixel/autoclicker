import sys
import time
import threading
import platform
import tkinter as tk
from tkinter import ttk

# --- OS Detection ---
IS_WINDOWS = platform.system() == "Windows"
IS_MAC = platform.system() == "Darwin"

# --- Import & Define OS-Specific Drivers ---
if IS_WINDOWS:
    import ctypes
    
    def os_click_mouse(button='left'):
        if button == 'left':
            ctypes.windll.user32.mouse_event(0x0002, 0, 0, 0, 0)
            ctypes.windll.user32.mouse_event(0x0004, 0, 0, 0, 0)
        elif button == 'right':
            ctypes.windll.user32.mouse_event(0x0008, 0, 0, 0, 0)
            ctypes.windll.user32.mouse_event(0x0010, 0, 0, 0, 0)
        elif button == 'middle':
            ctypes.windll.user32.mouse_event(0x0020, 0, 0, 0, 0)
            ctypes.windll.user32.mouse_event(0x0040, 0, 0, 0, 0)

    def os_press_key(vk_code):
        ctypes.windll.user32.keybd_event(vk_code, 0, 0, 0)
        ctypes.windll.user32.keybd_event(vk_code, 0, 0x0002, 0)

    KEY_CODES = {
        'F1': 0x70, 'F2': 0x71, 'F3': 0x72, 'F4': 0x73, 'F5': 0x74, 'F6': 0x75,
        'F7': 0x76, 'F8': 0x77, 'F9': 0x78, 'F10': 0x79, 'F11': 0x7A, 'F12': 0x7B,
        'Space': 0x20, 'Enter': 0x0D, 'Tab': 0x09, 'Shift': 0x10, 'Ctrl': 0x11,
        'A': 0x41, 'B': 0x42, 'C': 0x43, 'D': 0x44, 'E': 0x45, 'Q': 0x51, 'X': 0x58, 'Z': 0x5A
    }

else:  # macOS / Linux
    from pynput.mouse import Button, Controller as MouseController
    from pynput.keyboard import Key, Controller as KeyboardController, Listener as KeyboardListener

    mac_mouse = MouseController()
    mac_keyboard = KeyboardController()

    def os_click_mouse(button='left'):
        btn = Button.left if button == "left" else (Button.right if button == "right" else Button.middle)
        mac_mouse.click(btn)

    def os_press_key(key_name):
        special_map = {
            'Space': Key.space, 'Enter': Key.enter, 'Tab': Key.tab,
            'Shift': Key.shift, 'Ctrl': Key.ctrl,
            'F1': Key.f1, 'F2': Key.f2, 'F3': Key.f3, 'F4': Key.f4, 'F5': Key.f5, 'F6': Key.f6,
            'F7': Key.f7, 'F8': Key.f8, 'F9': Key.f9, 'F10': Key.f10, 'F11': Key.f11, 'F12': Key.f12
        }
        k = special_map.get(key_name, key_name.lower())
        mac_keyboard.press(k)
        mac_keyboard.release(k)

    KEY_CODES = {
        'F1': 'f1', 'F2': 'f2', 'F3': 'f3', 'F4': 'f4', 'F5': 'f5', 'F6': 'f6',
        'F7': 'f7', 'F8': 'f8', 'F9': 'f9', 'F10': 'f10', 'F11': 'f11', 'F12': 'f12',
        'Space': 'space', 'Enter': 'enter', 'Tab': 'tab', 'Shift': 'shift', 'Ctrl': 'ctrl',
        'A': 'a', 'B': 'b', 'C': 'c', 'D': 'd', 'E': 'e', 'Q': 'q', 'X': 'x', 'Z': 'z'
    }


class AutoClickerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Universal AutoClicker")
        self.root.geometry("380x540")
        self.root.resizable(False, False)
        self.root.configure(bg="#F8F9FA")
        self.root.attributes("-topmost", True)

        self.clicking = False
        self.current_hotkey_str = "F6"
        self.fade_timer = None

        # Fonts
        font_family = "Segoe UI" if IS_WINDOWS else "Helvetica Neue"
        self.FONT_TITLE = (font_family, 16, "bold")
        self.FONT_LABEL = (font_family, 9, "bold")
        self.FONT_BODY = (font_family, 10)
        self.FONT_STATUS = (font_family, 10, "bold")
        self.FONT_SAVED = (font_family, 9, "bold")

        # --- Header ---
        header_frame = tk.Frame(root, bg="#F8F9FA")
        header_frame.pack(fill="x", padx=25, pady=(20, 10))

        os_title = "Windows Version" if IS_WINDOWS else "macOS Version"
        tk.Label(header_frame, text=f"AutoClicker ({os_title})", font=self.FONT_TITLE, bg="#F8F9FA", fg="#111827").pack(anchor="w")
        tk.Label(header_frame, text="Automate mouse clicks or key presses", font=(font_family, 9), bg="#F8F9FA", fg="#6B7280").pack(anchor="w")

        # --- Status Badge ---
        self.status_frame = tk.Frame(root, bg="#FEE2E2", highlightbackground="#FCA5A5", highlightthickness=1)
        self.status_frame.pack(fill="x", padx=25, pady=(5, 15))

        self.status_label = tk.Label(self.status_frame, text="● STOPPED", font=self.FONT_STATUS, fg="#DC2626", bg="#FEE2E2", pady=6)
        self.status_label.pack()

        # --- Settings Board ---
        container = tk.Frame(root, bg="#FFFFFF", highlightbackground="#E5E7EB", highlightthickness=1)
        container.pack(fill="both", expand=True, padx=25, pady=(0, 20))

        # 1. Action Type
        tk.Label(container, text="Action Type", font=self.FONT_LABEL, bg="#FFFFFF", fg="#374151").pack(anchor="w", padx=15, pady=(15, 4))
        self.action_mode = tk.StringVar(value="Mouse Click")
        self.mode_dropdown = ttk.Combobox(container, textvariable=self.action_mode, values=["Mouse Click", "Key Press"], state="readonly")
        self.mode_dropdown.pack(fill="x", padx=15, pady=(0, 10))
        self.mode_dropdown.bind("<<ComboboxSelected>>", self.toggle_mode_ui)

        # 2. Target Dynamic Selection
        self.target_label = tk.Label(container, text="Target Mouse Button", font=self.FONT_LABEL, bg="#FFFFFF", fg="#374151")
        self.target_label.pack(anchor="w", padx=15, pady=(0, 4))

        self.mouse_var = tk.StringVar(value="left")
        self.mouse_dropdown = ttk.Combobox(container, textvariable=self.mouse_var, values=["left", "right", "middle"], state="readonly")
        self.mouse_dropdown.pack(fill="x", padx=15, pady=(0, 10))

        self.target_key_var = tk.StringVar(value="Space")
        self.target_key_dropdown = ttk.Combobox(container, textvariable=self.target_key_var, values=list(KEY_CODES.keys()), state="readonly")

        # 3. Interval Entry
        tk.Label(container, text="Interval (seconds)", font=self.FONT_LABEL, bg="#FFFFFF", fg="#374151").pack(anchor="w", padx=15, pady=(0, 4))
        self.interval_entry = tk.Entry(container, font=self.FONT_BODY, bg="#F9FAFB", fg="#111827", relief="solid", bd=1, justify="center")
        self.interval_entry.insert(0, "0.1")
        self.interval_entry.pack(fill="x", padx=15, ipady=4, pady=(0, 10))

        # 4. Toggle Hotkey Dropdown
        tk.Label(container, text="Toggle Hotkey (Start/Stop)", font=self.FONT_LABEL, bg="#FFFFFF", fg="#374151").pack(anchor="w", padx=15, pady=(0, 4))
        self.hotkey_var = tk.StringVar(value="F6")
        self.hotkey_dropdown = ttk.Combobox(container, textvariable=self.hotkey_var, values=list(KEY_CODES.keys()), state="readonly")
        self.hotkey_dropdown.pack(fill="x", padx=15, pady=(0, 12))

        # 5. Apply Button
        apply_btn = tk.Button(container, text="Apply Settings", font=(font_family, 10, "bold"), bg="#2563EB", fg="white", relief="flat", cursor="hand2", command=self.apply_settings)
        apply_btn.pack(fill="x", padx=15, ipady=6, pady=(0, 4))

        # 6. Inline "Saved" Confirmation Label
        self.saved_label = tk.Label(container, text="", font=self.FONT_SAVED, bg="#FFFFFF", fg="#16A34A")
        self.saved_label.pack(pady=(0, 8))

        # Start background listener depending on OS
        if IS_WINDOWS:
            threading.Thread(target=self.win_key_listener_loop, daemon=True).start()
        else:
            self.mac_listener = KeyboardListener(on_press=self.mac_on_key_press)
            self.mac_listener.start()

    def toggle_mode_ui(self, event=None):
        if self.action_mode.get() == "Mouse Click":
            self.target_key_dropdown.pack_forget()
            self.target_label.config(text="Target Mouse Button")
            self.mouse_dropdown.pack(fill="x", padx=15, pady=(0, 10), before=self.interval_entry.master.children['!label3'])
        else:
            self.mouse_dropdown.pack_forget()
            self.target_label.config(text="Target Key to Press")
            self.target_key_dropdown.pack(fill="x", padx=15, pady=(0, 10), before=self.interval_entry.master.children['!label3'])

    def apply_settings(self):
        """Saves settings and shows inline status text instead of a popup."""
        self.current_hotkey_str = self.hotkey_var.get()
        
        # Display inline text indicator
        self.saved_label.config(text="✓ Settings Saved!")
        
        # Cancel any previous timer if button is clicked repeatedly
        if self.fade_timer:
            self.root.after_cancel(self.fade_timer)
            
        # Hide the text automatically after 2.5 seconds
        self.fade_timer = self.root.after(2500, lambda: self.saved_label.config(text=""))

    # --- Windows Hotkey Loop ---
    def win_key_listener_loop(self):
        last_state = False
        while True:
            vk = KEY_CODES.get(self.current_hotkey_str, 0x75)
            key_down = ctypes.windll.user32.GetAsyncKeyState(vk) & 0x8000
            if key_down and not last_state:
                self.toggle_clicking()
            last_state = key_down
            time.sleep(0.05)

    # --- Mac Hotkey Callback ---
    def mac_on_key_press(self, key):
        try:
            k = key.char.upper() if hasattr(key, 'char') and key.char else key.name.upper()
        except AttributeError:
            k = str(key).replace("Key.", "").upper()

        if k == self.current_hotkey_str.upper():
            self.toggle_clicking()

    def toggle_clicking(self):
        self.clicking = not self.clicking
        if self.clicking:
            self.status_frame.config(bg="#DCFCE7", highlightbackground="#86EFAC")
            self.status_label.config(text="● RUNNING", fg="#166534", bg="#DCFCE7")
            threading.Thread(target=self.action_loop, daemon=True).start()
        else:
            self.status_frame.config(bg="#FEE2E2", highlightbackground="#FCA5A5")
            self.status_label.config(text="● STOPPED", fg="#DC2626", bg="#FEE2E2")

    def action_loop(self):
        while self.clicking:
            try:
                delay = float(self.interval_entry.get())
            except ValueError:
                delay = 0.1

            if self.action_mode.get() == "Mouse Click":
                os_click_mouse(self.mouse_var.get())
            else:
                os_press_key(self.target_key_var.get())

            time.sleep(max(delay, 0.001))

if __name__ == "__main__":
    root = tk.Tk()
    app = AutoClickerApp(root)
    root.mainloop()