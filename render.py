#!/usr/bin/env python3
"""Décryptage Express - rendu cloud (recette v6 validée).
Entrée : topic.json (collect.py). MODE=short (9:16) ou long (16:9). Sortie : out/<date>-<mode>/video.mp4 + meta.json.
Sans clé : script via Pollinations (gratuit), voix edge-tts, clips Mixkit (registre used_clips.json, jamais réutilisés)."""
import asyncio, time, glob, json, os, random, re, subprocess, sys, urllib.request, datetime as dt
_ca = os.path.expanduser("~/.ccr/ca-bundle.crt")
if os.path.exists(_ca):  # uniquement dans le bac à sable de test
    import certifi; certifi.where = lambda: _ca
HERE = os.path.dirname(os.path.abspath(__file__))
MODE = os.environ.get("MODE", "short"); SHORT = MODE == "short"
W, H = (1080, 1920) if SHORT else (1920, 1080)
VOICE = "fr-FR-VivienneMultilingualNeural"
STAMP = dt.datetime.now().strftime("%Y-%m-%d-%H%M")
OUT = os.path.join(HERE, "out", f"{STAMP}-{MODE}"); os.makedirs(OUT, exist_ok=True)
WORK = os.path.join(OUT, "w"); os.makedirs(WORK, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0"}
def sh(c): subprocess.run(c, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
def dur(f): return float(subprocess.check_output(f"ffprobe -v error -show_entries format=duration -of csv=p=0 '{f}'", shell=True))
def get(url, data=None, headers=None, t=120):
    return urllib.request.urlopen(urllib.request.Request(url, data=data, headers=headers or UA), timeout=t).read()

PROMPT = """Tu écris pour « Décryptage Express », média français sur l'IA. Voix off sans visage, texte écrit comme un grand média :
phrases longues et liées, connecteurs, aucun mot-étiquette (« verdict », « premier signal »), chiffres écrits en chiffres, tutoiement léger.
STRUCTURE OBLIGATOIRE : le champ « intro » est une vraie présentation : elle commence par la date du jour (« Nous sommes le … » avec la DATE DU JOUR fournie), puis annonce chaque sujet dans l'ordre
avec l'information brute : le fait, le chiffre clé s'il existe, et en une demi-phrase pourquoi on en parle. Sans « bonjour », sans « et si ».
Chaque bloc doit être riche en information : 1) le fait précis avec tous les chiffres, noms, montants des titres ; 2) la raison, pourquoi cela arrive ; 3) ce que cela change concrètement pour le spectateur. Pas de phrases vagues ni de remplissage.
STYLE CAPTIVANT ET PUISSANT : ouverture choc, phrases percutantes qui alternent courtes et longues, tension et enjeu (ce qu'on gagne, ce qu'on risque), chiffres mis en valeur, comparaisons concrètes qui parlent,
une chute marquante à la fin de chaque bloc, ton de journaliste passionné qui décrypte les coulisses, jamais de ton neutre ni scolaire. Ensuite « blocks » : UN bloc par sujet : chaque bloc entre DIRECTEMENT dans son sujet, SANS phrase de transition (elles sont ajoutées automatiquement), puis développe. Dernier bloc : conclusion + abonnement, sans transition non plus.
Si plusieurs sujets racontent la même affaire, fusionne-les en un seul bloc. Vocabulaire français riche et précis (synonymes, tournures variées, jargon du secteur expliqué simplement) :
ne répète jamais un même mot marquant, une même tournure ni une même formule d'un bloc à l'autre ; désigne les personnes et entreprises de façons différentes (nom, fonction, pronom).
N'utilise QUE les faits écrits dans les titres fournis : reformule-les, n'ajoute AUCUN chiffre, pourcentage ni date qui ne soit pas écrit dans les titres fournis (un chiffre inventé est une faute grave). Ne cite JAMAIS les sources ni les médias (pas de « selon », pas de nom de site) : à la place, explique le pourquoi, la raison de chaque fait, en t'appuyant uniquement sur ce que disent les titres (si la raison n'y est pas, explique l'enjeu pour le spectateur sans inventer de fait). Les sujets s'enchaînent comme un seul récit, sans « affaire à suivre ».
Les mots-clés vidéo de chaque bloc doivent représenter LITTÉRALEMENT son sujet (objet ou lieu concret : robot, microchip, laptop code, data center, smartphone, stock market screen),
jamais d'abstraction. Choisis-les UNIQUEMENT parmi cette liste : robot, laptop, server, code, stock-market, finance, business, data, smartphone, hacker, factory, satellite, laboratory, microscope, network, screen, keyboard, programming, drone, electronics, circuit-board, hologram, digital, technology. %s
Réponds UNIQUEMENT en JSON : {"intro":"texte de l'intro","intro_keywords":["3 mots-clés vidéo EN ANGLAIS"],"title":"titre viral à mots-clés, max 95 caractères","description":"2 phrases","hashtags":["#..."],
"blocks":[{"text":"narration","keywords":["3 mots-clés de recherche vidéo EN ANGLAIS, ex: server room"]}]}"""
FORMAT = ("FORMAT SHORT : intro de 20 à 30 mots, puis 1 à 2 blocs (UN sujet par bloc, développé à fond : fait, chiffres, raison, conséquence) de 45 à 60 mots chacun, 45 à 60 secondes au total, dernier bloc : « Abonne-toi pour ne rien perdre des décryptages »."
          if SHORT else "FORMAT LONG : intro de 70 à 100 mots, puis 9 à 12 blocs de 45 à 70 mots, un changement de sujet toutes les 1 à 2 minutes, dernier bloc : « Abonne-toi pour la prochaine vidéo, à bientôt »."
)

def merge_same(topics):
    """Fusionne les sujets qui parlent de la même affaire (mêmes noms propres) : aucune répétition d'un bloc à l'autre."""
    key = lambda t: set(re.findall(r"[A-ZÉ][\wéèï]+ [A-ZÉ][\wéèï]+", t["title"]))
    out = []
    for t in topics:
        k = key(t)
        for o in out:
            if k & key(o):
                o["articles"] = o["articles"] + [{"title": t["title"], "source": ""}] + t["articles"]; break
        else: out.append(dict(t, articles=list(t["articles"])))
    return out

def llm_script(topics):
    topics = merge_same(topics)
    facts = "\n".join(f"SUJET {i+1} : {t['title']}\n" + "\n".join(f"- {a['title']}" for a in t['articles'][:4]) for i, t in enumerate(topics))
    J = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]; M = ["", "janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
    n = dt.datetime.now(); facts = f"DATE DU JOUR : {J[n.weekday()]} {n.day}{'er' if n.day == 1 else ''} {M[n.month]} {n.year}\n\n" + facts
    msgs = [{"role": "system", "content": PROMPT % FORMAT}, {"role": "user", "content": facts}]
    key = os.environ.get("LLM_API_KEY")
    best = None
    for attempt in range(6):
        try:
            if key:
                base = (os.environ.get("LLM_BASE_URL") or "https://api.deepseek.com").rstrip("/")
                body = json.dumps({"model": os.environ.get("LLM_MODEL") or "deepseek-chat", "messages": msgs, "temperature": 0.5}).encode()
                out = json.loads(get(base + "/chat/completions", body, {"Content-Type": "application/json", "Authorization": "Bearer " + key}, 180))
            else:  # gratuit, sans clé
                body = json.dumps({"model": "openai-fast", "messages": msgs, "temperature": 0.5, "seed": random.randint(1, 10**6)}).encode()
                out = json.loads(get("https://text.pollinations.ai/openai", body, {"Content-Type": "application/json", **UA}, 180))
            txt = out["choices"][0]["message"]["content"]
            d = json.loads(re.search(r"\{.*\}", txt, re.S).group(0))
            assert d["blocks"] and all(b["text"] for b in d["blocks"]) and len(d.get("intro", "")) > 40
            nw = len(d["intro"].split()) + sum(len(b["text"].split()) for b in d["blocks"])
            TR = ["Premier dossier :", "Ensuite :", "Autre dossier chaud :", "Pendant ce temps :", "Plus loin :", "Autre info clé :", "Aussi :", "Dans un autre registre :", "Et ce n'est pas tout :", "À noter aussi :"]
            for k, bk in enumerate(d["blocks"][:-1]): bk["text"] = (TR[k] if k < len(TR) else "Aussi :") + " " + bk["text"]
            if len(d["blocks"]) > 2: d["blocks"][-2]["text"] = re.sub(r"^[^:]+:", "Dernier dossier :", d["blocks"][-2]["text"])
            d["blocks"] = [{"text": d["intro"], "keywords": d.get("intro_keywords") or d["blocks"][0].get("keywords", [])}] + d["blocks"]
            tgt = 150 if SHORT else 700
            if best is None or abs(nw - tgt) < best[0]: best = (abs(nw - tgt), d)
            assert (nw <= 210) if SHORT else (350 <= nw <= 1100), f"longueur {nw} mots hors cible"
            return d
        except Exception as e:
            print("script retry", e, file=sys.stderr); time.sleep(8)
    if best: return best[1]  # meilleur essai : la vidéo sort toujours
    sys.exit("script indisponible")

async def say(text, path):
    import edge_tts
    c = edge_tts.Communicate(text, VOICE, rate="+7%", boundary="WordBoundary"); words = []
    with open(path, "wb") as f:
        async for ch in c.stream():
            if ch["type"] == "audio": f.write(ch["data"])
            elif ch["type"] == "WordBoundary": words.append((ch["text"], ch["offset"] / 1e7, (ch["offset"] + ch["duration"]) / 1e7))
    cuts = [(words[i][2] + .05, words[i + 1][1] - .05) for i in range(len(words) - 1) if words[i + 1][1] - words[i][2] > .18]
    if cuts:  # silences raccourcis à 0,10 s (recette v6)
        segs, pos = [], 0.0
        for a, b in cuts: segs.append((pos, a)); pos = b
        segs.append((pos, None))
        fl = ";".join(f"[0:a]atrim=start={a:.3f}" + (f":end={b:.3f}" if b else "") + f",asetpts=PTS-STARTPTS[s{i}]" for i, (a, b) in enumerate(segs))
        fl += ";" + "".join(f"[s{i}]" for i in range(len(segs))) + f"concat=n={len(segs)}:v=0:a=1[o]"
        sh(f"ffmpeg -y -i '{path}' -filter_complex \"{fl}\" -map [o] '{path}.t.mp3'"); os.replace(path + ".t.mp3", path)
        words = [(w, s - sum(b - a for a, b in cuts if b <= s + 1e-6), e - sum(b - a for a, b in cuts if b <= s + 1e-6)) for w, s, e in words]
    return words

REG = os.path.join(HERE, "used_clips.json")
used = set(json.load(open(REG))) if os.path.exists(REG) else set()
BAN = ("santa", "christmas", "xmas", "gift", "holiday", "snow", "winter", "party", "wedding", "baby", "celebrat", "costume", "toy")
TECH = ["technology", "laptop", "server", "robot", "code", "stock-market", "business", "finance", "data", "smartphone", "hacker", "factory", "satellite",
        "laboratory", "microscope", "network", "screen", "keyboard", "programming", "drone", "electronics", "circuit-board", "hologram", "digital"]
_page = {}
def page_ids(slug, pg=1):
    if (slug, pg) in _page: return _page[(slug, pg)]
    ids = []
    for att in range(3):
        try:
            u = f"https://mixkit.co/free-stock-video/{slug}/" + (f"?page={pg}" if pg > 1 else "")
            html = get(u).decode("utf8", "ignore"); ids = list(dict.fromkeys(re.findall(r"assets\.mixkit\.co/videos/(\d+)/", html))); break
        except Exception as e:
            if "429" in str(e): time.sleep(20 * (att + 1))
            else: break
    time.sleep(1.0); _page[(slug, pg)] = ids; return ids
def block_clips(kws, need, off=0):
    cands = []
    def add(sg, pgs=6):
        for pg in range(1, pgs + 1):
            if len(cands) >= need: return
            ids = page_ids(sg, pg)
            if not ids: return
            cands.extend(i for i in ids if i not in used and i not in cands)
    for kw in kws:
        for sg in re.sub(r"[^a-z0-9]+", "-", kw.lower()).strip("-").split("-"):
            if sg in TECH: add(sg, 3)
        if len(cands) >= need: break
    for k in range(len(TECH)):
        if len(cands) >= need: break
        add(TECH[(off + k) % len(TECH)])
    if not cands:  # réserve épuisée : on reprend les plus anciens plutôt que d'échouer
        for k in range(len(TECH)):
            cands += [i for i in page_ids(TECH[(off + k) % len(TECH)]) if i not in cands]
            if len(cands) >= need: break
    got = []
    for i in cands:
        f = os.path.join(WORK, f"c{i}.mp4")
        try: open(f, "wb").write(get(f"https://assets.mixkit.co/videos/{i}/{i}-720.mp4", t=90)); got.append(f); used.add(i)
        except Exception: continue
        if len(got) >= need: break
    return got

def main():
    sys.path.insert(0, os.path.join(HERE, "assets"))
    if os.environ.get("PRESENTATION"):  # vidéo de présentation de la chaîne (script fixe, aucun appel LLM)
        script = json.load(open(os.path.join(HERE, "presentation.json" if SHORT else "presentation_long.json")))
        topics = [{"title": script["title"], "articles": [{"title": script["title"], "source": "Décryptage Express"}], "cluster": {"items": [], "tok": []}}]
    else:
        topic = json.load(open(os.path.join(HERE, "topic.json")))
        topics = topic.get("topics") or ([topic["topic"]] if topic.get("topic") else [])
        if topic.get("status") != "ok" or not topics: print("pas de sujet :", topic.get("reason")); return
        script = llm_script(topics[:2 if SHORT else 10])
    blocks = script["blocks"]
    voices = []
    for i, b in enumerate(blocks):
        p = os.path.join(WORK, f"v{i}.mp3"); words = asyncio.run(say(b["text"], p)); voices.append((p, words, dur(p)))
    GAP, LEAD = .14, 3.0 if SHORT else 5.0
    starts, t = [], LEAD
    for p, w, d in voices: starts.append(t); t += d + GAP
    total = t + 1.0
    # --- vidéo : plans de ~1,8 s (Short) / ~5 s (long), zoom lent, flash blanc au début de chaque sujet
    seg_len = 1.8 if SHORT else 5.0; nseg = int(total / seg_len) + 1
    nb = len(blocks); bounds = [0.0] + starts[1:] + [total + 9]
    blk = lambda x: max(i for i in range(nb) if x >= bounds[i] - 1e-6)
    seg_blk = [blk(k * seg_len) for k in range(nseg)]
    pools = {}
    for i in range(nb):
        need = max(2, seg_blk.count(i))
        pools[i] = block_clips(blocks[i].get("keywords", []), need, i * 3)
    allc = [c for i in range(nb) for c in pools[i]]
    if not allc: sys.exit("aucun clip")
    segs = []; cur = 0.0; cnt = {}
    for k in range(nseg):
        sd = min(seg_len, total - cur)
        if sd <= 0.05: break
        pool = pools[seg_blk[k]] or allc; j = cnt.get(seg_blk[k], 0); cnt[seg_blk[k]] = j + 1
        c = pool[j % len(pool)]; o = os.path.join(WORK, f"s{k:03d}.mp4"); fr = int(sd * 30) + 1
        z = f"zoompan=z='1.0+0.07*on/{fr}+0.10*exp(-on/6)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps=30"
        vf = f"fps=30,scale={int(W*1.25)}:{int(H*1.25)}:force_original_aspect_ratio=increase,crop={int(W*1.25)}:{int(H*1.25)},{z},eq=contrast=1.1:saturation=1.08:brightness=-0.03,vignette=PI/5"
        if any(abs(cur - s) < .01 or (cur <= s < cur + sd) for s in starts): vf += ",fade=t=in:st=0:d=0.14:color=white"
        sh(f"ffmpeg -y -stream_loop -1 -ss {0.3 + (j // len(pool)) * 4.2:.2f} -t {sd + .2:.2f} -i '{c}' -vf \"{vf}\" -t {sd:.3f} -r 30 -pix_fmt yuv420p -c:v libx264 -preset veryfast -crf 21 '{o}'")
        segs.append(o); cur += sd
    open(os.path.join(WORK, "list.txt"), "w").write("\n".join(f"file '{os.path.basename(s)}'" for s in segs))
    sh(f"ffmpeg -y -f concat -safe 0 -i '{WORK}/list.txt' -c copy '{WORK}/video.mp4'")
    # --- sous-titres : 2 mots (Short) / 3 mots (long), mot-clé en jaune, jamais superposés
    ts = lambda x: f"{int(x//3600)}:{int(x%3600//60):02d}:{x%60:05.2f}"
    n = 2 if SHORT else 3; fs = 120 if SHORT else 92
    head = f"[Script Info]\nScriptType: v4.00+\nPlayResX: {W}\nPlayResY: {H}\n[V4+ Styles]\nFormat: Name,Fontname,Fontsize,PrimaryColour,OutlineColour,BackColour,Bold,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV\nStyle: D,Roboto,{fs},&H00FFFFFF,&H00000000,&H80000000,1,1,8,3,5 if False else 2,80,80,{int(H*0.38) if SHORT else 120}\n[Events]\nFormat: Layer,Start,End,Style,Text"
    head = head.replace("5 if False else 2", "2")
    stop = set("le la les un une des de du et en au aux à a ce ces sur pour par avec dans qui que est sont il elle the of to in".split())
    ev = []; srt = []; prev = None; stat_ev = []; blk_times = []
    def clean(t): return re.sub(r"\s+", " ", t).strip()
    for (p, words, d), st, b in zip(voices, starts, blocks):
        toks = clean(b["text"]).split(" ")
        if len(words) != len(toks):  # mots manquants dans la synchro : on répartit selon la longueur, aucun mot n'est perdu
            tot = sum(len(x) + 1 for x in toks); t0 = 0.0; w2 = []
            for x in toks:
                dd = d * (len(x) + 1) / tot; w2.append((x, t0, t0 + dd)); t0 += dd
            words = w2
        else: words = [(tk, w[1], w[2]) for tk, w in zip(toks, words)]
        import inserts
        for si_, sv_, su_, sl_ in inserts.find_stats(toks):
            if si_ < len(words): stat_ev.append((st + words[si_][1], sv_, su_, sl_))
        blk_times.append((st, d))
        gs, cur = [], []  # un groupe ne déborde jamais sur la phrase suivante : fin de phrase = fin du sous-titre
        for w in words:
            cur.append(w)
            if len(cur) >= n or re.search(r"[.!?…:]$", w[0]): gs.append(cur); cur = []
        if cur: gs.append(cur)
        prev = None
        for gi, g in enumerate(gs):
            s0 = st + g[0][1]; e0 = st + gs[gi + 1][0][1] - .03 if gi + 1 < len(gs) else st + g[-1][2] + .15
            e0 = max(e0, s0 + .1)
            txt = " ".join(("{\\c&H00D7FF&}" + w[0].upper() + "{\\c&HFFFFFF&}") if (len(w[0]) > 6 and w[0].lower().strip(",.;:!?") not in stop and (gi * n + g.index(w)) % 3 == 0) else w[0].upper() for w in g)
            yb = H // 2
            mx = max(len(w[0]) for w in g); tot = sum(len(w[0]) for w in g) + len(g) - 1
            fsz = int(min(fs * 1.3, .9 * W / (.62 * max(tot, 1))))
            rot = random.choice([-3, -2, 0, 2, 3])
            fx = ("{\\an5\\pos(%d,%d)\\fs%d\\bord12\\shad5\\blur1.5\\frz%d\\fscx55\\fscy55\\alpha&H80&"
                  "\\t(0,90,\\fscx118\\fscy118\\alpha&H00&)\\t(90,170,\\fscx100\\fscy100)}" % (W // 2, yb, fsz, rot))
            ev.append(f"Dialogue: 0,{ts(s0)},{ts(e0)},D,{fx}{txt}")
            prev = " ".join(w[0].upper() for w in g)
            srt.append((s0, e0, " ".join(w[0] for w in g)))
    open(os.path.join(WORK, "cap.ass"), "w", encoding="utf8").write(head + "\n" + "\n".join(ev))
    fm = lambda x: f"{int(x//3600):02d}:{int(x%3600//60):02d}:{int(x%60):02d},{int(x*1000)%1000:03d}"
    open(os.path.join(OUT, "subs.srt"), "w", encoding="utf8").write("\n".join(f"{i+1}\n{fm(a)} --> {fm(b)}\n{t}\n" for i, (a, b, t) in enumerate(srt)))
    # --- audio : voix + musique cinématique basse (sidechain) + whoosh très discrets, loudnorm
    ins = " ".join(f"-i '{p}'" for p, _, _ in voices)
    fl = "".join(f"[{i}:a]adelay={int(s*1000)}|{int(s*1000)},volume=1.3[a{i}];" for i, s in enumerate(starts))
    fl += "".join(f"[a{i}]" for i in range(len(voices))) + f"amix=inputs={len(voices)}:normalize=0,apad,atrim=0:{total:.2f}[v]"
    sh(f"ffmpeg -y {ins} -filter_complex \"{fl}\" -map [v] -ar 44100 '{WORK}/voice.wav'")
    sys.path.insert(0, os.path.join(HERE, "assets")); import musicgen
    mus = os.path.join(WORK, "music.wav"); musicgen.make(mus, total + 1, random.randrange(10**6))
    ctat = max(total - 6.0, LEAD + 2); clk = int((ctat + 1.55) * 1000)
    import sfx  # ouverture, fin, 3 transitions « switch » + 3 « whoosh » tirées au hasard, cloche « cling cling » au clic sur S'abonner
    cands = [k * seg_len for k in range(1, nseg) if 2.5 <= k * seg_len <= ctat - 1.0]
    random.shuffle(cands); picks = []
    for c in cands:
        if all(abs(c - q) >= 1.2 for q in picks): picks.append(c)
        if len(picks) == 6: break
    picks.sort(); kinds = ["switch"] * 3 + ["whoosh"] * 3; random.shuffle(kinds)
    sfx.build(os.path.join(WORK, "sfx.wav"), total, list(zip(picks, kinds)), ctat, clk, random.randrange(10**6))
    sh(f"""ffmpeg -y -i '{WORK}/voice.wav' -i '{WORK}/sfx.wav' -stream_loop -1 -i '{mus}' -filter_complex "[0:a]asplit=2[k][v1];[2:a]atrim=0:{total:.2f},volume=0.22,afade=t=in:d=1,afade=t=out:st={total-3:.2f}:d=3[m];[m][k]sidechaincompress=threshold=0.02:ratio=10:attack=15:release=350[md];[md][v1][1:a]amix=inputs=3:normalize=0:duration=longest[mx];[mx]loudnorm=I=-14:TP=-0.8:LRA=11[o]" -map "[o]" -t {total:.2f} -ar 44100 '{WORK}/audio.wav'""")
    sys.path.insert(0, os.path.join(HERE, "assets")); import overlays
    ov = os.path.join(WORK, "ov"); overlays.build(ov, SHORT)
    cx, cy = ((W - 820) // 2, int(H * 0.10)) if SHORT else (W - 660, 60)
    import inserts
    inserts.intro(os.path.join(WORK, "intro"), W, H); inserts.outro(os.path.join(WORK, "outro"), W, H)
    cw, chh = (760, 330) if SHORT else (560, 250); px, py = ((W - cw) // 2, int(H * 0.115)) if SHORT else (60, 60)
    pw, ph = (760, 428) if SHORT else (560, 315); ppx, ppy = ((W - pw) // 2, int(H * 0.115)) if SHORT else (60, 60)
    cards = []; busy = [(0, 2.8), (ctat - .4, ctat + 3.9)]  # intro et animation S'abonner : zone réservée
    free = lambda a, b: all(b <= x0 or a >= x1 for x0, x1 in busy)
    for k, (ts_, v_, u_, l_) in enumerate(sorted(stat_ev)[:4]):
        if free(ts_ - .2, ts_ + 3.4):
            dd = os.path.join(WORK, f"stat{k}"); inserts.stat_card(dd, cw, chh, v_, u_, l_); cards.append((max(ts_ - .2, 0), dd, px, py)); busy.append((ts_ - .2, ts_ + 3.4))
    allclips = [c for i in range(nb) for c in pools[i]]; nimg = 0
    for bi, (bst, bd) in enumerate(blk_times):
        if nimg >= (4 if SHORT else 8): break
        t0 = bst + max(.8, bd * .5)
        if t0 + 2.6 < total - 1.5 and free(t0 - .2, t0 + 2.6) :
            src = os.path.join(WORK, f"pip{bi}.jpg")
            try:
                pc = [c for c in block_clips(blocks[bi].get("keywords", []), 1, bi * 3 + 1) if c not in allclips]  # image dédiée au sujet du bloc, jamais un plan de la vidéo
                if not pc: continue
                sh(f"ffmpeg -y -v error -ss 1.0 -i '{pc[0]}' -frames:v 1 -q:v 3 '{src}'")
                dd = os.path.join(WORK, f"pip{bi}"); inserts.pip_card(dd, pw, ph, src); cards.append((t0, dd, ppx, ppy)); busy.append((t0 - .2, t0 + 2.6)); nimg += 1
            except Exception as e: print("pip ignorée :", e)
    fc = (f"[0:v]ass='{WORK}/cap.ass'[b];[2:v]format=rgba,setpts=PTS-STARTPTS+0.1/TB[l];[3:v]format=rgba,setpts=PTS-STARTPTS+{ctat:.2f}/TB[c];[4:v]format=rgba,setpts=PTS-STARTPTS/TB[it];"
          f"[b][l]overlay=x=(W-w)/2:y=(H-h)/2-80:eof_action=pass[b2];[b2][c]overlay=x={cx}:y={cy}:eof_action=pass[cur];")
    for k, (t0_, dd, x_, y_) in enumerate(cards):
        fc += f"[{5 + k}:v]format=rgba,setpts=PTS-STARTPTS+{t0_:.2f}/TB[k{k}];[cur][k{k}]overlay=x={x_}:y={y_}:eof_action=pass[cur];"
    no = 5 + len(cards)
    fc += f"[{no}:v]format=rgba,setpts=PTS-STARTPTS+{total-1.7:.2f}/TB[ot];[cur][it]overlay=0:0:eof_action=pass[o0];[o0][ot]overlay=0:0:eof_action=repeat[o1];[o1]fade=t=out:st={total-0.5:.2f}:d=0.5:color=black[o]"
    card_in = "".join(f" -framerate 30 -i '{dd}/%03d.png'" for _, dd, _, _ in cards)
    sh(f"""ffmpeg -y -i '{WORK}/video.mp4' -i '{WORK}/audio.wav' -framerate 30 -i '{ov}/logo_in/%03d.png' -framerate 30 -i '{ov}/cta/%03d.png' -framerate 30 -i '{WORK}/intro/%03d.png'{card_in} -framerate 30 -i '{WORK}/outro/%03d.png' -filter_complex "{fc}" -map "[o]" -map 1:a -c:v libx264 -preset veryfast -crf 21 -pix_fmt yuv420p -c:a aac -b:a 192k -t {total:.2f} -movflags +faststart '{OUT}/video.mp4'""")
    import seo, cover
    S = seo.build(script, topics, MODE, [b["text"] for b in blocks])
    cover.make(f"{WORK}/video.mp4", script["title"], "ACTU IA" if SHORT else "DÉCRYPTAGE IA", f"{OUT}/cover.jpg", SHORT)
    if SHORT:  # la couverture charte devient la toute première image : TikTok/Instagram/YouTube la prennent comme vignette automatique
        try:
            sh(f"ffmpeg -y -i '{OUT}/video.mp4' -i '{OUT}/cover.jpg' -filter_complex \"[1:v]scale=1080:1920,format=yuv420p[c];[0:v][c]overlay=0:0:enable='lt(n,3)'[o]\" -map [o] -map 0:a -c:v libx264 -preset veryfast -crf 21 -pix_fmt yuv420p -c:a copy -movflags +faststart '{OUT}/v2.mp4' && mv '{OUT}/v2.mp4' '{OUT}/video.mp4'")
        except Exception as e: print("cover 1re image ignorée", e, file=sys.stderr)
    json.dump({**S, "mode": MODE, "duration": round(total, 1), "language": "fr", "category": "Science et technologie", "ai_label": True,
               "topics": [t["title"] for t in topics]}, open(os.path.join(OUT, "meta.json"), "w"), ensure_ascii=False, indent=2)
    json.dump(sorted(used), open(REG, "w"))
    print("OK", OUT, round(total, 1), "s")
main()
