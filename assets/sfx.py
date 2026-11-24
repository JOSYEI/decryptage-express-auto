"""Effets sonores 100 % tonals (aucun bruit blanc : pas d'effet « sable »). Très discrets, chaque son différent dans une même vidéo."""
import numpy as np, wave, random
SR = 44100
def _t(n): return np.arange(n) / SR
def _norm(y, g=1.0): return y / max(abs(y).max(), 1e-6) * g
def ping(f=2400, dur=.35):  # tic doux de commutateur : cloche sinusoïdale très courte + harmonique
    n = int(dur * SR); t = _t(n)
    y = np.sin(2 * np.pi * f * t) * np.exp(-t / .05) + .35 * np.sin(2 * np.pi * f * 2.01 * t) * np.exp(-t / .03)
    y *= np.minimum(t / .002, 1); return _norm(y)
def tick_pair(f1=2400, f2=1600, gap=.06):
    y = np.zeros(int(.5 * SR)); a = ping(f1, .25); b = ping(f2, .25) * .7; i = int(gap * SR)
    y[:len(a)] += a; y[i:i + len(b)] += b[:len(y) - i]; return _norm(y)
def glide(f0=300, f1=900, dur=.6):  # souffle tonal : glissando lisse (sinus + octave), enveloppe en cloche, sans bruit
    n = int(dur * SR); t = np.linspace(0, 1, n)
    f = f0 * (f1 / f0) ** (t ** 1.2); ph = 2 * np.pi * np.cumsum(f) / SR
    y = (np.sin(ph) + .4 * np.sin(2 * ph) + .2 * np.sin(1.5 * ph)) * np.sin(np.pi * t) ** 2.2
    return _norm(y)
def swell(dur=1.2, root=110, up=True):  # nappe d'accord (quinte + octave) qui monte ou retombe : montée « premium »
    n = int(dur * SR); t = _t(n); u = t / dur
    y = sum(a * (np.sin(2 * np.pi * root * r * t) + .5 * np.sin(2 * np.pi * root * r * 1.003 * t)) for r, a in ((1, 1), (1.5, .7), (2, .6), (3, .3), (4, .15)))
    env = (u ** 2.2) if up else (1 - u) ** 1.5
    return _norm(y * env * np.minimum((dur - t) / .08, 1))
def impact(f0=50, dur=1.8):  # impact cinématique propre : sub profond + accord chaud, sans bruit
    n = int(dur * SR); t = _t(n)
    sub = np.sin(2 * np.pi * np.cumsum(f0 + 60 * np.exp(-t * 14)) / SR) * np.exp(-t / .55)
    chord = sum(a * np.sin(2 * np.pi * f0 * 4 * r * t) * np.exp(-t / d) for r, a, d in ((1, .5, .9), (1.5, .35, .8), (2, .3, .7), (2.52, .2, .6)))
    y = sub + .5 * chord; y *= np.minimum(t / .004, 1); return _norm(y)
def bell(dur=1.4, f=1760):  # « cling » doux, partiels inharmoniques
    n = int(dur * SR); t = _t(n)
    y = sum(a * np.sin(2 * np.pi * f * r * t) * np.exp(-t / d) for r, a, d in ((1, 1, .6), (2.76, .45, .35), (5.4, .22, .2), (8.93, .1, .1)))
    y *= np.minimum(t / .003, 1); return _norm(y)

def build(path, total, trans, ctat, clk, seed=0):
    K = .4  # niveau global : à peine perceptible
    """trans : [(temps, 'switch'|'whoosh')]. Niveaux volontairement très bas : on doit tendre l'oreille pour les entendre."""
    rnd = random.Random(seed); out = np.zeros(int((total + 2) * SR))
    def add(sig, t0, g):
        i = int(max(t0, 0) * SR)
        if i >= len(out): return
        j = min(len(out), i + len(sig)); out[i:j] += sig[:j - i] * g * K
    sw = [(2400, 1600, .06), (3000, 2000, .05), (1900, 1250, .07), (3400, 2300, .045), (2700, 1800, .055)]; rnd.shuffle(sw)
    gl = [(260, 820, .6), (900, 280, .7), (180, 640, .5), (1100, 380, .8), (340, 1000, .55)]; rnd.shuffle(gl)
    roots = [98, 110, 123.5, 87.3]; rnd.shuffle(roots)
    add(swell(1.1, roots[0], True), 0, .10); add(impact(rnd.choice([46, 49, 52]), 1.8), 1.0, .12)   # ouverture : montée d'accord puis impact doux
    add(swell(1.2, roots[1], True), total - 1.7, .09); add(impact(rnd.choice([55, 58, 62]), 1.6), total - .55, .11)  # fin
    si = wi = 0
    for t, kind in trans:
        if kind == "switch":
            a, b, g = sw[si % len(sw)]; si += 1; add(tick_pair(a, b, g), t, .08)
        else:
            f0, f1, d = gl[wi % len(gl)]; wi += 1; add(glide(f0, f1, d), t - d * .5, .07)
    add(bell(1.4, 1760), clk / 1000 + .05, .10); add(bell(1.4, 2093), clk / 1000 + .32, .09)   # cling cling, légèrement
    out = np.clip(out[:int(total * SR)], -1, 1)
    with wave.open(path, "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767).astype(np.int16).tobytes())
