"""Blog statique Décryptage Express (docs/) : un article par vidéo longue, vidéo YouTube intégrée, design 2026.
Usage : python blog.py <dossier_video>   (ajoute l'article)   |   python blog.py --rebuild   (régénère tout + retrouve les vidéos YouTube)"""
import sys, os, json, html, re, glob, datetime, urllib.request
BASE = os.environ.get("BLOG_URL", "https://josyei.github.io/decryptage-express-auto")
CH = "UCUwq8QxrO-DulXvTwH2lT0w"
NET = [("YouTube", f"https://www.youtube.com/channel/{CH}?sub_confirmation=1", "#ff3b3b"),
       ("TikTok", "https://www.tiktok.com/@decryptageexpress", "#25f4ee"),
       ("Instagram", "https://www.instagram.com/decryptageexpress/", "#ff5fa2"),
       ("Facebook", "https://www.facebook.com/profile.php?id=61596391229000", "#4c8dff")]
esc = html.escape
norm = lambda s: re.sub(r"[^a-z0-9]+", " ", s.lower().encode("ascii", "ignore").decode()).strip()

def yt_index():
    try:
        x = urllib.request.urlopen(f"https://www.youtube.com/feeds/videos.xml?channel_id={CH}", timeout=20).read().decode()
        return [(norm(t), v) for v, t in re.findall(r"<yt:videoId>([^<]+)</yt:videoId>.*?<title>([^<]+)</title>", x, re.S)]
    except Exception as e:
        print("RSS indisponible", e); return []

def sections(desc):
    out = []
    for p in desc.split("\n\n"):
        p = p.strip()
        if not p or re.match(r"^(⏰|📩|✉️|Contenu réalisé|🔔|👇|🔑|#)", p): continue
        lines = p.split("\n"); head = ""
        if re.match(r"^[^\w\s•]", lines[0]) and len(lines[0]) < 60 and len(lines) > 1: head = lines.pop(0)
        out.append((head, lines))
    return out

def render_body(secs):
    h = ""
    for head, lines in secs:
        li = [l[1:].strip() for l in lines if l.strip().startswith("•")]
        rest = [l for l in lines if not l.strip().startswith("•")]
        h += '<section class="card reveal">' + (f"<h2>{esc(head)}</h2>" if head else "")
        if rest: h += "<p>" + "<br>".join(esc(l) for l in rest) + "</p>"
        if li: h += "<ul>" + "".join(f"<li>{esc(x)}</li>" for x in li) + "</ul>"
        h += "</section>"
    return h

CSS = """*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;font-family:Inter,system-ui,Segoe UI,Roboto,sans-serif;background:#050b1f;color:#e8f1ff;line-height:1.7;overflow-x:hidden}
.bg{position:fixed;inset:0;z-index:-1;background:radial-gradient(60% 50% at 20% 10%,#0e3a8a55,transparent),radial-gradient(50% 40% at 85% 20%,#00d4ff33,transparent),#050b1f}
.bg:after{content:"";position:absolute;inset:-50%;background:conic-gradient(from 0deg,#00d4ff10,#2b6cff14,#00d4ff10);animation:spin 40s linear infinite;filter:blur(80px)}
@keyframes spin{to{transform:rotate(360deg)}}
header{display:flex;align-items:center;justify-content:space-between;padding:18px 5vw;position:sticky;top:0;backdrop-filter:blur(14px);background:#050b1fb0;border-bottom:1px solid #ffffff14;z-index:5}
.brand{display:flex;align-items:center;gap:12px;color:#fff;text-decoration:none;font-weight:800;letter-spacing:.3px}.brand img{width:40px;height:40px;border-radius:12px;box-shadow:0 0 22px #00d4ff66}
.nets{display:flex;gap:10px;flex-wrap:wrap}.net{padding:9px 16px;border-radius:999px;border:1px solid var(--c);color:var(--c);text-decoration:none;font-weight:700;font-size:.9rem;transition:.25s}.net:hover{background:var(--c);color:#050b1f;transform:translateY(-2px);box-shadow:0 8px 24px color-mix(in srgb,var(--c) 40%,transparent)}
main{max-width:980px;margin:0 auto;padding:0 5vw 80px}
.hero{padding:70px 0 30px;text-align:center}.hero h1{font-size:clamp(2.2rem,6vw,4rem);line-height:1.08;margin:0 0 16px;background:linear-gradient(90deg,#fff,#6fe3ff,#4c8dff,#fff);background-size:250% 100%;-webkit-background-clip:text;background-clip:text;color:transparent;animation:shine 8s linear infinite}
@keyframes shine{to{background-position:250% 0}}.hero p{color:#a9c4ee;font-size:1.15rem;max-width:640px;margin:0 auto 26px}
.pill{display:inline-block;padding:6px 14px;border-radius:999px;background:#00d4ff1c;color:#6fe3ff;font-weight:700;font-size:.8rem;letter-spacing:.08em;margin-bottom:18px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:22px;margin-top:30px}
.post{display:block;text-decoration:none;color:inherit;border-radius:22px;padding:26px;background:linear-gradient(160deg,#0d1f4a99,#0a1433aa);border:1px solid #ffffff16;transition:.3s;position:relative;overflow:hidden}
.post:hover{transform:translateY(-6px);border-color:#00d4ff88;box-shadow:0 18px 50px #00d4ff22}.post small{color:#6fe3ff;font-weight:700}.post h3{margin:10px 0;font-size:1.15rem;line-height:1.3}.post p{color:#a9c4ee;margin:0;font-size:.95rem}
.card{background:#0b1a40a8;border:1px solid #ffffff14;border-radius:20px;padding:26px 28px;margin:22px 0;backdrop-filter:blur(6px)}.card h2{margin:0 0 12px;font-size:1.25rem;color:#6fe3ff}.card ul{padding-left:20px;margin:0}.card li{margin:8px 0}
.video{position:relative;padding-top:56.25%;border-radius:22px;overflow:hidden;box-shadow:0 24px 70px #00d4ff2e;border:1px solid #00d4ff55;margin:26px 0}.video iframe{position:absolute;inset:0;width:100%;height:100%;border:0}
.cta{text-align:center;margin:40px 0}.cta h2{margin:0 0 14px}.reveal{opacity:0;transform:translateY(24px);transition:.7s}.reveal.on{opacity:1;transform:none}
footer{text-align:center;color:#6f88b8;padding:40px 5vw;border-top:1px solid #ffffff12;font-size:.9rem}
@media(prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}.reveal{opacity:1;transform:none}}"""
JS = "<script>const o=new IntersectionObserver(e=>e.forEach(x=>x.isIntersecting&&x.target.classList.add('on')),{threshold:.12});document.querySelectorAll('.reveal').forEach(e=>o.observe(e))</script>"
netlinks = lambda: "".join(f'<a class="net" style="--c:{c}" href="{u}" target="_blank" rel="noopener">{n}</a>' for n, u, c in NET)
def shell(title, desc, canon, body, root):
    return f"""<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)}</title>
<meta name="description" content="{esc(desc[:155])}"><link rel="canonical" href="{canon}"><link rel="icon" href="{root}assets/logo.jpg"><meta property="og:title" content="{esc(title)}"><meta property="og:image" content="{BASE}/assets/logo.jpg">
<link rel="alternate" type="application/rss+xml" href="{root}feed.xml"><style>{CSS}</style></head><body><div class="bg"></div>
<header><a class="brand" href="{root}"><img src="{root}assets/logo.jpg" alt="">Décryptage Express</a><nav class="nets">{netlinks()}</nav></header><main>{body}</main>
<footer>© 2026 Décryptage Express · L'actu IA, tech et bourse décryptée chaque jour · Contenu réalisé avec l'aide de l'IA</footer>{JS}</body></html>"""

def add(D):
    m = json.load(open(os.path.join(D, "meta.json")))
    if m.get("mode") != "long": return
    day = re.search(r"(\d{4}-\d{2}-\d{2})", D).group(1)
    title = m["title"].split(" | ")[0].strip()
    slug = day + "-" + re.sub(r"[^a-z0-9]+", "-", norm(title))[:50].strip("-")
    os.makedirs("docs/data", exist_ok=True)
    json.dump({"slug": slug, "title": title, "full_title": m["title"], "date": day, "desc": m["description"].split("🔑 MOTS-CLÉS")[0].strip(), "yt": None},
              open(f"docs/data/{slug}.json", "w", encoding="utf-8"), ensure_ascii=False)

def rebuild():
    idx = yt_index(); items = []; print("flux YouTube :", len(idx), "vidéos")
    for f in glob.glob("docs/data/*.json"):
        a = json.load(open(f, encoding="utf-8"))
        if not a.get("yt") and not a.get("tt"):
            k = norm(a["full_title"])
            kw = set(k.split()); best = (0, None)
            for t, v in idx:
                tw = set(t.split()); j = len(kw & tw) / max(1, len(kw | tw))
                if j > best[0]: best = (j, v)
            print("match", round(best[0], 2), a["title"][:40])
            if best[0] >= 0.45: a["yt"] = best[1]
            json.dump(a, open(f, "w", encoding="utf-8"), ensure_ascii=False)
        items.append(a)
    items.sort(key=lambda a: a["date"], reverse=True); items = items[:200]
    os.makedirs("docs/articles", exist_ok=True)
    for a in items:
        sec = sections(a["desc"]); summ = (sec[0][1][0] if sec and sec[0][1] else a["title"])
        a["summary"] = summ
        vid = (f'<div class="reveal" style="display:flex;justify-content:center;margin:26px 0"><blockquote class="tiktok-embed" cite="https://www.tiktok.com/@decryptageexpress.com/video/{a["tt"]}" data-video-id="{a["tt"]}" style="max-width:605px;min-width:325px"><section></section></blockquote><script async src="https://www.tiktok.com/embed.js"></script></div>' if a.get("tt") else
               f'<div class="video reveal"><iframe src="https://www.youtube.com/embed/{a["yt"]}" title="{esc(a["title"])}" allowfullscreen loading="lazy"></iframe></div>' if a.get("yt")
               else f'<div class="video reveal"><iframe src="https://www.youtube.com/embed/videoseries?list=UU{CH[2:]}" title="Dernières vidéos" allowfullscreen loading="lazy"></iframe></div>')
        body = (f'<div class="hero"><span class="pill">VIDÉO DU {a["date"][8:]}/{a["date"][5:7]}/{a["date"][:4]}</span><h1>{esc(a["title"])}</h1></div>{vid}{render_body(sec)}'
                f'<div class="cta reveal card"><h2>Ne rate aucun décryptage</h2><p>Abonne-toi sur tous nos réseaux : Une vidéo longue et un Short, tous les jours.</p><div class="nets" style="justify-content:center">{netlinks()}</div></div>')
        open(f"docs/articles/{a['slug']}.html", "w", encoding="utf-8").write(shell(a["title"] + " | Décryptage Express", summ, f"{BASE}/articles/{a['slug']}.html", body, "../"))
    cards = "".join(f'<a class="post reveal" href="articles/{a["slug"]}.html"><small>{a["date"]}</small><h3>{esc(a["title"])}</h3><p>{esc(a["summary"][:150])}…</p></a>' for a in items)
    hero = '<div class="hero"><span class="pill">ACTU IA · TECH · BOURSE</span><h1>Décryptage Express</h1><p>Toute l\'actu IA décryptée simplement, sans blabla. Une vidéo longue et un Short, tous les jours.</p><div class="nets" style="justify-content:center">' + netlinks() + "</div></div>"
    open("docs/index.html", "w", encoding="utf-8").write(shell("Décryptage Express : l'actu IA, tech et bourse décryptée", "Toute l'actu IA, tech et bourse décryptée chaque jour : Shorts et vidéo longue.", BASE + "/", hero + f'<div class="grid">{cards}</div>', ""))
    esc2 = html.escape; rfc = lambda d: datetime.datetime.strptime(d, "%Y-%m-%d").strftime("%a, %d %b %Y 12:00:00 +0000")
    rss = "".join(f'<item><title>{esc2(a["title"])}</title><link>{BASE}/articles/{a["slug"]}.html</link><guid>{BASE}/articles/{a["slug"]}.html</guid><pubDate>{rfc(a["date"])}</pubDate><description>{esc2(a["summary"])}</description></item>' for a in items)
    open("docs/feed.xml", "w", encoding="utf-8").write(f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>Décryptage Express</title><link>{BASE}/</link><description>Actu IA, tech et bourse décryptée</description><language>fr</language>{rss}</channel></rss>')
    open("docs/sitemap.xml", "w").write('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>' + BASE + "/</loc></url>" + "".join(f'<url><loc>{BASE}/articles/{a["slug"]}.html</loc></url>' for a in items) + "</urlset>")
    open("docs/robots.txt", "w").write(f"User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n")
    print(len(items), "articles,", sum(1 for a in items if a.get("yt")), "avec vidéo")

if __name__ == "__main__":
    if sys.argv[1] != "--rebuild": add(sys.argv[1])
    rebuild()
