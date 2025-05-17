# 🌞 Solar Widget – Desktop Display for Growatt Solar Data

This tool displays your current PV power values directly on your desktop. The data is retrieved from the Growatt server (server-us.growatt.com). It runs as a small, transparent widget with tray icon and automatic updates.

## ✅ Requirements

### Python (recommended: 3.10 or 3.11)


### 2. Required Python Packages
Install all required packages using `pip`:

```bash
pip install playwright pystray pillow
```

Initialize Playwright (only once):

```bash
playwright install
```

### 3. Add Chromium
- Copy chromium-1169/chrome-win/ to the script's working directory

```
./SolarWidget/chromium-1169/chrome-win/chrome.exe
```

👉 This is needed because Playwright requires a manual Chromium path in compiled versions.

### 4. Create Configuration File
Create a `config.txt` in the same directory as the script:

```txt
intervall=60
username=YOUR_USERNAME
password=YOUR_PASSWORD_BASE64
```

📌 Note:
- The password **must** be Base64-encoded.

### 5. Compile
You can compile the script with pyinstaller: 
```
pyinstaller --onefile --windowed --add-data "chromium-1169;chromium-1169" solarwidget.py
```

