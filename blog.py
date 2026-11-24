"""Génère le blog statique (docs/) : un article par vidéo longue + index, flux RSS, sitemap. Hébergé gratuitement sur GitHub Pages."""
import sys, os, json, html, re, datetime
BASE = os.environ.get("BLOG_URL", "https://josyei.github.io/decryptage-express-auto")
DOCS = "docs"; D = sys.argv[1]
m = json.load(open(os.path.join(D, "meta.json")))
if m.get("mode") != "long": sys.exit(0)
day = re.search(r"(\d{4}-\d{2}-\d{2})", D).group(1)
slug = day + "-" + re.sub(r"[^a-z0-9]+", "-", m["title"].lower().encode("ascii", "ignore").decode())[:50].strip("-")
os.makedirs(DOCS + "/articles", exist_ok=True)
esc = html.escape
desc = m["description"].split("🔑 MOTS-CLÉS")[0].strip()
paras = "".join("<p>" + esc(p).replace("\n", "<br>") + "</p>" for p in desc.split("\n\n") if p.strip())
page = f"""<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(m['title'])} | Décryptage Express</title><meta name="description" content="{esc(desc[:155])}">
<link rel="canonical" href="{BASE}/articles/{slug}.html"><style>body{{font-family:system-ui;max-width:760px;margin:2rem auto;padding:0 1rem;background:#0b1530;color:#e8f1ff;line-height:1.6}}a{{color:#3fd0ff}}</style></head><body>
<p><a href="{BASE}/">← Décryptage Express</a></p><h1>{esc(m['title'])}</h1><p><em>{day}</em></p>{paras}
<p>▶ Retrouve la vidéo et tous les décryptages : <a href="https://www.youtube.com/channel/UCUwq8QxrO-DulXvTwH2lT0w?sub_confirmation=1">chaîne YouTube</a>.</p>
<p>{esc(m.get('hashtags',''))}</p></body></html>"""
open(f"{DOCS}/articles/{slug}.html", "w", encoding="utf-8").write(page)
idx = f"{DOCS}/index.json"
items = json.load(open(idx)) if os.path.exists(idx) else []
items = [i for i in items if i["slug"] != slug] + [{"slug": slug, "title": m["title"], "date": day, "summary": desc[:300]}]
items.sort(key=lambda i: i["date"], reverse=True); items = items[:200]
json.dump(items, open(idx, "w"), ensure_ascii=False)
li = "".join(f'<li><a href="articles/{i["slug"]}.html">{esc(i["title"])}</a> <small>{i["date"]}</small></li>' for i in items)
open(f"{DOCS}/index.html", "w", encoding="utf-8").write(f'<!doctype html><html lang="fr"><head><meta charset="utf-8"><title>Décryptage Express : l\'actu IA, tech et bourse décryptée</title><link rel="alternate" type="application/rss+xml" href="feed.xml"><style>body{{font-family:system-ui;max-width:760px;margin:2rem auto;padding:0 1rem;background:#0b1530;color:#e8f1ff}}a{{color:#3fd0ff}}</style></head><body><h1>Décryptage Express</h1><p>L\'actu IA, tech et bourse décryptée chaque jour.</p><ul>{li}</ul></body></html>')
rfc = lambda d: datetime.datetime.strptime(d, "%Y-%m-%d").strftime("%a, %d %b %Y 12:00:00 +0000")
rss = "".join(f'<item><title>{esc(i["title"])}</title><link>{BASE}/articles/{i["slug"]}.html</link><guid>{BASE}/articles/{i["slug"]}.html</guid><pubDate>{rfc(i["date"])}</pubDate><description>{esc(i["summary"])}</description></item>' for i in items)
open(f"{DOCS}/feed.xml", "w", encoding="utf-8").write(f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>Décryptage Express</title><link>{BASE}/</link><description>Actu IA, tech et bourse décryptée</description><language>fr</language>{rss}</channel></rss>')
open(f"{DOCS}/sitemap.xml", "w").write('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>' + BASE + '/</loc></url>' + "".join(f'<url><loc>{BASE}/articles/{i["slug"]}.html</loc></url>' for i in items) + "</urlset>")
open(f"{DOCS}/robots.txt", "w").write(f"User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n")
