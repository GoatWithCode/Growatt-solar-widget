import tkinter as tk
from playwright.sync_api import sync_playwright
from threading import Thread, Event
import time
import os
import sys
from datetime import datetime
import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw
import math
import base64

# Chromium-Pfad
base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
chrome_path = os.path.join(base_path, "chromium-1169", "chrome-win", "chrome.exe")

LOGIN_URL = "https://server-us.growatt.com/login"
stop_event = Event()
auto_thread = None
tray_icon = None

# --- Konfiguration laden ---
def load_config():
    config = {"intervall": 60, "username": "", "password": ""}
    try:
        with open("config.txt", "r") as f:
            for line in f:
                if "=" in line:
                    key, val = line.strip().split("=", 1)
                    if key in config:
                        config[key] = val.strip()
        config["intervall"] = int(config["intervall"])
        if config["password"]:
            config["password"] = base64.b64decode(config["password"]).decode("utf-8")
    except Exception as e:
        with open("error.log", "a") as log:
            log.write(f"{datetime.now()} Fehler beim Laden der config.txt: {e}\n")
    return config

config = load_config()

def get_solar_data():
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                executable_path=chrome_path,
                args=[
                    "--disable-gpu", "--disable-extensions", "--disable-infobars",
                    "--no-sandbox", "--disable-dev-shm-usage",
                    "--window-size=1920,1080", "--hide-scrollbars"
                ]
            )
            page = browser.new_page()
            page.goto(LOGIN_URL)
            page.fill("#val_loginAccount", config["username"])
            page.fill("#val_loginPwd", config["password"])
            page.click(".hasColorBtn.loginB")
            page.wait_for_selector("div.abs", timeout=15000)

            pv_power = page.text_content('div.abs:has(span.text:has-text("PV Power")) span.val') or "---"
            pv_today = page.text_content('div.half > span.val.val_epvOne') or "---"
            import_power = page.text_content('div.abs:has(span.text:has-text("Import")) span.val') or "---"
            consumption_power = page.text_content('div.abs:has(span.text:has-text("Consumption Power")) span.val') or "---"

            browser.close()
            return pv_power, pv_today, import_power, consumption_power
    except Exception as e:
        with open("error.log", "a") as log:
            log.write(f"{datetime.now()} Fehler beim Abrufen: {e}\n")
        return "---", "---", "---", "---"

def show_data():
    pv, pv_t, imp, cons = get_solar_data()
    pv_var.set(pv)
    pv_today_var.set(f"{pv_t} kW")
    imp_var.set(imp)
    cons_var.set(f"{cons} W")
    timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    last_update_var.set(f"Stand: {timestamp}")

def start_auto_update():
    global auto_thread
    stop_event.clear()
    def loop():
        global config
        while not stop_event.is_set():
            config.update(load_config())
            show_data()
            seconds = config.get("intervall", 60)
            for _ in range(seconds):
                if stop_event.is_set():
                    break
                time.sleep(1)
    auto_thread = Thread(target=loop, daemon=True)
    auto_thread.start()

def hide_to_tray(icon=None, item=None):
    root.withdraw()

def on_exit(icon=None, item=None):
    stop_event.set()
    if tray_icon:
        tray_icon.stop()
    root.quit()

def create_solar_icon():
    size = 64
    img = Image.new("RGBA", (size, size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((16, 16, 48, 48), fill="gold", outline="orange", width=3)
    return img

def create_tray_icon():
    global tray_icon
    icon_img = create_solar_icon()
    tray_icon = pystray.Icon("SolarWidget", icon_img, "Solar Werte", menu=pystray.Menu(
        item("Anzeigen", lambda: root.after(0, root.deiconify)),
        item("Verstecken", lambda: root.after(0, hide_to_tray)),
        item("Beenden", lambda: root.after(0, on_exit))
    ))
    tray_icon.run_detached()

class PulsingSun(tk.Canvas):
    def __init__(self, master, size=40, **kwargs):
        super().__init__(master, width=size, height=size, bg="#202020", highlightthickness=0, **kwargs)
        self.size = size
        self.center = size // 2
        self.base_radius = 12
        self.pulse_range = 4
        self.pulse_speed = 0.07
        self.angle = 0
        self.animate()

    def animate(self):
        self.delete("all")
        radius = self.base_radius + self.pulse_range * math.sin(self.angle)
        self.angle += self.pulse_speed
        self.create_oval(
            self.center - radius, self.center - radius,
            self.center + radius, self.center + radius,
            fill="gold", outline="orange", width=2
        )
        for angle_deg in range(0, 360, 45):
            angle_rad = math.radians(angle_deg)
            x1 = self.center + radius * 1.5 * math.cos(angle_rad)
            y1 = self.center + radius * 1.5 * math.sin(angle_rad)
            x2 = self.center + radius * 2.2 * math.cos(angle_rad)
            y2 = self.center + radius * 2.2 * math.sin(angle_rad)
            self.create_line(x1, y1, x2, y2, fill="orange", width=2)
        self.after(50, self.animate)

def round_button_style(btn, bg_color):
    btn.configure(
        bg=bg_color,
        fg="white",
        activebackground=bg_color,
        relief="flat",
        bd=0,
        highlightthickness=0,
        font=("Segoe UI", 10, "bold"),
        cursor="hand2"
    )
    btn.bind("<Enter>", lambda e: btn.config(bg="#66bb66" if bg_color == "green" else "#cc6666"))
    btn.bind("<Leave>", lambda e: btn.config(bg=bg_color))

# GUI erstellen
root = tk.Tk()
root.overrideredirect(True)
root.attributes("-topmost", True)
root.attributes("-transparentcolor", "black")
root.configure(bg="black")
root.protocol("WM_DELETE_WINDOW", hide_to_tray)

screen_width = root.winfo_screenwidth()
widget_width = 320
widget_height = 240
root.geometry(f"{widget_width}x{widget_height}+{screen_width - widget_width - 20}+40")

def start_move(event): root.x, root.y = event.x, event.y
def stop_move(event): root.x = root.y = None
def do_move(event):
    x = root.winfo_x() + (event.x - root.x)
    y = root.winfo_y() + (event.y - root.y)
    root.geometry(f"+{x}+{y}")

root.bind("<ButtonPress-1>", start_move)
root.bind("<B1-Motion>", do_move)
root.bind("<ButtonRelease-1>", stop_move)

canvas = tk.Canvas(root, bg="black", highlightthickness=0)
canvas.pack(fill="both", expand=True)
canvas.create_rectangle(10, 10, widget_width - 10, widget_height - 10, fill="#202020", outline="")

frame = tk.Frame(canvas, bg="#202020")
canvas.create_window((widget_width // 2, widget_height // 2 - 10), window=frame)

sun_icon = PulsingSun(canvas, size=40)
sun_icon.place(x=widget_width - 50, y=10)

label_style_white = {"font": ("Segoe UI", 11, "bold"), "fg": "white", "bg": "#202020"}
label_style_yellow = {"font": ("Segoe UI", 11, "bold"), "fg": "yellow", "bg": "#202020"}

tk.Label(frame, text="☀ PV Power:", **label_style_yellow).grid(row=0, column=0, sticky="w", padx=5, pady=3)
tk.Label(frame, text="📈 Today:", **label_style_yellow).grid(row=1, column=0, sticky="w", padx=5, pady=3)
tk.Label(frame, text="💵 Import:", **label_style_white).grid(row=2, column=0, sticky="w", padx=5, pady=3)
tk.Label(frame, text="🏠 Verbrauch:", **label_style_white).grid(row=3, column=0, sticky="w", padx=5, pady=3)

pv_var = tk.StringVar(value="---")
pv_today_var = tk.StringVar(value="---")
imp_var = tk.StringVar(value="---")
cons_var = tk.StringVar(value="---")
last_update_var = tk.StringVar(value="Stand: --")

tk.Label(frame, textvariable=pv_var, **label_style_white).grid(row=0, column=1, sticky="w", padx=5, pady=3)
tk.Label(frame, textvariable=pv_today_var, **label_style_white).grid(row=1, column=1, sticky="w", padx=5, pady=3)
tk.Label(frame, textvariable=imp_var, **label_style_white).grid(row=2, column=1, sticky="w", padx=5, pady=3)
tk.Label(frame, textvariable=cons_var, **label_style_white).grid(row=3, column=1, sticky="w", padx=5, pady=3)
tk.Label(frame, textvariable=last_update_var, font=("Segoe UI", 9), fg="white", bg="#202020").grid(
    row=4, column=0, columnspan=2, sticky="w", pady=(10, 10)
)

btn_refresh = tk.Button(frame, text="Refresh", command=show_data, width=10)
btn_to_tray = tk.Button(frame, text="To Tray", command=hide_to_tray, width=10)

btn_refresh.grid(row=5, column=0, pady=5, padx=5)
btn_to_tray.grid(row=5, column=1, pady=5, padx=5)

round_button_style(btn_refresh, "green")
round_button_style(btn_to_tray, "red")

create_tray_icon()
show_data()
start_auto_update()
root.mainloop()
