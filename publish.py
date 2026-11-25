#!/usr/bin/env python3
"""Publication directe sur YouTube (API officielle, sans passer par Make => aucune limite d'opérations).
Dormant tant que YT_CLIENT_ID, YT_CLIENT_SECRET et YT_REFRESH_TOKEN ne sont pas des secrets GitHub.
Usage : python publish.py <dossier out/...>   Sortie : écrit youtube.json (id) dans le dossier ; code 3 si non configuré."""
import json, os, sys, urllib.parse, urllib.request
D = sys.argv[1]
ids = [os.environ.get(k) for k in ("YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN")]
if not all(ids): print("YouTube direct non configuré"); sys.exit(3)
def call(url, data=None, headers=None, method=None):
    r = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    with urllib.request.urlopen(r, timeout=600) as x: return x.status, dict(x.headers), x.read()
tok = json.loads(call("https://oauth2.googleapis.com/token", urllib.parse.urlencode({"client_id": ids[0], "client_secret": ids[1],
      "refresh_token": ids[2], "grant_type": "refresh_token"}).encode())[2])["access_token"]
A = {"Authorization": "Bearer " + tok}
m = json.load(open(f"{D}/meta.json"))
body = {"snippet": {"title": m["title"], "description": m["description"], "tags": [t for t in m["tags"].split(",") if t],
        "categoryId": "28", "defaultLanguage": "fr", "defaultAudioLanguage": "fr"},
        "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False, "containsSyntheticMedia": True}}
if os.environ.get("SCHEDULE_AT"):  # programmation exacte : privée jusqu'à publishAt
    import datetime as _dt
    body["status"].update(privacyStatus="private", publishAt=_dt.datetime.fromtimestamp(int(os.environ["SCHEDULE_AT"]), _dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z"))
video = open(f"{D}/video.mp4", "rb").read()
_, h, _ = call("https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
               json.dumps(body).encode(), {**A, "Content-Type": "application/json; charset=UTF-8", "X-Upload-Content-Type": "video/mp4",
               "X-Upload-Content-Length": str(len(video))}, "POST")
_, _, out = call(h.get("Location") or h["location"], video, {**A, "Content-Type": "video/mp4"}, "PUT")
vid = json.loads(out)["id"]
call(f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={vid}", open(f"{D}/cover.jpg", "rb").read(), {**A, "Content-Type": "image/jpeg"}, "POST")
call("https://www.googleapis.com/youtube/v3/commentThreads?part=snippet", json.dumps({"snippet": {"videoId": vid, "topLevelComment": {"snippet": {"textOriginal": m["pinned_comment"]}}}}).encode(),
     {**A, "Content-Type": "application/json"}, "POST")
json.dump({"id": vid}, open(f"{D}/youtube.json", "w")); print("YouTube OK", vid)
