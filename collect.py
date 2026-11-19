#!/usr/bin/env python3
"""Décryptage Express - étape 1 : choix automatique du sujet du jour.

Lit Google Actualités (RSS), regroupe les articles qui parlent de la même
histoire, calcule un score et écrit topic.json. Aucune dépendance externe.
Sortie : topic.json (status "ok" ou "skip"), journal dans log.csv.
"""
import csv, datetime as dt, email.utils, html, json, os, re, sys, time
import urllib.parse, urllib.request
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
QUERIES = [
    "robot humanoïde", "robots humanoïdes", "humanoid robot",
    "Tesla Optimus", "Figure AI robot", "Unitree robot", "Boston Dynamics Atlas",
    "Agility Robotics Digit", "1X NEO robot", "Apptronik Apollo",
]
MIN_SCORE = 50          # en dessous : pas de vidéo ce jour-là
MIN_TRUSTED = 2         # sources fiables différentes minimum
MAX_AGE_H = 30

TRUSTED = [
    "le monde", "les echos", "les échos", "le figaro", "bfm", "numerama", "clubic",
    "frandroid", "01net", "journal du geek", "reuters", "techcrunch", "the verge",
    "wired", "ieee spectrum", "cnbc", "bloomberg", "bbc", "futura", "l'usine",
    "usine nouvelle", "siècle digital", "presse-citron", "le monde informatique",
    "zdnet", "ars technica", "financial times", "the guardian", "afp", "france 24",
    "la tribune", "challenges", "les numériques", "generation-nt", "actu.fr",
    "le parisien", "ouest-france", "science et vie", "sciences et avenir",
    "the robot report", "interesting engineering", "new atlas", "engadget",
    "associated press", "forbes", "business insider", "mit technology review",
    "génération nt", "l'informaticien", "paperjam", "usine digitale", "silicon.fr", "lemagit",
    "journal du net", "maddyness", "capital", "l'express", "libération", "le point", "20 minutes",
    "euronews", "franceinfo", "courrier international", "techradar", "cnet", "the register",
    "tom's guide", "tom's hardware", "euractiv", "la croix", "les numériques", "01net",
    "channelnews", "itpro", "decideurs", "usine-digitale", "bpifrance", "cio-online",
]
NICHE = ["humanoïde", "humanoide", "humanoid", "optimus", "figure", "unitree", "atlas",
         "digit", "neo", "apptronik", "agility", "robot", "robotique", "boston dynamics",
         "nvidia", "xpeng", "ubtech", "fourier", "agibot"]
GENERIC = set("robot robots humanoïde humanoïdes humanoide humanoides humanoid usine entreprise nouveau nouvelle million millions milliard milliards ia intelligence artificielle company new first".split())
STOP = set("""le la les un une des de du d l et en au aux à a ce ces se sa son ses
sur pour par avec dans qui que quoi est sont il elle ils elles the of to in on for and
a an is are with by at as from its it his her their vs après avant plus très pas ne""".split())


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt == 3:
                raise
            time.sleep(8 * (attempt + 1))


def norm_tokens(title):
    t = re.sub(r"[^\w\s]", " ", title.lower())
    return {w for w in t.split() if w not in STOP and w not in GENERIC and len(w) > 2}


def jacc(a, b):
    return len(a & b) / len(a | b) if a and b else 0.0


def same_story(a, b):
    sh = len(a & b)
    return sh >= 2 and sh / min(len(a), len(b)) >= 0.5


def parse_feed(q):
    url = ("https://news.google.com/rss/search?q=" + urllib.parse.quote(q + " when:1d")
           + "&hl=fr&gl=FR&ceid=FR:fr")
    root = ET.fromstring(fetch(url))
    out = []
    for it in root.iter("item"):
        title = html.unescape(it.findtext("title") or "")
        src_el = it.find("source")
        source = (src_el.text if src_el is not None else "") or ""
        if source and title.endswith(" - " + source):
            title = title[: -len(" - " + source)]
        try:
            pub = email.utils.parsedate_to_datetime(it.findtext("pubDate"))
        except Exception:
            continue
        out.append({"title": title.strip(), "source": source.strip(),
                    "link": it.findtext("link") or "", "published": pub})
    return out


def is_trusted(src):
    s = src.lower()
    return any(t in s for t in TRUSTED)


def load_history():
    p = os.path.join(HERE, "history.json")
    if os.path.exists(p):
        return json.load(open(p, encoding="utf-8"))
    return []


def main():
    now = dt.datetime.now(dt.timezone.utc)
    arts, seen = [], set()
    for qi, q in enumerate(QUERIES):
        if qi:
            time.sleep(2)
        try:
            for a in parse_feed(q):
                key = (a["title"].lower(), a["source"].lower())
                age = (now - a["published"]).total_seconds() / 3600
                if key in seen or age > MAX_AGE_H or age < -1 or not a["source"]:
                    continue
                seen.add(key)
                a["age_h"] = max(age, 0)
                a["tok"] = norm_tokens(a["title"])
                arts.append(a)
        except Exception as e:
            print("flux ignoré:", q, e, file=sys.stderr)

    # regroupement glouton par similarité de titre
    clusters = []
    for a in sorted(arts, key=lambda x: x["age_h"]):
        for c in clusters:
            if same_story(a["tok"], c["tok"]) or jacc(a["tok"], c["tok"]) >= 0.4:
                c["items"].append(a); c["tok"] |= a["tok"]; break
        else:
            clusters.append({"items": [a], "tok": set(a["tok"])})

    hist = load_history()
    hist_tok = [set(h["tokens"]) for h in hist[-60:]]
    scored = []
    for c in clusters:
        items = c["items"]
        trusted = {i["source"].lower() for i in items if is_trusted(i["source"])}
        allsrc = {i["source"].lower() for i in items}
        newest = min(i["age_h"] for i in items)
        fresh = 25 if newest <= 12 else 15 if newest <= 24 else 5
        multi = min(len(trusted), 3) / 3 * 25
        text = " ".join(i["title"].lower() for i in items)
        hits = sum(1 for k in NICHE if k in text)
        niche = min(hits, 4) / 4 * 20
        concrete = 15 if re.search(r"\d", " ".join(i["title"] for i in items)) else 0
        novel = 15 * (1 - max([jacc(c["tok"], h) for h in hist_tok] or [0]))
        score = round(fresh + multi + niche + concrete + novel, 1)
        scored.append({"score": score, "trusted": len(trusted), "sources": len(allsrc),
                       "cluster": c})
    scored.sort(key=lambda x: -x["score"])

    result = {"date": now.astimezone().strftime("%Y-%m-%d"), "status": "skip",
              "reason": "", "topic": None}
    best = next((s for s in scored if s["trusted"] >= MIN_TRUSTED and s["score"] >= MIN_SCORE), None)
    if best is None:
        top = scored[0] if scored else None
        result["reason"] = ("aucun article" if not top else
                            f"meilleur score {top['score']} avec {top['trusted']} source(s) fiable(s) "
                            f"(minimum {MIN_SCORE} et {MIN_TRUSTED})")
    else:
        items = sorted(best["cluster"]["items"], key=lambda i: i["age_h"])
        result.update(status="ok", topic={
            "title": items[0]["title"], "score": best["score"],
            "trusted_sources": best["trusted"],
            "articles": [{"title": i["title"], "source": i["source"], "link": i["link"],
                          "published": i["published"].isoformat()} for i in items[:8]]})
        hist.append({"date": result["date"], "title": items[0]["title"],
                     "tokens": sorted(best["cluster"]["tok"])})
        json.dump(hist[-200:], open(os.path.join(HERE, "history.json"), "w", encoding="utf-8"),
                  ensure_ascii=False)

    json.dump(result, open(os.path.join(HERE, "topic.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    newfile = not os.path.exists(os.path.join(HERE, "log.csv"))
    with open(os.path.join(HERE, "log.csv"), "a", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        if newfile:
            w.writerow(["date", "statut", "score", "sources_fiables", "sujet", "raison"])
        t = result["topic"]
        w.writerow([result["date"], result["status"], t["score"] if t else "",
                    t["trusted_sources"] if t else "", t["title"] if t else "", result["reason"]])
    print(json.dumps({k: result[k] for k in ("status", "reason")}, ensure_ascii=False))
    for s in scored[:5]:
        print(s["score"], s["trusted"], "|", s["cluster"]["items"][0]["title"][:90])


if __name__ == "__main__":
    main()
