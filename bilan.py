#!/usr/bin/env python3
"""Bilan analytics quotidien (YouTube Data API) + consignes d'amélioration injectées dans l'écriture des scripts.
Sortie : bilans/AAAA-MM-JJ.md, perf.json (historique) et insights.json (lu par produce.py). Aucune clé affichée."""
import json, os, re, sys, datetime, urllib.parse, urllib.request
ids = [os.environ.get(k) for k in ("YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN")]
if not all(ids): print("YouTube non configuré"); sys.exit(3)
def get(url, h=None, data=None):
    with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=h or {}), timeout=120) as x: return json.loads(x.read())
tok = get("https://oauth2.googleapis.com/token", data=urllib.parse.urlencode({"client_id": ids[0], "client_secret": ids[1], "refresh_token": ids[2], "grant_type": "refresh_token"}).encode())["access_token"]
A = {"Authorization": "Bearer " + tok}
up = get("https://www.googleapis.com/youtube/v3/channels?part=contentDetails,statistics&mine=true", A)["items"][0]
pl = up["contentDetails"]["relatedPlaylists"]["uploads"]
vids = []
tokn = ""
while len(vids) < 150:
    r = get(f"https://www.googleapis.com/youtube/v3/playlistItems?part=contentDetails&maxResults=50&playlistId={pl}&pageToken={tokn}", A)
    vids += [i["contentDetails"]["videoId"] for i in r["items"]]; tokn = r.get("nextPageToken", "")
    if not tokn: break
rows = []
for i in range(0, len(vids), 50):
    r = get("https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics,contentDetails&id=" + ",".join(vids[i:i+50]), A)
    for v in r["items"]:
        s, st = v["snippet"], v["statistics"]
        pub = datetime.datetime.fromisoformat(s["publishedAt"].replace("Z", "+00:00"))
        age = max((datetime.datetime.now(datetime.timezone.utc) - pub).total_seconds() / 3600, 1)
        d = v["contentDetails"]["duration"]; sec = sum(int(n) * m for n, m in zip(re.findall(r"\d+", d)[::-1], (1, 60, 3600)))
        views = int(st.get("viewCount", 0))
        rows.append({"id": v["id"], "title": s["title"], "published": s["publishedAt"], "hour_paris": (pub.hour + 1) % 24, "short": sec <= 61,
                     "views": views, "likes": int(st.get("likeCount", 0)), "comments": int(st.get("commentCount", 0)), "views_per_h": round(views / age, 2), "age_h": round(age, 1)})
today = datetime.date.today().isoformat()
os.makedirs("bilans", exist_ok=True)
day = [r for r in rows if (datetime.datetime.now(datetime.timezone.utc) - datetime.datetime.fromisoformat(r["published"].replace("Z", "+00:00"))).total_seconds() < 86400]
top = sorted(rows, key=lambda r: -r["views_per_h"])[:5]; flop = sorted([r for r in rows if r["age_h"] > 24], key=lambda r: r["views_per_h"])[:5]
def avg(l, k): return round(sum(r[k] for r in l) / len(l), 2) if l else 0
by_hour = {}
for r in rows: by_hour.setdefault(r["hour_paris"], []).append(r["views_per_h"])
best_hours = sorted(by_hour, key=lambda h: -sum(by_hour[h]) / len(by_hour[h]))[:3]
words = {}
for r in rows:
    for w in set(re.findall(r"[a-zà-ÿ0-9]{4,}", r["title"].lower())): words.setdefault(w, []).append(r["views_per_h"])
good = sorted([w for w, l in words.items() if len(l) >= 2], key=lambda w: -sum(words[w]) / len(words[w]))[:8]
bad = sorted([w for w, l in words.items() if len(l) >= 2], key=lambda w: sum(words[w]) / len(words[w]))[:5]
sh, lg = [r for r in rows if r["short"]], [r for r in rows if not r["short"]]
md = [f"# Bilan du {today}", "", f"Chaîne : {up['statistics'].get('subscriberCount','?')} abonnés, {up['statistics'].get('viewCount','?')} vues au total, {len(rows)} vidéos.",
      f"Dernières 24 h : {len(day)} vidéos publiées, {sum(r['views'] for r in day)} vues, {sum(r['likes'] for r in day)} likes, {sum(r['comments'] for r in day)} commentaires.", "",
      f"Shorts : {len(sh)} vidéos, {avg(sh,'views_per_h')} vues/h en moyenne. Longues : {len(lg)} vidéos, {avg(lg,'views_per_h')} vues/h.", "",
      "## Meilleures vidéos (vues par heure)"] + [f"- {r['title']} : {r['views']} vues, {r['views_per_h']}/h" for r in top] + \
     ["", "## Moins bonnes (plus de 24 h)"] + [f"- {r['title']} : {r['views']} vues" for r in flop] + \
     ["", f"Meilleures heures de publication (Paris) : {', '.join(str(h)+'h' for h in best_hours)}", f"Mots de titre qui marchent : {', '.join(good) or 'pas assez de données'}", f"Mots de titre à éviter : {', '.join(bad) or 'pas assez de données'}"]
open(f"bilans/{today}.md", "w", encoding="utf8").write("\n".join(md) + "\n")
json.dump(rows, open("perf.json", "w", encoding="utf8"), ensure_ascii=False)
tips = []
if top: tips.append("Titres qui performent le mieux : " + " | ".join(r["title"] for r in top[:3]) + ". Reprends leur structure d'accroche (sans les copier).")
if good: tips.append("Mots qui attirent : " + ", ".join(good) + ".")
if bad: tips.append("Mots à éviter dans le titre : " + ", ".join(bad) + ".")
json.dump({"date": today, "consignes": tips}, open("insights.json", "w", encoding="utf8"), ensure_ascii=False, indent=1)
print("\n".join(md))
