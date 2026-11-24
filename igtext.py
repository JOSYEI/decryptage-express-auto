#!/usr/bin/env python3
"""Légende Instagram : max 25 hashtags (limite 30) et 2200 caractères. Usage : python igtext.py <dossier>"""
import json, re, sys
d = json.load(open(sys.argv[1] + "/meta.json"))["description"]
n = 0
def keep(m):
    global n
    n += 1
    return m.group(0) if n <= 25 else ""
t = re.sub(r"#\w+", keep, d)
t = re.sub(r"[ \t]+\n", "\n", re.sub(r" {2,}", " ", t)).strip()
if len(t) > 2200:
    t = t[:2200].rsplit(" ", 1)[0]
print(t)
