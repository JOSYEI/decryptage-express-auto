"""Effets sonores synthétiques (numpy) : ouverture, fin, transitions (switch / whoosh), cloche d'abonnement. Tous audibles : crêtes ~ -0,8 dB avant mixage."""
import numpy as np, wave
SR = 44100
def _noise(n, seed): return np.random.default_rng(seed).standard_normal(n)
def _lp(x, a):  # filtre passe-bas simple
    y = np.zeros_like(x); s = 0.0
    for i, v in enumerate(x): s += a * (v - s); y[i] = s
    return y
def whoosh(seed=0, dur=.55):
    n = int(dur * SR); t = np.linspace(0, 1, n)
    x = _noise(n, seed); lo = _lp(x, .02); hi = x - _lp(x, .35)
    sweep = lo * (1 - t) + (x - _lp(x, .15)) * t  # grave -> aigu : effet « wash »
    env = np.sin(np.pi * t) ** 1.5
    y = sweep * env; return y / max(abs(y).max(), 1e-6) * .9
def switch(seed=0):  # « clac » sec de commutateur : deux clics rapprochés
    n = int(.12 * SR); t = np.arange(n) / SR; y = np.zeros(n)
    for off, f, g in ((0, 2600, 1), (.045, 1700, .75)):
        i = int(off * SR); m = n - i; tt = np.arange(m) / SR
        y[i:] += (np.sin(2 * np.pi * f * tt) * .6 + _noise(m, seed + i) * .5) * np.exp(-tt / .012) * g
    return y / max(abs(y).max(), 1e-6) * .9
def boom(dur=1.4):
    n = int(dur * SR); t = np.arange(n) / SR
    k = np.sin(2 * np.pi * np.cumsum(38 + 120 * np.exp(-t * 6)) / SR) * np.exp(-t / .5)
    sh = _lp(_noise(n, 5), .5) * np.exp(-t / .35) * .35
    return (k + sh) / max(abs(k + sh).max(), 1e-6) * .9
def riser(dur=1.3):
    n = int(dur * SR); t = np.linspace(0, 1, n); x = _noise(n, 8)
    y = (x - _lp(x, .1)) * t ** 2.2 + np.sin(2 * np.pi * np.cumsum(200 + 1400 * t ** 2) / SR) * .3 * t
    return y / max(abs(y).max(), 1e-6) * .8
def bell(dur=1.2):  # « cling » : partiels inharmoniques de cloche
    n = int(dur * SR); t = np.arange(n) / SR
    y = sum(a * np.sin(2 * np.pi * 1760 * r * t) * np.exp(-t / d) for r, a, d in ((1, 1, .5), (2.76, .5, .3), (5.4, .3, .18), (8.93, .2, .1)))
    y *= np.minimum(t / .002, 1); return y / max(abs(y).max(), 1e-6) * .85
def build(path, total, trans, ctat, clk, seed=0):
    """trans : liste (temps, 'switch'|'whoosh'). Ouverture à t=0, fin à total, cloche (x2) au clic de l'abonnement."""
    out = np.zeros(int((total + 2) * SR))
    def add(sig, t0, g=1.0):
        i = int(max(t0, 0) * SR)
        if i >= len(out): return
        j = min(len(out), i + len(sig)); out[i:j] += sig[:j - i] * g
    add(boom(), 0, 1.0); add(whoosh(1, .7), 0, .7)          # ouverture
    add(riser(), total - 1.9, .8); add(boom(1.2), total - .6, .9)  # fin
    for k, (t, kind) in enumerate(trans):
        add(switch(k) if kind == "switch" else whoosh(10 + k), t - (0 if kind == "switch" else .25), .9)
    add(bell(), clk / 1000 + .05, .9); add(bell(), clk / 1000 + .32, .8)  # cling cling
    out = out[:int((total) * SR)]; out = np.clip(out, -1, 1)
    with wave.open(path, "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((out * 32767 * .93).astype(np.int16).tobytes())
