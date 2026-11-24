#!/usr/bin/env python3
"""Ajoute au blog des articles pour les anciens Shorts deja publies (TikTok), a la date de publication d'origine.
Usage : python backfill_blog.py tiktok_posts.json   (liste {date, text, src} issue de Buffer) puis python blog.py --rebuild"""
import json, os, re, sys, datetime, zoneinfo
posts = json.load(open(sys.argv[1], encoding="utf-8"))
norm = lambda s: re.sub(r"[^a-z0-9]+", " ", s.lower().encode("ascii", "ignore").decode()).strip()
os.makedirs("docs/data", exist_ok=True); n = 0
for p in sorted(posts, key=lambda p: p["date"]):
    m = re.search(r"tiktok\.com/@[^/]+/video/(\d+)", p.get("src", ""))
    if not m: continue
    day = datetime.datetime.fromisoformat(p["date"].replace("Z", "+00:00")).astimezone(zoneinfo.ZoneInfo("Europe/Paris")).strftime("%Y-%m-%d")
    body = re.sub(r"\s#\S.*$", "", p["text"].strip(), flags=re.S).strip()          # retire le bloc de hashtags final
    body = re.sub(r"[\U0001F300-\U0001FAFF☀-➿️]", "", body).strip()  # retire les emojis
    first = re.split(r"(?<=[?!.])\s", body, 1)[0].strip()
    title = (first if len(first) <= 90 else first[:90].rsplit(" ", 1)[0]).rstrip(" ,;:.")
    slug = day + "-" + re.sub(r"[^a-z0-9]+", "-", norm(title))[:50].strip("-")
    desc = body + "\n\nCe Short est aussi disponible sur TikTok, Instagram, Facebook et YouTube : Décryptage Express décrypte l'actu IA, tech et bourse chaque jour."
    json.dump({"slug": slug, "title": title, "full_title": title, "date": day, "desc": desc, "yt": None, "tt": m.group(1)},
              open(f"docs/data/{slug}.json", "w", encoding="utf-8"), ensure_ascii=False); n += 1
print(n, "articles ajoutes")
