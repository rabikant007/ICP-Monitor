import os
import json
import requests

# Load the secret credentials you saved in GitHub
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# The exact URLs for the ICP dashboard data
APIS = {
    "Subnets": "https://ic-api.internetcomputer.org/api/v3/subnets",
    "Node Machines": "https://ic-api.internetcomputer.org/api/v3/nodes",
    "Cloud Engines": "https://ic-api.internetcomputer.org/api/v3/cloud-engines"
}
STATE_FILE = "state.json"

def get_count(url):
    """Fetches the number from the API."""
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
    # 1. Read the old numbers from the last time it checked
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            old_state = json.load(f)
    else:
        old_state = {}

    new_state = {}
    changes = []

    # 2. Check each parameter
    for name, url in APIS.items():
        current_count = get_count(url)
        if current_count is not None:
            new_state[name] = current_count
            old_count = old_state.get(name)

            # If this is the very first time running
            if old_count is None:
                changes.append(f"✅ *{name}*: Started tracking at `{current_count}`")
            # If the number went up or down
            elif current_count != old_count:
                symbol = "📈 Increased" if current_count > old_count else "📉 Decreased"
                diff = current_count - old_count
                sign = "+" if diff > 0 else ""
                changes.append(f"{symbol}\n*{name}*: `{old_count}` ➡️ `{current_count}` ({sign}{diff})")

    # 3. Save the new numbers for the next check
    with open(STATE_FILE, "w") as f:
        json.dump(new_state, f)

    # 4. If anything changed, send the Telegram message
    if changes and TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        message = "🚨 *ICP Dashboard Update*\n\n" + "\n\n".join(changes)
        telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(telegram_url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        })

if __name__ == "__main__":
    main()
