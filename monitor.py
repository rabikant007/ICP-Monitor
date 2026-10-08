import os
import json
import requests

# Grab secrets and print a warning if they are empty
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

print("Token loaded:", "YES" if TELEGRAM_BOT_TOKEN else "NO (IT IS EMPTY)")
print("Chat ID loaded:", "YES" if TELEGRAM_CHAT_ID else "NO (IT IS EMPTY)")

APIS = {
    "Subnets": "https://ic-api.internetcomputer.org/api/v3/subnets",
    "Node Machines": "https://ic-api.internetcomputer.org/api/v3/nodes",
    "Cloud Engines": "https://ic-api.internetcomputer.org/api/v3/cloud-engines"
}
STATE_FILE = "state.json"

def get_count(url):
    try:
        res = requests.get(url, timeout=15)
        if res.status_code == 200:
            data = res.json()
            if isinstance(data, list): return len(data)
            if "data" in data: return len(data["data"])
            if "total" in data: return int(data["total"])
    except Exception as e:
        print(f"Error fetching {url}: {e}")
    return None

def main():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            old_state = json.load(f)
    else:
        old_state = {}

    new_state = {}
    changes = []

    for name, url in APIS.items():
        current_count = get_count(url)
        if current_count is not None:
            new_state[name] = current_count
            old_count = old_state.get(name)

            if old_count is None:
                changes.append(f"✅ *{name}*: Started tracking at `{current_count}`")
            elif current_count != old_count:
                symbol = "📈 Increased" if current_count > old_count else "📉 Decreased"
                diff = current_count - old_count
                sign = "+" if diff > 0 else ""
                changes.append(f"{symbol}\n*{name}*: `{old_count}` ➡️ `{current_count}` ({sign}{diff})")

    with open(STATE_FILE, "w") as f:
        json.dump(new_state, f)

    if changes:
        if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
            message = "🚨 *ICP Dashboard Update*\n\n" + "\n\n".join(changes)
            telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            res = requests.post(telegram_url, json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message,
                "parse_mode": "Markdown"
            })
            print("Telegram Response Status:", res.status_code)
            print("Telegram Response Body:", res.text)
        else:
            print("ERROR: Secrets are missing or empty in GitHub!")
    else:
        print("No changes to report, but script executed successfully.")

if __name__ == "__main__":
    main()
