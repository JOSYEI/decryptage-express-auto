import sys, json, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import seo
name, mode, src, out = sys.argv[1:5]
d = json.load(open(src)); d["custom"] = True
bl = [b["text"] for b in d["blocks"]]
m = json.load(open(out)) if os.path.exists(out) else {}
S = seo.build(d, [{"title": d["title"], "articles": [{"title": d["title"], "source": ""}]}], mode, bl)
m.update(S); json.dump(m, open(out, "w"), ensure_ascii=False, indent=2)
print(len(S["title"]), len(S["description"]), len(S["tags"]))
