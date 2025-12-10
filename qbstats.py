
import requests
import json
import os
import sys
from datetime import datetime, timedelta

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    if not os.path.exists(config_path):
        print(f"Error: Config file not found at {config_path}")
        sys.exit(1)
    with open(config_path, 'r') as f:
        return json.load(f)

def get_data_dir():
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    return data_dir

def load_daily_file(date_str):
    data_dir = get_data_dir()
    filepath = os.path.join(data_dir, f"{date_str}.json")
    if not os.path.exists(filepath):
        return []
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

def save_daily_file(date_str, entries):
    data_dir = get_data_dir()
    filepath = os.path.join(data_dir, f"{date_str}.json")
    with open(filepath, 'w') as f:
        json.dump(entries, f, indent=4)

def login(session, url, username, password):
    try:
        resp = session.post(f"{url}/api/v2/auth/login", data={'username': username, 'password': password}, timeout=10)
        if resp.status_code == 200 and "Ok." in resp.text:
            return True
        elif resp.status_code == 403:
             print(f"Login failed: {resp.text}")
             return False
        else:
            if resp.text == "Ok.":
                 return True
            print(f"Login failed. Status: {resp.status_code}, Body: {resp.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Connection error during login: {e}")
        return False

def get_transfer_info(session, url):
    try:
        resp = session.get(f"{url}/api/v2/transfer/info", timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching transfer info: {e}")
        return None

def get_torrents_info(session, url):
    try:
        resp = session.get(f"{url}/api/v2/torrents/info", timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching torrents info: {e}")
        return None



def update_uploaded_stats(torrents_info):
    """
    Updates data/uploaded.json with current torrent info.
    Returns the global total uploaded bytes.
    """
    uploaded_file_path = os.path.join(get_data_dir(), "uploaded.json")
    uploaded_data = {}
    
    if os.path.exists(uploaded_file_path):
        try:
            with open(uploaded_file_path, 'r') as f:
                uploaded_data = json.load(f)
        except json.JSONDecodeError:
            uploaded_data = {}

    for t in torrents_info:
        t_hash = t.get('hash')
        t_name = t.get('name')
        t_uploaded = t.get('uploaded', 0)
        
        if t_hash in uploaded_data:
            # Update if current uploaded is higher
            if t_uploaded > uploaded_data[t_hash]['uploaded']:
                uploaded_data[t_hash]['uploaded'] = t_uploaded
                uploaded_data[t_hash]['name'] = t_name 
        else:
            # New entry
            uploaded_data[t_hash] = {
                "name": t_name,
                "uploaded": t_uploaded
            }
            
    # Calculate Total Uploaded (Global) from uploaded.json
    total_uploaded_global = sum(item['uploaded'] for item in uploaded_data.values())
    
    # Save uploaded.json
    with open(uploaded_file_path, 'w') as f:
        json.dump(uploaded_data, f, indent=4)
        
    print(f"Updated uploaded tracking: data/uploaded.json")
    return total_uploaded_global

def main():
    config = load_config()
    
    url = config.get('url')
    username = config.get('username')
    password = config.get('password')
    
    if url.endswith('/'):
        url = url[:-1]

    session = requests.Session()
    
    print(f"Connecting to {url}...")
    if not login(session, url, username, password):
        print("Could not authenticate. Please check your credentials in config.json.")
        sys.exit(1)
        
    print("Authenticated successfully.")
    
    transfer_info = get_transfer_info(session, url)
    torrents_info = get_torrents_info(session, url)
    
    if not transfer_info or torrents_info is None:
        sys.exit(1)
        
    current_uploaded_bytes = transfer_info.get('up_info_data', 0)
    current_time = datetime.now()
    today_str = current_time.strftime("%Y-%m-%d")
    
    torrents_data = []
    for t in torrents_info:
        torrents_data.append({
            "name": t.get("name"),
            "hash": t.get("hash"),
            "size": t.get("size"),
            "uploaded": t.get("uploaded"),
            "ratio": t.get("ratio"),
            "added_on": t.get("added_on")
        })

    entry = {
        "timestamp": current_time.isoformat(),
        "total_uploaded": current_uploaded_bytes,
        "torrents": torrents_data
    }
    
    # Save to today's file
    today_entries = load_daily_file(today_str)
    today_entries.append(entry)
    save_daily_file(today_str, today_entries)
    
    print(f"Saved entry to data/{today_str}.json")

    # --- Compare with Yesterday ---
    yesterday_str = (current_time - timedelta(days=1)).strftime("%Y-%m-%d")
    yesterday_entries = load_daily_file(yesterday_str)
    
    upload_diffs = []
    added_files = []
    deleted_files = []

    # We compare the CURRENT entry with the LAST entry of yesterday
    # If yesterday has no data, we can't generate diffs properly.
    
    if yesterday_entries:
        last_yesterday = yesterday_entries[-1]
        
        # Build maps for comparison {hash: torrent_obj}
        yesterday_map = {t['hash']: t for t in last_yesterday.get('torrents', [])}
        today_map = {t['hash']: t for t in entry['torrents']}
        
        # 1. Upload Diff (upload-YYYY-MM-DD.json)
        upload_diffs = []
        for h, t_now in today_map.items():
            if h in yesterday_map:
                t_prev = yesterday_map[h]
                diff = t_now['uploaded'] - t_prev['uploaded']
                if diff > 0:
                    upload_diffs.append({
                        "name": t_now['name'],
                        "upload_diff": diff,
                        "total_uploaded_now": t_now['uploaded']
                    })
        
        # Save upload diff
        if upload_diffs:
            upload_file = os.path.join(get_data_dir(), f"upload-{today_str}.json")
            with open(upload_file, 'w') as f:
                json.dump(upload_diffs, f, indent=4)
            print(f"Generated upload report: data/upload-{today_str}.json")

        # 2. Update Diff (update-YYYY-MM-DD.json) -> Added / Deleted
        added_files = []
        deleted_files = []
        
        for h, t_now in today_map.items():
            if h not in yesterday_map:
                added_files.append({"name": t_now['name'], "hash": h})
                
        for h, t_prev in yesterday_map.items():
            if h not in today_map:
                deleted_files.append({"name": t_prev['name'], "hash": h})
                
        if added_files or deleted_files:
            update_data = {
                "added": added_files,
                "deleted": deleted_files
            }
            update_file = os.path.join(get_data_dir(), f"update-{today_str}.json")
            with open(update_file, 'w') as f:
                json.dump(update_data, f, indent=4)
            print(f"Generated update report: data/update-{today_str}.json")

    # --- Limitless 24h Stats Calculation (Global) ---
    # Calculate 24h stats as sum of individual torrent upload differences
    stats_24h = sum(d['upload_diff'] for d in upload_diffs)
    
    # Find closest entry for time reference in message
    target_time = current_time - timedelta(hours=24)
    
    candidates = []
    candidates.extend(yesterday_entries)
    candidates.extend(today_entries) 
    
    closest_entry = None
    min_diff = timedelta(hours=24)
    
    for item in candidates:
        try:
            item_time = datetime.fromisoformat(item['timestamp'])
            time_diff = abs(item_time - target_time)
            if time_diff < min_diff and item_time <= current_time:
                min_diff = time_diff
                closest_entry = item
        except ValueError:
            continue

    # --- Uploaded Tracking (uploaded.json) ---
    total_uploaded_global = update_uploaded_stats(torrents_info)

    # --- Prepare Discord Message ---
    message_lines = []
    
    # Upload Diff Section
    if upload_diffs:
        message_lines.append("**Top Uploaders (Last 24h)**")
        upload_diffs.sort(key=lambda x: x['upload_diff'], reverse=True)
        for d in upload_diffs: # Show all
             message_lines.append(f"- {d['name']} : +{sizeof_fmt(d['upload_diff'])}")
        message_lines.append("") # Blank line

    # Update Diff Section
    if added_files or deleted_files:
        message_lines.append(f"**Generated update report**: `data/update-{today_str}.json`")
        if added_files:
            message_lines.append(f"Files Added: {len(added_files)}")
        if deleted_files:
            message_lines.append(f"Files Deleted: {len(deleted_files)}")
        message_lines.append("")

    # Global Stats Section
    message_lines.append("**Statistics**")
    message_lines.append(f"Total Uploaded (Global): {sizeof_fmt(total_uploaded_global)}")
    
    if closest_entry:
         message_lines.append(f"Uploaded in last 24h:    {sizeof_fmt(stats_24h)}")
         time_ago = current_time - datetime.fromisoformat(closest_entry['timestamp'])
         hours = int(time_ago.total_seconds() // 3600)
         minutes = int((time_ago.total_seconds() % 3600) // 60)
         message_lines.append(f"(Compared to data from {hours}h {minutes}m ago)")
    else:
         message_lines.append("Uploaded in last 24h:    Not enough history.")

    # Send detailed message to Discord if configured
    discord_url = config.get('discord_webhook_url')
    if discord_url and message_lines:
        discord_msg = "\n".join(message_lines)
        if len(discord_msg) > 1900: # Discord limit slightly below 2000
             discord_msg = discord_msg[:1900] + "\n...(truncated)"
        
        try:
            r = requests.post(discord_url, json={"content": discord_msg}, timeout=10)
            if r.status_code in [200, 204]:
                print("Notification sent to Discord.")
            else:
                print(f"Failed to send Discord notification: {r.status_code} - {r.text}")
        except Exception as e:
            print(f"Error sending Discord notification: {e}")
    else:
        # Fallback to console if no webhook or empty message
        print("\n".join(message_lines))

def sizeof_fmt(num, suffix="B"):
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"

if __name__ == "__main__":
    main()

