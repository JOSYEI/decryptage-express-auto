"""Assemble un script JSON à partir d'un fichier texte : en-tête 'titre:', 'desc:', 'tags:' puis blocs séparés par une ligne vide, chaque bloc = 'mot1,mot2,mot3 | texte'."""
import sys, json
src, out = sys.argv[1:3]
head, blocks = {}, []
for part in open(src, encoding="utf8").read().strip().split("\n\n"):
    part = part.strip()
    if part.startswith(("titre:", "desc:", "tags:")):
        for l in part.split("\n"): k, v = l.split(":", 1); head[k] = v.strip()
    else:
        kw, txt = part.split("|", 1); blocks.append({"text": " ".join(txt.split()), "keywords": [k.strip() for k in kw.split(",")]})
n = sum(len(b["text"].split()) for b in blocks)
json.dump({"title": head["titre"], "description": head["desc"], "hashtags": head["tags"].split(), "blocks": blocks}, open(out, "w", encoding="utf8"), ensure_ascii=False, indent=1)
print(out, len(blocks), "blocs", n, "mots ~", round(n / 165, 1), "min")
