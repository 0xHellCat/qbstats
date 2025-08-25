import requests
import json
from datetime import datetime
import os

# --- Charger config ---
CONFIG_FILE = os.getenv("CONFIG_FILE", "config.json")

with open(CONFIG_FILE, "r", encoding="utf-8") as f:
    cfg = json.load(f)

QB_URL = cfg["qb_url"]
QB_USER = cfg["qb_user"]
QB_PASS = cfg["qb_pass"]
OUTPUT_DIR = cfg.get("output_dir", "/data")

# --- Connexion ---
session = requests.Session()
login_data = {"username": QB_USER, "password": QB_PASS}
resp = session.post(f"{QB_URL}/api/v2/auth/login", data=login_data)

if resp.text != "Ok.":
    raise Exception("Échec connexion qBittorrent")

# --- Récupération infos ---
torrents = session.get(f"{QB_URL}/api/v2/torrents/info").json()
transfer_info = session.get(f"{QB_URL}/api/v2/transfer/info").json()

# --- Structuration ---
data = {
    "timestamp": datetime.now().isoformat(),
    "global_stats": transfer_info,
    "torrents": [
        {
            "name": t["name"],
            "progress": round(t["progress"] * 100, 2),
            "state": t["state"],
            "ratio": t["ratio"],
            "dlspeed": t["dlspeed"],
            "upspeed": t["upspeed"],
            "size": t["size"],
            "uploaded": t["uploaded"],
            "downloaded": t["downloaded"]
        }
        for t in torrents
    ]
}

# --- Sauvegarde journalière ---
date_str = datetime.now().strftime("%Y-%m-%d")
output_file = os.path.join(OUTPUT_DIR, f"stats_{date_str}.json")

with open(output_file, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"✅ Données sauvegardées dans {output_file}")
