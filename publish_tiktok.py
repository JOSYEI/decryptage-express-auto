#!/usr/bin/env python3
"""Publication TikTok directe via l'API officielle de Buffer (gratuit, sans Claude, sans PC).
Secret GitHub a creer une fois : BUFFER_API_KEY (publish.buffer.com/settings/api > Personal Access > + New Key ; duree max 1 an, a renouveler).
Usage : python publish_tiktok.py <dossier out/...> <url video.mp4>   Code 3 = non configure ; 1 = echec."""
import json, os, re, sys, urllib.request, urllib.error
D, VURL = sys.argv[1], sys.argv[2]
KEY = os.environ.get("BUFFER_API_KEY")
CHANNEL = os.environ.get("BUFFER_TIKTOK_CHANNEL_ID", "6af07cd762b70b94b0be78e0")
if not KEY: print("TikTok direct non configure"); sys.exit(3)
m = json.load(open(f"{D}/meta.json"))
body = m["description"].split("📝 LE RÉSUMÉ")[0].split("🔑 MOTS-CLÉS")[0].strip()
tags = " ".join(["#IA", "#DécryptageExpress"] + [t for t in re.findall(r"#\w+", m["description"]) if t.lower() not in ("#ia", "#décryptageexpress", "#shorts")][:3])
text = (body[:2200 - len(tags) - 2].rstrip() + "\n\n" + tags)
title = m["title"][:90]
title = re.sub(r"(\s+(du|de|la|le|des|un|et|#))+$", "", title).rstrip(" ,;:#-–")
q = lambda s: json.dumps(s, ensure_ascii=False)
def run(with_meta):
    meta = f"metadata: {{ tiktok: {{ title: {q(title)} }} }}" if with_meta else ""
    query = f"""mutation {{ createPost(input: {{ text: {q(text)}, channelId: "{CHANNEL}", schedulingType: automatic, mode: shareNow,
      assets: [{{ video: {{ url: {q(VURL)} }} }}] {meta} }}) {{ ... on PostActionSuccess {{ post {{ id }} }} ... on MutationError {{ message }} }} }}"""
    r = urllib.request.Request("https://api.buffer.com", json.dumps({"query": query}).encode(),
                               {"Content-Type": "application/json", "Authorization": "Bearer " + KEY}, method="POST")
    try:
        with urllib.request.urlopen(r, timeout=300) as x: return json.loads(x.read())
    except urllib.error.HTTPError as e: return {"http": e.code, "body": e.read()[:400].decode("utf-8", "ignore")}
for meta in (True, False):   # si le champ titre TikTok est refuse, on reessaie sans
    out = run(meta); print(json.dumps(out, ensure_ascii=False)[:500])
    post = (((out.get("data") or {}).get("createPost")) or {}).get("post")
    if post: print("TikTok OK", post["id"]); sys.exit(0)
sys.exit(1)
