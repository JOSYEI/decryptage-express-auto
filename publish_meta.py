#!/usr/bin/env python3
"""Publication directe Facebook + Instagram (Graph API officielle) : gratuit, sans quota Make.
Secrets GitHub (a creer une fois) : FB_PAGE_ID, FB_PAGE_TOKEN (jeton de Page longue duree), IG_USER_ID (compte Instagram Pro lie a la Page).
Usage : python publish_meta.py <dossier out/...> <fb|fblong|ig> <url video.mp4>
Code de sortie 0 = publie ; 3 = non configure ; 1 = echec (le workflow bascule alors sur Make en secours)."""
import json, os, sys, time, urllib.parse, urllib.request, urllib.error
D, KIND, VURL = sys.argv[1], sys.argv[2], sys.argv[3]
G = "https://graph.facebook.com/v21.0"
SCHED = os.environ.get("SCHEDULE_AT")  # epoch (UTC) : programmation exacte (Facebook) ou attente avant publication (Instagram)
PAGE, TOK, IG = (os.environ.get(k) for k in ("FB_PAGE_ID", "FB_PAGE_TOKEN", "IG_USER_ID"))
if not (PAGE and TOK) or (KIND == "ig" and not IG): print("Meta direct non configure"); sys.exit(3)
m = json.load(open(f"{D}/meta.json"))
def post(url, data, headers=None):
    r = urllib.request.Request(url, urllib.parse.urlencode(data).encode(), headers or {}, method="POST")
    try:
        with urllib.request.urlopen(r, timeout=600) as x: return json.loads(x.read() or b"{}")
    except urllib.error.HTTPError as e: print("HTTP", e.code, e.read()[:500]); raise
def get(url):
    with urllib.request.urlopen(url, timeout=120) as x: return json.loads(x.read())
if KIND == "fb":  # Reel Facebook
    s = post(f"{G}/{PAGE}/video_reels", {"upload_phase": "start", "access_token": TOK})
    post(s["upload_url"], {}, {"Authorization": "OAuth " + TOK, "file_url": VURL})
    for _ in range(30):
        st = get(f"{G}/{s['video_id']}?fields=status&access_token={TOK}").get("status", {})
        if st.get("uploading_phase", {}).get("status") == "complete" or st.get("video_status") in ("ready", "upload_complete"): break
        time.sleep(10)
    fin = {"upload_phase": "finish", "video_id": s["video_id"], "video_state": "PUBLISHED", "description": m["description"][:2000], "access_token": TOK}
    if SCHED: fin.update(video_state="SCHEDULED", scheduled_publish_time=SCHED)
    post(f"{G}/{PAGE}/video_reels", fin)
    try: post(f"{G}/{s['video_id']}/comments", {"message": m["pinned_comment"], "access_token": TOK})
    except Exception as e: print("commentaire non poste", e)
    print("Facebook reel OK", s["video_id"])
elif KIND == "fblong":  # Video longue Facebook
    d = {"file_url": VURL, "title": m["title"][:255],
         "description": (m["description"][:1900] + "\n\n📖 Article complet et toutes nos vidéos : https://decryptageexpress.com"), "access_token": TOK}
    if SCHED: d.update(published="false", scheduled_publish_time=SCHED, unpublished_content_type="SCHEDULED")
    r = post(f"{G}/{PAGE}/videos", d)
    print("Facebook video OK", r.get("id"))
elif KIND == "ig":  # Reel Instagram
    import subprocess
    cap = subprocess.run([sys.executable, "igtext.py", D], capture_output=True, text=True).stdout.strip() or m["description"]
    c = post(f"{G}/{IG}/media", {"media_type": "REELS", "video_url": VURL, "caption": cap[:2200], "share_to_feed": "true", "access_token": TOK})
    for _ in range(40):
        sc = get(f"{G}/{c['id']}?fields=status_code&access_token={TOK}").get("status_code")
        if sc == "FINISHED": break
        if sc in ("ERROR", "EXPIRED"): print("Instagram traitement", sc); sys.exit(1)
        time.sleep(10)
    if SCHED: time.sleep(max(0, int(SCHED) - time.time()))  # publication à l'heure exacte
    r = post(f"{G}/{IG}/media_publish", {"creation_id": c["id"], "access_token": TOK})
    print("Instagram reel OK", r.get("id"))
