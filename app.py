from flask import Flask, render_template, request, redirect
import json
import threading
import websocket
import requests

app = Flask(__name__)

CONFIG_FILE = 'config.json'
WLED_IP = '192.168.178.59'

DEFAULT_CONFIG = {
    "READY": "green_static",
    "TAKEOUT": "yellow_static",
    "LEG_WON": "rainbow",
    "MATCH_WON": "rainbow",
    "TRIPLE_20": "pink_blink",
    "BULL": "green_blink",
    "DBULL": "green_blink",
    "MISS": "red_blink"
}

EFFECTS = {
    "green_static": "&R=0&G=255&B=0&T=1",
    "yellow_static": "&R=255&G=255&B=0&T=1",
    "rainbow": "&FX=80&SX=128&IX=128&T=1",
    "pink_blink": "&R=255&G=20&B=147&T=2",
    "green_blink": "&R=0&G=255&B=0&T=2",
    "red_blink": "&R=255&G=0&B=0&T=2",
    "off": "&T=0"
}

# Load or create config
def load_config():
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG

def save_config(config):
    
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f)
        

# Send command to WLED
def send_wled_command(effect_key):
    d_wled_command(\"red_blink\")
    if effect_key not in EFFECTS:
        return
    url = f"http://{WLED_IP}/win{EFFECTS[effect_key]}"
    try:
        requests.get(url, timeout=2)
    except requests.RequestException:
        pass

# WebSocket handler
def on_message(ws, message):
    print("💬 Nachricht von Autodarts:", message)  # <-- NEU für Debug
    config = load_config()
    for key in config:
        if key in message:
            send_wled_command(config[key])
            break

def start_websocket():
    ws = websocket.WebSocketApp("ws://192.168.178.108:3000/ws", on_message=on_message)
    ws.run_forever()

# Web GUI
@app.route('/', methods=['GET', 'POST'])
def index():
    config = load_config()
    if request.method == 'POST':
        for key in config.keys():
            config[key] = request.form.get(key)
        save_config(config)
        return redirect('/')
    return render_template('index.html', config=config, effects=EFFECTS)

# Start WebSocket listener in background
threading.Thread(target=start_websocket, daemon=True).start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
    send_wled_command(\"red_blink\")
