"""Habillage animé : intro cinématique, cartes statistiques (compteur + jauge), incrustations d'images. Séquences PNG RGBA superposées par ffmpeg
dans une zone libre (jamais sur les sous-titres centraux ni sur le plan principal)."""
import os, math, re
from PIL import Image, ImageDraw, ImageFont, ImageFilter
FPS = 30
FONTS = ["/usr/share/fonts/truetype/roboto/unhinted/RobotoCondensed-Black.ttf", "/usr/share/fonts/truetype/roboto/unhinted/Roboto-Black.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
def font(s):
    for p in FONTS:
        try: return ImageFont.truetype(p, s)
        except Exception: pass
    return ImageFont.load_default()
def ease(t): t = min(max(t, 0), 1); return 1 - (1 - t) ** 3
def back(t, c=1.5): t = min(max(t, 0), 1); return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2
GOLD = (255, 214, 0)
def _fade(t, dur, tin=.35, tout=.3): return min(1, t / tin) * min(1, max(0, (dur - t) / tout))
def _finish(im, a, out, i):
    if a < 1: im.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
    im.save(f"{out}/{i:03d}.png")

def intro(out, W, H, dur=2.6):
    """Ouverture cinématique : écran noir, trait de lumière, bandes cinéma qui s'ouvrent, titre lettre par lettre avec balayage de lumière."""
    os.makedirs(out, exist_ok=True); N = int(dur * FPS); title = "DÉCRYPTAGE EXPRESS"
    fs = int(W * (.075 if H > W else .05)); f = font(fs); ty = int(H * (.80 if H > W else .86))
    _d = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    while fs > 20 and sum(_d.textlength(c, font=f) + W * .006 for c in title) > W * .86: fs -= 4; f = font(fs)
    for i in range(N):
        t = i / FPS; im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        open_k = ease((t - .35) / 1.0)
        bar = int(H / 2 * (1 - open_k)) + (int(H * .075) * (1 if t < dur - .5 else max(0, (dur - t) / .5)) * open_k if t > .35 else 0)
        bar = int(bar)
        d.rectangle((0, 0, W, bar), fill=(0, 0, 0, 255)); d.rectangle((0, H - bar, W, H), fill=(0, 0, 0, 255))
        if t < .55:  # trait de lumière horizontal qui s'ouvre
            k = ease(t / .35); half = int(W * .5 * k); a = int(255 * (1 - max(0, (t - .35) / .2)))
            d.rectangle((W // 2 - half, H // 2 - 2, W // 2 + half, H // 2 + 2), fill=(255, 235, 150, a))
        # titre : lettres qui apparaissent en cascade
        if .7 <= t <= dur:
            tt = t - .7; chars = list(title); widths = [d.textlength(c, font=f) + W * .006 for c in chars]; tw = sum(widths)
            x = W / 2 - tw / 2; glow = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(glow)
            for k, c in enumerate(chars):
                a = ease((tt - k * .045) / .25) * min(1, max(0, (dur - t) / .4))
                if a > 0:
                    dy = int((1 - ease((tt - k * .045) / .25)) * 24)
                    col = (255, 255, 255, int(255 * a)); gd.text((x, ty + dy), c, font=f, fill=(255, 214, 0, int(160 * a)), stroke_width=6, stroke_fill=(255, 214, 0, int(120 * a)))
                    d.text((x, ty + dy), c, font=f, fill=col, stroke_width=4, stroke_fill=(0, 0, 0, int(255 * a)))
                x += widths[k]
            im = Image.alpha_composite(glow.filter(ImageFilter.GaussianBlur(10)), im)
            d = ImageDraw.Draw(im)
            sx = int((W + 400) * ease((tt - .2) / 1.0)) - 200  # balayage de lumière
            if 0 < tt - .2 < 1.0: d.polygon([(sx, ty - 10), (sx + 60, ty - 10), (sx + 20, ty + int(f.size * 1.3)), (sx - 40, ty + int(f.size * 1.3))], fill=(255, 255, 255, 70))
        im.save(f"{out}/{i:03d}.png")

def _card_base(w, h, a=1.0):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), h // 9, fill=(8, 12, 28, 225), outline=GOLD + (255,), width=5)
    return im, d

def stat_card(out, w, h, value, unit, label, dur=3.2):
    """Carte statistique : compteur qui monte de 0 à la valeur + jauge (si %) ou barres croissantes (autres unités)."""
    os.makedirs(out, exist_ok=True); N = int(dur * FPS)
    txt_val = (f"{value:.1f}".rstrip("0").rstrip(".") if value != int(value) else f"{int(value)}")
    for i in range(N):
        t = i / FPS; k = ease((t - .25) / 1.3); cur = value * k
        im, d = _card_base(w, h)
        s = f"{cur:.1f}".rstrip("0").rstrip(".") if value != int(value) and k < 1 else (f"{int(round(cur))}" if value == int(value) else txt_val)
        if k >= 1: s = txt_val
        suffix = "%" if unit == "%" else ""
        fb = font(int(h * .42)); d.text((int(w * .06), int(h * .06)), s + suffix, font=fb, fill=GOLD + (255,), stroke_width=3, stroke_fill=(0, 0, 0, 255))
        if unit != "%": fu = font(int(h * .17)); d.text((int(w * .06), int(h * .50)), unit.upper(), font=fu, fill=(255, 255, 255, 255))
        fl = font(int(h * .12)); d.text((int(w * .06), int(h * (.70 if unit != "%" else .52))), label.upper()[:34], font=fl, fill=(200, 210, 230, 255))
        if unit == "%":
            bx0, bx1, by = int(w * .06), int(w * .94), int(h * .80); d.rounded_rectangle((bx0, by, bx1, by + int(h * .1)), 12, fill=(40, 48, 70, 255))
            fillw = int((bx1 - bx0) * min(value, 100) / 100 * k)
            if fillw > 8: d.rounded_rectangle((bx0, by, bx0 + fillw, by + int(h * .1)), 12, fill=GOLD + (255,))
        else:
            bars = 6; bw = int(w * .07); gx = int(w * .5)
            for b in range(bars):
                kk = ease((t - .25 - b * .12) / .5); bh = int(h * (.25 + .5 * (b + 1) / bars) * kk)
                x0 = gx + b * (bw + 10); d.rounded_rectangle((x0, int(h * .85) - bh, x0 + bw, int(h * .85)), 6, fill=GOLD + (255,) if b == bars - 1 else (255, 255, 255, 190))
        im = im.transform(im.size, Image.AFFINE, (1, 0, 0, 0, 1, int((1 - back(t / .4)) * -60)))
        _finish(im, _fade(t, dur), out, i)

def pip_card(out, w, h, frame_path, tag="EN IMAGES", dur=2.4):
    """Incrustation d'une image/vidéo d'illustration (cadre doré, léger zoom lent)."""
    os.makedirs(out, exist_ok=True); N = int(dur * FPS); src = Image.open(frame_path).convert("RGB")
    for i in range(N):
        t = i / FPS; z = 1.0 + .08 * t / dur; sw, sh = src.size
        cw, ch = int(sw / z), int(sh / z); l, tp = (sw - cw) // 2, (sh - ch) // 2
        pic = src.crop((l, tp, l + cw, tp + ch)).resize((w, h), Image.LANCZOS)
        m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), h // 12, fill=255)
        im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); im.paste(pic, (0, 0), m)
        d = ImageDraw.Draw(im); d.rounded_rectangle((2, 2, w - 3, h - 3), h // 12, outline=GOLD + (255,), width=6)
        f = font(int(h * .09)); tb = d.textbbox((0, 0), tag, font=f); tw = tb[2] - tb[0] + 30
        d.rounded_rectangle((18, 18, 18 + tw, 18 + int(h * .13)), 10, fill=GOLD + (255,)); d.text((33 - tb[0], 18 + int(h * .065) - (tb[3] - tb[1]) // 2 - tb[1]), tag, font=f, fill=(0, 0, 0, 255))
        im = im.transform(im.size, Image.AFFINE, (1, 0, 0, 0, 1, int((1 - back(t / .4)) * -60)))
        _finish(im, _fade(t, dur), out, i)

NUM = re.compile(r"^(\d+(?:[.,]\d+)?)(%?)$")
def find_stats(toks):
    """Chiffres présents DANS le texte (jamais inventés) : retourne [(index_token, valeur, unité, libellé)]."""
    res = []
    for i, tk in enumerate(toks):
        m = NUM.match(tk.strip(",.;:!?»«\"'"))
        if not m: continue
        v = float(m.group(1).replace(",", ".")); nxt = [x.strip(",.;:!?").lower() for x in toks[i + 1:i + 5]]
        if m.group(2) == "%": unit, rest = "%", nxt
        elif nxt[:1] == ["%"]: unit, rest = "%", nxt[1:]
        elif nxt[:2] == ["pour", "cent"]: unit, rest = "%", nxt[2:]
        elif nxt and re.match(r"milliards?|millions?|mille", nxt[0]): unit, rest = nxt[0], nxt[1:]
        else: continue
        res.append((i, v, unit, " ".join(rest[:3])))
    return res
