#!/usr/bin/env python3
"""Exécute planning.json : pour chaque vidéo prévue, programme Facebook (heure exacte) ou publie Instagram à l'heure.
Entrée : planning.json = [{"date":"2026-11-25","slot":"10:00","tag":"v47-mer-long","nets":["fblong"]}, ...] (heure de Paris, jamais écrite en public).
nets : yt (YouTube programmé), fblong (vidéo longue Facebook), fb (reel Facebook), ig (reel Instagram). Sortie : planning_done.json (évite les doublons)."""
import json, os, subprocess, sys, time, urllib.request, datetime as dt
from zoneinfo import ZoneInfo
REPO = os.environ.get("GITHUB_REPOSITORY", "JOSYEI/decryptage-express-auto")
plan = json.load(open("planning.json")); done = json.load(open("planning_done.json")) if os.path.exists("planning_done.json") else {}
now = time.time(); changed = False
for e in sorted(plan, key=lambda x: (x["date"], x["slot"])):
    ts = dt.datetime.fromisoformat(f'{e["date"]}T{e["slot"]}:00').replace(tzinfo=ZoneInfo("Europe/Paris")).timestamp()
    for net in e["nets"]:
        key = f'{e["tag"]}:{net}'
        if key in done: continue
        if ts < now + 660 and net != "ig": print("trop tard / trop proche, ignoré :", key); continue
        if net == "ig" and not (now - 600 < ts < now + 5 * 3600): continue  # Instagram : seulement dans la fenêtre de la prochaine exécution
        D = f'out/{e["tag"]}'; os.makedirs(D, exist_ok=True)
        base = f"https://github.com/{REPO}/releases/download/{e['tag']}"
        urllib.request.urlretrieve(base + "/meta.json", f"{D}/meta.json")
        env = {**os.environ, "SCHEDULE_AT": str(int(ts))}
        if net == "yt":
            for f in ("video.mp4", "cover.jpg"): urllib.request.urlretrieve(f"{base}/{f}", f"{D}/{f}")
            r = subprocess.run([sys.executable, "publish.py", D], env=env)
        else:
            r = subprocess.run([sys.executable, "publish_meta.py", D, net, base + "/video.mp4"], env=env)
        print(key, "code", r.returncode)
        if r.returncode == 0: done[key] = dt.datetime.utcnow().isoformat(); changed = True
if changed: json.dump(done, open("planning_done.json", "w"), indent=1)
