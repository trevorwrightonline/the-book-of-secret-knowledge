"""Run this ONCE on your own computer to authorise uploads to your channel.

    pip install google-auth-oauthlib
    python3 get_token.py path/to/client_secret.json

A browser window opens; sign in with the Google account that owns the channel
and approve. The script prints three values to store as environment secrets:
YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN. Don't paste them into chat.
"""
import json
import sys

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/youtube.force-ssl"]  # force-ssl: thumbnails + captions

secrets = sys.argv[1] if len(sys.argv) > 1 else "client_secret.json"
flow = InstalledAppFlow.from_client_secrets_file(secrets, SCOPES)
creds = flow.run_local_server(port=0, prompt="consent", access_type="offline")
client = json.load(open(secrets))["installed"]
print("\nStore these as environment secrets:\n")
print("YT_CLIENT_ID=" + client["client_id"])
print("YT_CLIENT_SECRET=" + client["client_secret"])
print("YT_REFRESH_TOKEN=" + creds.refresh_token)
