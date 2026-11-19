#!/usr/bin/env python3
"""Décryptage Express - étape 2 : script, voix, montage, extraits.

Lit topic.json (créé par collect.py). Écrit dans OUT_DIR/AAAA-MM-JJ/ :
  long.mp4 (16:9), short_1..3.mp4 (9:16), meta.json (titre, description, hashtags).
Réglages dans config.env (même dossier). MOCK=1 : essai sans clé ni voix.
Dépendances : Python 3.10+, ffmpeg, Pillow, edge-tts (pip install pillow edge-tts).
"""
import json, os, re, shutil, subprocess, sys, urllib.parse, urllib.request
from PIL import Image, ImageDraw, ImageEnhance, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))


def load_env():
    env = dict(os.environ)
    p = os.path.join(HERE, "config.env")
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.strip().split("=", 1)
                env.setdefault(k.strip(), v.strip().strip('"'))
    return env


ENV = load_env()
MOCK = ENV.get("MOCK") == "1"
VOICE = ENV.get("VOICE", "fr-FR-RemyMultilingualNeural")
OUT_DIR = ENV.get("OUT_DIR", os.path.join(HERE, "out"))
FFMPEG = ENV.get("FFMPEG", "ffmpeg")
BRAND = "decryptageexpress.com"

PROMPT = """Tu écris pour « Décryptage Express », média français sur les robots humanoïdes et l'IA.
Écris le script d'une vidéo de 4 à 5 minutes (environ 600 à 750 mots), ton clair, simple, factuel,
voix off sans visage. RÈGLES STRICTES : utilise UNIQUEMENT les faits présents dans les titres et
sources fournis ci-dessous ; n'invente aucun chiffre, citation, date ni nom ; si une information
manque, dis-le franchement (« les détails ne sont pas encore connus ») ; cite les sources à voix
haute (« selon L'Usine Digitale »). Structure : accroche forte, contexte, ce qui change, limites et
questions ouvertes, conclusion + invitation à s'abonner.
Réponds UNIQUEMENT en JSON : {"title": "...(max 90 car., mots-clés robots humanoïdes)",
"description": "2-3 phrases", "hashtags": ["#..."] (8 à 12, bien nichés),
"scenes": [{"narration": "40 à 70 mots", "onscreen": "6 mots max", "keywords": ["3 termes de recherche EN ANGLAIS pour des photos libres, ex: humanoid robot factory"], "highlight": true|false}]}
avec 9 à 12 scènes ; 3 scènes seulement en highlight=true (les plus percutantes, dont l'accroche)."""

MOCK_SCRIPT = {
    "title": "Essai : robot humanoïde Atlas dans les usines",
    "description": "Vidéo d'essai du pipeline.",
    "hashtags": ["#robotshumanoides", "#atlas", "#bostondynamics"],
    "scenes": [
        {"narration": "Voici un essai de la chaîne de production automatique de Décryptage Express. " * 3,
         "onscreen": "Essai du pipeline", "keywords": ["humanoid robot", "robot factory", "artificial intelligence"], "highlight": True},
        {"narration": "Cette scène vérifie le montage, les titres à l'écran et la synchronisation. " * 3,
         "onscreen": "Montage et titres", "keywords": ["robot arm", "technology lab"], "highlight": False},
        {"narration": "Dernière scène : abonne-toi pour une nouvelle vidéo chaque jour à dix heures. " * 3,
         "onscreen": "Abonne-toi", "keywords": ["robot hand", "futuristic city"], "highlight": True},
    ],
}


def llm_script(topic):
    key = ENV.get("LLM_API_KEY")
    if not key:
        sys.exit("LLM_API_KEY manquante dans config.env")
    base = ENV.get("LLM_BASE_URL", "https://api.deepseek.com").rstrip("/")
    model = ENV.get("LLM_MODEL", "deepseek-chat")
    facts = "\n".join(f"- {a['title']} (source : {a['source']}, {a['published'][:10]})"
                      for a in topic["articles"])
    body = json.dumps({"model": model, "temperature": 0.4,
                       "response_format": {"type": "json_object"},
                       "messages": [{"role": "system", "content": PROMPT},
                                    {"role": "user", "content": f"Sujet : {topic['title']}\nFaits disponibles :\n{facts}"}]}).encode()
    req = urllib.request.Request(base + "/chat/completions", data=body,
                                 headers={"Content-Type": "application/json", "Authorization": "Bearer " + key})
    out = json.load(urllib.request.urlopen(req, timeout=180))
    txt = out["choices"][0]["message"]["content"]
    return json.loads(re.search(r"\{.*\}", txt, re.S).group(0))


def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def duration(path):
    r = subprocess.run([FFMPEG.replace("ffmpeg", "ffprobe"), "-v", "error", "-show_entries",
                        "format=duration", "-of", "csv=p=0", path], capture_output=True, text=True)
    return float(r.stdout.strip())


def voice(text, path):
    if MOCK:
        secs = max(3, len(text.split()) / 2.6)
        run([FFMPEG, "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", f"{secs:.2f}",
             "-c:a", "libmp3lame", path])
        return
    run([sys.executable, "-m", "edge_tts", "--voice", VOICE, "--text", text, "--write-media", path])


def font(size):
    for p in ["C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/arialbd.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


BEAT = 1.5  # secondes entre deux changements d'image
PALETTES = [((6, 12, 40), (0, 200, 255)), ((30, 8, 40), (255, 90, 180)), ((8, 32, 30), (60, 255, 170)),
            ((38, 22, 6), (255, 190, 40)), ((10, 10, 10), (255, 255, 255)), ((8, 20, 48), (120, 140, 255))]


def pexels(keyword, w, h, work):
    key = ENV.get("PEXELS_API_KEY")
    if not key or MOCK:
        return None
    safe = re.sub(r"\W+", "_", keyword)
    path = os.path.join(work, f"px_{safe}_{w}.jpg")
    if os.path.exists(path):
        return path
    try:
        o = "landscape" if w > h else "portrait"
        url = "https://api.pexels.com/v1/search?per_page=8&orientation=" + o + "&query=" + urllib.parse.quote(keyword)
        res = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"Authorization": key}), timeout=30))
        ph = res["photos"][hash(keyword + str(len(os.listdir(work)))) % len(res["photos"])]
        urllib.request.urlretrieve(ph["src"]["large2x"], path)
        return path
    except Exception:
        return None


def wrap(px, text, f, maxw):
    lines, line = [], ""
    for wd in text.split():
        t = (line + " " + wd).strip()
        if px.textlength(t, font=f) < maxw:
            line = t
        else:
            lines.append(line); line = wd
    lines.append(line)
    return lines


def beat_card(path, w, h, caption, n, progress, source_line, photo=None):
    bg, accent = PALETTES[n % len(PALETTES)]
    if photo:
        im = Image.open(photo).convert("RGB")
        k = max(w / im.width, h / im.height)
        im = im.resize((int(im.width * k) + 1, int(im.height * k) + 1))
        l, t = (im.width - w) // 2, (im.height - h) // 2
        img = ImageEnhance.Brightness(im.crop((l, t, l + w, t + h))).enhance(0.5)
    else:
        img = Image.new("RGB", (w, h))
        d0 = ImageDraw.Draw(img)
        for y in range(h):
            c = y / h
            d0.line([(0, y), (w, y)], fill=tuple(int(b + 34 * c) for b in bg))
        d0.ellipse([w * (0.1 + 0.15 * (n % 4)), h * 0.12, w * (0.1 + 0.15 * (n % 4)) + w * 0.5, h * 0.12 + w * 0.5],
                   outline=accent, width=6)
    px = ImageDraw.Draw(img)
    px.rectangle([0, 0, w, 14 if w > h else 20], fill=accent)
    f = font(int(w * (0.07 if w > h else 0.095)))
    lines = wrap(px, caption.upper(), f, w * 0.84)
    lh = int(f.size * 1.2)
    y0 = int(h * (0.5 if n % 2 == 0 else 0.62)) - lh * len(lines) // 2
    for i, l in enumerate(lines):
        tw = px.textlength(l, font=f)
        px.text(((w - tw) / 2, y0 + i * lh), l, font=f, fill=(255, 255, 255), stroke_width=max(4, w // 300), stroke_fill=(0, 0, 0))
    small = font(int(w * (0.022 if w > h else 0.04)))
    px.text((int(w * 0.05), h - int(h * 0.075)), BRAND, font=small, fill=accent)
    if source_line:
        maxw = w * 0.5 if w > h else w * 0.9
        while px.textlength(source_line, font=small) > maxw and "," in source_line:
            source_line = source_line.rsplit(",", 1)[0]
        if w <= h:
            px.text((int(w * 0.05), h - int(h * 0.135)), source_line, font=small, fill=(200, 210, 220))
        else:
            sw = px.textlength(source_line, font=small)
            px.text((w - sw - int(w * 0.05), h - int(h * 0.075)), source_line, font=small, fill=(200, 210, 220))
    bw = int((w - 2 * int(w * 0.05)) * progress)
    px.rectangle([int(w * 0.05), h - int(h * 0.1), int(w * 0.05) + bw, h - int(h * 0.1) + 6], fill=accent)
    img.save(path)


def render_scene_beats(sc, i, aud, out, w, h, work, src, prog0, prog1, counter):
    dur = duration(aud)
    nb = max(1, round(dur / BEAT))
    words = sc["narration"].split()
    per = max(1, round(len(words) / nb))
    chunks = [" ".join(words[k:k + per]) for k in range(0, len(words), per)][:nb] or [sc["onscreen"]]
    while len(chunks) < nb:
        chunks.append(sc["onscreen"])
    kws = sc.get("keywords") or []
    lst = os.path.join(work, f"b{w}_{i}.txt")
    lines = []
    for j in range(nb):
        photo = pexels(kws[j % len(kws)], w, h, work) if kws else None
        p = os.path.join(work, f"b{w}_{i}_{j}.png")
        beat_card(p, w, h, chunks[j], counter[0], prog0 + (prog1 - prog0) * (j + 1) / nb, "Sources : " + src, photo)
        counter[0] += 1
        lines.append(f"file '{os.path.basename(p)}'\nduration {dur / nb:.3f}\n")
    lines.append(f"file '{os.path.basename(p)}'\n")
    open(lst, "w", encoding="utf-8").write("".join(lines))
    run([FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", lst, "-i", aud, "-vf", f"fps=25,scale={w}:{h},format=yuv420p",
         "-c:v", "libx264", "-preset", ENV.get("PRESET", "veryfast"), "-c:a", "aac", "-b:a", "160k", "-ar", "44100",
         "-shortest", out])


def concat(parts, out, work):
    lst = os.path.join(work, "list.txt")
    open(lst, "w", encoding="utf-8").write("".join(f"file '{os.path.basename(p)}'\n" for p in parts))
    run([FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out])


def main():
    topic_doc = json.load(open(os.path.join(HERE, "topic.json"), encoding="utf-8"))
    if topic_doc["status"] != "ok":
        print("Pas de vidéo aujourd'hui :", topic_doc["reason"]); return
    topic = topic_doc["topic"]
    script = MOCK_SCRIPT if MOCK else llm_script(topic)
    day = topic_doc["date"]
    out = os.path.join(OUT_DIR, day); work = os.path.join(out, "_tmp")
    os.makedirs(work, exist_ok=True)
    scenes = script["scenes"]
    src = ", ".join(sorted({a["source"] for a in topic["articles"]})[:4])
    clips = {"long": [], "short": {}}
    n = len(scenes)
    counter = [0]
    for i, sc in enumerate(scenes):
        aud = os.path.join(work, f"a{i}.mp3")
        voice(sc["narration"], aud)
        for fmt, (w, h) in {"long": (1920, 1080), "short": (1080, 1920)}.items():
            if fmt == "short" and not sc.get("highlight"):
                continue
            mp4 = os.path.join(work, f"{fmt}{i}.mp4")
            render_scene_beats(sc, i, aud, mp4, w, h, work, src, i / n, (i + 1) / n, counter)
            if fmt == "long":
                clips["long"].append(mp4)
            else:
                clips["short"][i] = mp4
    concat(clips["long"], os.path.join(out, "long.mp4"), work)
    for k, (i, p) in enumerate(list(clips["short"].items())[:3], 1):
        shutil.copy(p, os.path.join(out, f"short_{k}.mp4"))
    tags = " ".join(script["hashtags"])
    desc = (script["description"] + "\n\nSources : " + ", ".join(sorted({a["source"] for a in topic["articles"]})[:6]) +
            " (articles du " + day + ")\n\nVidéo produite avec l'aide de l'IA (voix de synthèse). " + tags)
    json.dump({"date": day, "title": script["title"], "description": desc, "hashtags": script["hashtags"],
               "long": "long.mp4", "shorts": [f"short_{k}.mp4" for k in range(1, len(clips['short']) + 1)][:3],
               "ai_content": True}, open(os.path.join(out, "meta.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    shutil.rmtree(work, ignore_errors=True)
    print("OK ->", out, f"({duration(os.path.join(out, 'long.mp4')):.0f}s)")


if __name__ == "__main__":
    main()
