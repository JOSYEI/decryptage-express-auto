"""Couverture automatique (9:16 Short / 16:9 longue) : image d'une scène floutée, bandeau + titre accrocheur dans la zone sûre."""
import re, subprocess
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
    im = im.crop((x, y, x + W, y + H)); im = ImageEnhance.Color(ImageEnhance.Contrast(im).enhance(1.25)).enhance(1.3).filter(ImageFilter.GaussianBlur(8))
    ov = Image.new("RGBA", (W, H)); d = ImageDraw.Draw(ov)
    for yy in range(H): d.line([(0, yy), (W, yy)], fill=(0, 0, 0, min(215, int(120 * (1 - abs(yy - H / 2) / (H / 2)) ** .6) + 30)))
    im = Image.alpha_composite(im.convert("RGBA"), ov); d = ImageDraw.Draw(im)
    zx0, zx1 = (110, 970) if short else (70, 1210); zy0, zy1 = (640, 1260) if short else (130, 590)
    maxw = zx1 - zx0; cx = (zx0 + zx1) // 2
    text = re.sub(r"\s*[|#].*$", "", title).upper(); size = int(H * (0.085 if short else 0.15))
    lines = wrap(text, size, maxw)
    while (len(lines) > 4 or any(font(size).getlength(l) > maxw for l in lines)) and size > 30: size -= 4; lines = wrap(text, size, maxw)
    th = int(size * 1.12) * len(lines); y = (zy0 + zy1) / 2 - th / 2 + 40
    tf = font(int(H * 0.03)); tw = tf.getlength(tag) + 60
    d.rounded_rectangle((cx - tw / 2, y - 90, cx + tw / 2, y - 90 + int(H * 0.03) + 34), radius=30, fill=(230, 20, 40))
    d.text((cx, y - 90 + (int(H * 0.03) + 34) / 2), tag, font=tf, fill=(255, 255, 255), anchor="mm")
    cols = [(255, 214, 0), (255, 255, 255), (255, 70, 70), (255, 255, 255)]
    for i, l in enumerate(lines):
        d.text((cx, y + int(size * 1.12) * i + size / 2), l, font=font(size), fill=cols[i % 4], anchor="mm", stroke_width=max(6, size // 12), stroke_fill=(0, 0, 0))
    d.text((W / 2, H - int(H * 0.05)), "DÉCRYPTAGE EXPRESS", font=font(int(H * 0.028)), fill=(255, 255, 255), anchor="mm", stroke_width=3, stroke_fill=(0, 0, 0))
    im.convert("RGB").save(out, quality=93)
