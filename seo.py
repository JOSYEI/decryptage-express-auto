"""SEO automatique : titre ~99 %, description 4950-5000, tags <= 500 (compteur YouTube), commentaire épinglé."""
import re
BANK = ("intelligence artificielle,actualité IA,actu IA,IA générative,agents IA,OpenAI,ChatGPT,Anthropic,Claude,Gemini,DeepSeek,Mistral AI,Nvidia,"
 "puces IA,GPU,data centers,bulle IA,bourse IA,Nasdaq,Wall Street,robots humanoïdes,Tesla Optimus,régulation IA,Europe numérique,cybersécurité,"
 "vie privée,tech,high-tech,innovation,startups,investissement,économie,décryptage,actu tech,actu bourse,veille IA,machine learning,deep learning,LLM,"
 "modèles de langage,automatisation,emploi et IA,futur du travail,souveraineté numérique,cloud,semi-conducteurs,calcul haute performance,supercalculateur").split(",")
ST = set("le la les un une des de du et en au aux à a ce ces sur pour par avec dans qui que est sont il elle the of to in vs ou où se sa son ses plus très pas ne".split())
def words(s): return [w for w in re.findall(r"[\wÀ-ÿ'’-]+", s)]
def est_tags(L): return sum(len(x) + (2 if " " in x else 0) for x in L) + len(L) - 1
def build(script, topics, mode, blocks_text, hours="08h00, 12h00, 16h00 et 20h00"):
    short = mode == "short"
    kws = []
    for t in topics:
        for w in words(t["title"]):
            if len(w) > 3 and w.lower() not in ST and w not in kws: kws.append(w)
    for b in BANK:
        if b not in kws: kws.append(b)
    # tags
    tags = []
    for k in kws:
        if est_tags(tags + [k.lower()]) + 1 <= 497 and k.lower() not in tags: tags.append(k.lower())
    # titre : 95-100 caractères
    title = script["title"].strip().rstrip(".")
    suffix = " #Shorts" if short else ""
    extras = [k for k in kws if k.lower() not in title.lower() and " " not in k]
    for k in extras:
        if len(title) + len(suffix) + 3 + len(k) <= 100 and len(title + suffix) < 96: title += " | " + k if " | " not in title else " " + k
    room = 100 - len(suffix)
    if len(title) > room:
        title = title[:room].rsplit(" ", 1)[0].rstrip(" |,;:-—")
        while title.split(" ")[-1].lower() in ("du", "de", "des", "la", "le", "les", "un", "une", "et", "à", "au", "aux", "en", "sur", "pour", "que", "qui") and " " in title:
            title = title.rsplit(" ", 1)[0].rstrip(" |,;:-—")
    title = title + suffix
    hashtags = " ".join(dict.fromkeys(script.get("hashtags", []) + ["#IA", "#DécryptageExpress"] + (["#Shorts"] if short else [])))
    transcript = " ".join(blocks_text)
    if len(transcript) > 1800: transcript = transcript[:1800].rsplit(".", 1)[0] + "."
    retenir = "\n".join("• " + re.split(r"(?<=[.!?])\s", b)[0] for b in blocks_text[:8])
    if script.get("custom"):
        desc = (f"{script['description']}\n\n👇 Dis-moi en commentaire ce que tu en penses. 🔔 Abonne-toi à Décryptage Express pour comprendre ce que l'IA change dans nos émotions et nos vies.\n\n"
                f"✅ CE QU'IL FAUT RETENIR\n{retenir}\n\n📝 LE RÉSUMÉ\n{transcript}\n\n📩 Newsletter gratuite : https://decryptageexpress.com\n✉️ Contact : contact@decryptageexpress.com\n\n")
    else:
      desc = (f"{script['description']}\n\n👇 Dis-moi en commentaire : ce sujet te surprend-il ? 🔔 Abonne-toi à Décryptage Express pour l'actu IA, tech et bourse décryptée chaque jour.\n\n"
            f"✅ CE QU'IL FAUT RETENIR\n{retenir}\n\n📝 LE RÉSUMÉ COMPLET\n{transcript}\n\n"
            f"🗞️ LES SUJETS DU JOUR\n" + "\n".join("• " + t["title"] + " (" + ", ".join(sorted({a['source'] for a in t['articles']})[:3]) + ")" for t in topics) +
            f"\n\n📩 Newsletter gratuite : https://decryptageexpress.com\n✉️ Contact : contact@decryptageexpress.com\n\n")
    tail = "\n\nContenu réalisé avec l'aide de l'IA (voix de synthèse, images et vidéos assemblées).\n\n" + hashtags
    kline = "🔑 MOTS-CLÉS : "
    pool = [k for k in kws]
    i = 0; body = kline
    while len(desc) + len(body) + len(tail) < 4990 and pool:
        k = pool[i % len(pool)]; add = (", " if body != kline else "") + k
        if len(desc) + len(body) + len(add) + len(tail) > 4995: break
        body += add; i += 1
        if i > 400: break
    desc = (desc + body + tail)[:5000]
    t0 = topics[0]["title"]
    if len(t0) > 110: t0 = t0[:110].rsplit(" ", 1)[0].rstrip(" ,;:-—") + "…"
    pinned = (f"📌 {t0} — qu'en pensez-vous ? Répondez en commentaire 👇 "
              f"Abonnez-vous à Décryptage Express pour l'actu IA, tech et bourse décryptée chaque jour. {hashtags.split(' ')[0]} #IA")
    return {"title": title, "description": desc, "tags": ",".join(tags) + ",", "pinned_comment": pinned, "hashtags": hashtags}
