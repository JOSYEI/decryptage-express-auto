"""Couverture automatique (9:16 Short / 16:9 longue) : image d'une scène floutée, bandeau + titre accrocheur dans la zone sûre."""
import os, re, subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
FONTS = ["/usr/share/fonts/truetype/roboto/unhinted/RobotoCondensed-Black.ttf", "/usr/share/fonts/truetype/roboto/unhinted/Roboto-Black.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
def font(n):
    for f in FONTS:
        try: return ImageFont.truetype(f, n)
        except Exception: pass
    return ImageFont.load_default()
def wrap(s, size, maxw):
    out, cur = [], ""
    for w in s.split():
        t = (cur + " " + w).strip()
        if font(size).getlength(t) <= maxw: cur = t
        else: out.append(cur); cur = w
    return out + [cur]
def make(video, title, tag, out, short):
    W, H = (1080, 1920) if short else (1280, 720)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", "4", "-i", video, "-frames:v", "1", "/tmp/_cv.png"], check=True)
    im = Image.open("/tmp/_cv.png").convert("RGB"); r = max(W / im.width, H / im.height)
    im = im.resize((int(im.width * r) + 1, int(im.height * r) + 1)); x = (im.width - W) // 2; y = (im.height - H) // 2
    im = im.crop((x, y, x + W, y + H)); im = ImageEnhance.Contrast(im).enhance(1.15).filter(ImageFilter.GaussianBlur(5))
    NAVY = (5, 12, 28); CY = (0, 200, 255)
    im = Image.blend(im, Image.new("RGB", (W, H), NAVY), 0.62).convert("RGBA")
    # halo cyan + éclair diagonal (ADN du logo DE)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0)); g = ImageDraw.Draw(glow)
    bx, by = (W * 0.84, H * 0.20) if short else (W * 0.90, H * 0.50); s_ = H * (0.16 if short else 0.42)
    bolt = [(bx, by - s_), (bx - s_ * .22, by - s_ * .02), (bx - s_ * .02, by - s_ * .02), (bx - s_ * .30, by + s_), (bx + s_ * .20, by + s_ * .10), (bx, by + s_ * .10)]
    g.polygon(bolt, fill=CY + (255,)); glow = glow.filter(ImageFilter.GaussianBlur(22 if short else 16))
    im = Image.alpha_composite(im, glow)
    ov = Image.new("RGBA", (W, H)); d = ImageDraw.Draw(ov)
    for yy in range(H): d.line([(0, yy), (W, yy)], fill=(NAVY + (min(200, int(110 * (1 - abs(yy - H / 2) / (H / 2)) ** .6) + 25),)))
    im = Image.alpha_composite(im, ov); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 10 if not short else 14), fill=CY + (255,)); d.rectangle((0, H - (10 if not short else 14), W, H), fill=CY + (255,))
    zx0, zx1 = (110, 970) if short else (70, 1210); zy0, zy1 = (640, 1260) if short else (130, 590)
    maxw = zx1 - zx0; cx = (zx0 + zx1) // 2
    text = re.sub(r"\s*[|#].*$", "", title).upper(); size = int(H * (0.085 if short else 0.15))
    lines = wrap(text, size, maxw)
    while (len(lines) > 4 or any(font(size).getlength(l) > maxw for l in lines)) and size > 30: size -= 4; lines = wrap(text, size, maxw)
    th = int(size * 1.12) * len(lines); y = (zy0 + zy1) / 2 - th / 2 + 40
    tf = font(int(H * 0.03)); tw = tf.getlength(tag) + 60; ph = int(H * 0.03) + 34
    d.rounded_rectangle((cx - tw / 2, y - 90, cx + tw / 2, y - 90 + ph), radius=30, fill=CY + (255,))
    d.text((cx, y - 90 + ph / 2), tag, font=tf, fill=NAVY, anchor="mm")
    cols = [(255, 255, 255), CY, (255, 255, 255), CY]
    for i, l in enumerate(lines):
        d.text((cx, y + int(size * 1.12) * i + size / 2), l, font=font(size), fill=cols[i % 4], anchor="mm", stroke_width=max(6, size // 12), stroke_fill=NAVY)
    try:
        lg = Image.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "logo.jpg")).convert("RGB"); ls = int(H * (0.11 if short else 0.16)); lg = lg.resize((ls, ls))
        m = Image.new("L", (ls, ls), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, ls, ls), radius=ls // 5, fill=255)
        ly = (zy0 - ls - 40) if short else 18; im.paste(lg, (int(W / 2 - ls / 2) if short else 40, int(ly)), m)
    except Exception: pass
    d.text((W / 2, H - int(H * 0.05)), "DÉCRYPTAGE EXPRESS", font=font(int(H * 0.028)), fill=CY, anchor="mm", stroke_width=3, stroke_fill=NAVY)
    im.convert("RGB").save(out, quality=93)
