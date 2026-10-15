"""Phone-friendly YouTube login (OAuth device flow). No computer needed.

Needs env vars YT_CLIENT_ID and YT_CLIENT_SECRET from an OAuth client of type
"TVs and Limited Input devices". Prints a short code: open google.com/device on
your phone, enter it, approve. The refresh token is saved to ~/.yt_token.json
(never printed), where upload.py finds it.
"""
import json
import os
import sys
import time

import requests

SCOPES = "https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube.force-ssl"
TOKEN_FILE = os.path.expanduser("~/.yt_token.json")

try:
    cid, secret = os.environ["YT_CLIENT_ID"], os.environ["YT_CLIENT_SECRET"]
except KeyError as e:
    sys.exit(f"Missing environment variable {e}.")

r = requests.post("https://oauth2.googleapis.com/device/code", data={"client_id": cid, "scope": SCOPES}, timeout=30)
r.raise_for_status()
d = r.json()
print(f"Open {d['verification_url']} on your phone and enter code:  {d['user_code']}", flush=True)

deadline = time.time() + d["expires_in"]
interval = d.get("interval", 5)
while time.time() < deadline:
    time.sleep(interval)
    t = requests.post("https://oauth2.googleapis.com/token", timeout=30, data={
        "client_id": cid, "client_secret": secret, "device_code": d["device_code"],
        "grant_type": "urn:ietf:params:oauth:grant-type:device_code"}).json()
    if "refresh_token" in t:
        with open(os.open(TOKEN_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600), "w") as f:
            json.dump({"refresh_token": t["refresh_token"]}, f)
        print("Connected. Token saved for uploads.")
        sys.exit(0)
    err = t.get("error")
    if err == "slow_down":
        interval += 5
    elif err != "authorization_pending":
        sys.exit(f"Login failed: {err}: {t.get('error_description', '')}")
sys.exit("Code expired before it was approved. Run again.")
