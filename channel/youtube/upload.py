"""Upload a rendered video to YouTube with title, description, tags, thumbnail and captions.

Needs env vars YT_CLIENT_ID and YT_CLIENT_SECRET, plus a login: run device_login.py (phone)
or set YT_REFRESH_TOKEN (get_token.py, computer).

    python3 youtube/upload.py out/v03_real_cost --title "..." [--privacy private] [--publish-at 2026-10-20T22:00:00Z]

The folder must contain one .mp4; thumbnail.png, captions.srt and description.txt are used if present.
Uploads default to PRIVATE so a human reviews them in YouTube Studio before they go public.
(YouTube also forces private for API projects that haven't passed its API audit.)
"""
import argparse
import glob
import json
import os
import sys

import requests

API = "https://www.googleapis.com/youtube/v3"
UPLOAD = "https://www.googleapis.com/upload/youtube/v3"


def access_token():
    refresh = os.environ.get("YT_REFRESH_TOKEN")
    token_file = os.path.expanduser("~/.yt_token.json")
    if not refresh and os.path.exists(token_file):
        refresh = json.load(open(token_file))["refresh_token"]  # written by device_login.py
    try:
        data = dict(client_id=os.environ["YT_CLIENT_ID"], client_secret=os.environ["YT_CLIENT_SECRET"],
                    refresh_token=refresh, grant_type="refresh_token")
    except KeyError as e:
        sys.exit(f"Missing environment variable {e}. See youtube/device_login.py.")
    if not refresh:
        sys.exit("Not logged in. Run youtube/device_login.py (phone) or set YT_REFRESH_TOKEN (get_token.py).")
    r = requests.post("https://oauth2.googleapis.com/token", data=data, timeout=30)
    r.raise_for_status()
    return r.json()["access_token"]


def upload_video(tok, mp4, meta):
    h = {"Authorization": f"Bearer {tok}"}
    init = requests.post(f"{UPLOAD}/videos?uploadType=resumable&part=snippet,status", json=meta,
                         headers={**h, "X-Upload-Content-Type": "video/mp4",
                                  "X-Upload-Content-Length": str(os.path.getsize(mp4))}, timeout=60)
    init.raise_for_status()
    with open(mp4, "rb") as f:
        r = requests.put(init.headers["Location"], data=f, headers={**h, "Content-Type": "video/mp4"}, timeout=3600)
    r.raise_for_status()
    return r.json()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--title", required=True)
    ap.add_argument("--tags", default="homebuying,mortgage,personal finance,real estate,first time home buyer,housing market")
    ap.add_argument("--privacy", default="private", choices=["private", "unlisted", "public"])
    ap.add_argument("--publish-at", help="RFC3339 time; video stays private until then (requires --privacy private)")
    a = ap.parse_args()

    mp4 = [p for p in glob.glob(os.path.join(a.folder, "*.mp4")) if ".tmp" not in p]
    assert len(mp4) == 1, f"expected one mp4 in {a.folder}, found {mp4}"
    desc_p = os.path.join(a.folder, "description.txt")
    desc = open(desc_p).read() if os.path.exists(desc_p) else ""
    if "AI voice" not in desc:
        desc = desc.rstrip() + "\n\nNarration uses an AI voice."
    status = {"privacyStatus": a.privacy, "selfDeclaredMadeForKids": False, "containsSyntheticMedia": False}
    if a.publish_at:
        status["publishAt"] = a.publish_at
    meta = {"snippet": {"title": a.title[:100], "description": desc[:5000], "tags": a.tags.split(","),
                        "categoryId": "27", "defaultLanguage": "en", "defaultAudioLanguage": "en"},  # 27 = Education
            "status": status}

    tok = access_token()
    v = upload_video(tok, mp4[0], meta)
    vid = v["id"]
    print("uploaded:", f"https://youtu.be/{vid}", "privacy:", v["status"]["privacyStatus"])
    h = {"Authorization": f"Bearer {tok}"}

    thumb = os.path.join(a.folder, "thumbnail.png")
    if os.path.exists(thumb):
        r = requests.post(f"{UPLOAD}/thumbnails/set?videoId={vid}", data=open(thumb, "rb"),
                          headers={**h, "Content-Type": "image/png"}, timeout=120)
        print("thumbnail:", "ok" if r.ok else f"failed ({r.status_code}: {r.text[:200]})")

    srt = os.path.join(a.folder, "captions.srt")
    if os.path.exists(srt):
        body = {"snippet": {"videoId": vid, "language": "en", "name": "English", "isDraft": False}}
        boundary = "captionboundary"
        payload = (f"--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n{json.dumps(body)}\r\n"
                   f"--{boundary}\r\nContent-Type: application/octet-stream\r\n\r\n").encode() + \
            open(srt, "rb").read() + f"\r\n--{boundary}--".encode()
        r = requests.post(f"{UPLOAD}/captions?uploadType=multipart&part=snippet", data=payload,
                          headers={**h, "Content-Type": f"multipart/related; boundary={boundary}"}, timeout=120)
        print("captions:", "ok" if r.ok else f"failed ({r.status_code}: {r.text[:200]})")


if __name__ == "__main__":
    main()
