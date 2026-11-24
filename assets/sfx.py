"""Effets sonores synthétiques (numpy) : ouverture, fin, transitions (switch / whoosh), cloche d'abonnement. Tous audibles : crêtes ~ -0,8 dB avant mixage."""
import numpy as np, wave
SR = 44100
def _noise(n, seed): return np.random.default_rng(seed).standard_normal(n)
def _lp(x, a):  # filtre passe-bas simple
    y = np.zeros_like(x); s = 0.0
    for i, v in enumerate(x): s += a * (v - s); y[i] = s
    return y
def whoosh(seed=0, dur=.55, a_lo=.02, a_hi=.15, up=True):
    n = int(dur * SR); t = np.linspace(0, 1, n)
    x = _noise(n, seed); lo = _lp(x, a_lo)
    hi = x - _lp(x, a_hi)
    sweep = lo * (1 - t) + hi * t if up else hi * (1 - t) + lo * t  # grave -> aigu (ou l'inverse) : effet « wash »
    env = np.sin(np.pi * t) ** 1.5
    y = sweep * env; return y / max(abs(y).max(), 1e-6) * .9
def switch(seed=0, f1=2600, f2=1700, gap=.045):  # « clac » sec de commutateur : deux clics rapprochés
    n = int(.12 * SR); t = np.arange(n) / SR; y = np.zeros(n)
    for off, f, g in ((0, f1, 1), (gap, f2, .75)):
        i = int(off * SR); m = n - i; tt = np.arange(m) / SR
        y[i:] += (np.sin(2 * np.pi * f * tt) * .6 + _noise(m, seed + i) * .5) * np.exp(-tt / .012) * g
    return y / max(abs(y).max(), 1e-6) * .9
def boom(dur=1.4, f0=38, seed=5):
    n = int(dur * SR); t = np.arange(n) / SR
    k = np.sin(2 * np.pi * np.cumsum(f0 + 120 * np.exp(-t * 6)) / SR) * np.exp(-t / .5)
    sh = _lp(_noise(n, seed), .5) * np.exp(-t / .35) * .35
    return (k + sh) / max(abs(k + sh).max(), 1e-6) * .9
def riser(dur=1.3):
    n = int(dur * SR); t = np.linspace(0, 1, n); x = _noise(n, 8)
    y = (x - _lp(x, .1)) * t ** 2.2 + np.sin(2 * np.pi * np.cumsum(200 + 1400 * t ** 2) / SR) * .3 * t
    return y / max(abs(y).max(), 1e-6) * .8
def bell(dur=1.2, f=1760):  # « cling » : partiels inharmoniques de cloche
    n = int(dur * SR); t = np.arange(n) / SR
    y = sum(a * np.sin(2 * np.pi * f * r * t) * np.exp(-t / d) for r, a, d in ((1, 1, .5), (2.76, .5, .3), (5.4, .3, .18), (8.93, .2, .1)))
    y *= np.minimum(t / .002, 1); return y / max(abs(y).max(), 1e-6) * .85
def build(path, total, trans, ctat, clk, seed=0):
    """trans : liste (temps, 'switch'|'whoosh'). Chaque son d'une même vidéo est DIFFÉRENT (jamais deux fois le même). Niveaux discrets sous la voix."""
    import random; rnd = random.Random(seed)
    out = np.zeros(int((total + 2) * SR))
    def add(sig, t0, g=1.0):
        i = int(max(t0, 0) * SR)
        if i >= len(out): return
        j = min(len(out), i + len(sig)); out[i:j] += sig[:j - i] * g
    sw_f = [(2600, 1700, .045), (3200, 2100, .06), (2100, 1300, .035), (3600, 2400, .05), (1900, 1100, .07)]; rnd.shuffle(sw_f)
    wh_p = [(.5, .02, .15, True), (.7, .03, .25, False), (.4, .015, .1, True), (.85, .04, .2, False), (.6, .025, .3, True)]; rnd.shuffle(wh_p)
    add(riser(1.0), 0, .35); add(boom(1.6, rnd.choice([36, 40, 44]), rnd.randrange(999)), .95, .55); add(whoosh(rnd.randrange(999), .8, .02, .15, True), .75, .35)  # ouverture cinématique : montée, puis impact à l'ouverture des bandes
    add(riser(), total - 1.9, .4); add(boom(1.2, rnd.choice([50, 54, 58]), rnd.randrange(999)), total - .6, .5)  # fin (différente de l'ouverture)
    si = wi = 0
    for k, (t, kind) in enumerate(trans):
        if kind == "switch":
            f1, f2, g = sw_f[si % len(sw_f)]; si += 1; add(switch(rnd.randrange(999), f1, f2, g), t, .4)
        else:
            d, a, b, up = wh_p[wi % len(wh_p)]; wi += 1; add(whoosh(rnd.randrange(999), d, a, b, up), t - d * .45, .35)
    add(bell(1.2, 1760), clk / 1000 + .05, .3); add(bell(1.2, 2093), clk / 1000 + .32, .28)  # cling cling : deux notes différentes
    out = out[:int((total) * SR)]; out = np.clip(out, -1, 1)
    with wave.open(path, "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767 * .93).astype(np.int16).tobytes())
