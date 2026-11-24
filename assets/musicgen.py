"""Musique de fond originale, énergique et motivante (électro-cinématique), générée en numpy : aucune dépendance, aucun droit d'auteur.
124 bpm, la mineur : intro pad + arpège, puis kick / clap / hats / basse pulsée. Sidechain appliqué ensuite par ffmpeg pour laisser la voix passer."""
import numpy as np, wave, random
SR = 44100
def _env(n, a, d):
    t = np.arange(n) / SR
    return np.minimum(t / max(a, 1e-4), 1) * np.exp(-t / d)
def make(path, total, seed=None):
    rnd = random.Random(seed); bpm = rnd.choice([120, 124, 128]); beat = 60 / bpm; n = int((total + 2) * SR)
    out = np.zeros(n); t_all = np.arange(n) / SR
    root = rnd.choice([55.0, 49.0, 58.27])  # A1 / G1 / A#1
    prog = [(0, [0, 3, 7]), (-4, [0, 4, 7]), (-9, [0, 4, 7]), (-2, [0, 4, 7])]  # Am F C G (demi-tons relatifs à la tonique)
    f = lambda semi, oct=0: root * 2 ** ((semi + 12 * oct) / 12)
    nb = int((total + 2) / beat) + 1
    def add(sig, t0):
        i = int(t0 * SR)
        if i >= n: return
        j = min(n, i + len(sig)); out[i:j] += sig[:j - i]
    # pad
    for bar in range(nb // 4 + 1):
        r, ch = prog[bar % 4]; t0 = bar * 4 * beat; L = int(4 * beat * SR)
        if int(t0 * SR) >= n: break
        t = np.arange(L) / SR
        sig = sum(np.sin(2 * np.pi * f(r + c, 2) * t) + .5 * np.sin(2 * np.pi * f(r + c, 2) * 1.004 * t) for c in ch)
        sig *= np.minimum(t / (beat * 1.5), 1) * np.minimum((4 * beat - t) / .3, 1) * .045
        add(sig, t0)
    # arpège 16es
    for k in range(nb * 4):
        bar = k // 16; r, ch = prog[bar % 4]; step = k % 16
        semi = ch[[0, 1, 2, 1][step % 4]] + (12 if step % 8 >= 4 else 0)
        L = int(.22 * SR); t = np.arange(L) / SR
        sig = np.sign(np.sin(2 * np.pi * f(r + semi, 2) * t)) * .5 + np.sin(2 * np.pi * f(r + semi, 3) * t) * .5
        sig *= np.exp(-t / .07) * (.05 if bar >= 2 else .028)
        add(sig, k * beat / 4)
    # batterie + basse à partir de la 5e mesure (montée en puissance)
    for k in range(nb):
        t0 = k * beat; bar = k // 4
        if bar < 2: continue
        L = int(.35 * SR); t = np.arange(L) / SR
        kick = np.sin(2 * np.pi * (45 * t + 90 * (1 - np.exp(-t * 25)) / 25 * 25 / 25 * 1) ) if False else np.sin(2 * np.pi * np.cumsum(45 + 110 * np.exp(-t * 30)) / SR)
        add(kick * np.exp(-t / .12) * .9, t0)
        if k % 4 in (1, 3):
            L2 = int(.2 * SR); tt = np.arange(L2) / SR
            clap = np.random.default_rng(k).standard_normal(L2) * np.exp(-tt / .05) * .28
            add(clap, t0)
        for off in (.5,):
            L3 = int(.06 * SR); tt = np.arange(L3) / SR
            hat = np.diff(np.random.default_rng(k + 99).standard_normal(L3 + 1)) * np.exp(-tt / .015) * .2
            add(hat, t0 + off * beat)
        r, ch = prog[bar % 4]
        for s in range(2):  # basse pulsée en croches
            Lb = int(beat / 2 * SR); tb = np.arange(Lb) / SR
            bass = np.sin(2 * np.pi * f(r) * tb) + .35 * np.sin(2 * np.pi * f(r) * 2 * tb)
            add(bass * np.minimum(tb / .01, 1) * np.exp(-tb / .3) * .5, t0 + s * beat / 2)
    # riser sur 2 mesures avant le début des drums
    Lr = int(2 * 4 * beat * SR); tr = np.arange(Lr) / SR
    ris = np.random.default_rng(1).standard_normal(Lr) * (tr / tr[-1]) ** 2 * .05
    add(ris, 0)
    out = out[:n] * np.minimum(t_all / .5, 1)
    out = np.tanh(out * 1.6) / np.tanh(1.6); out /= max(abs(out).max(), 1e-6)
    pcm = (out * 0.9 * 32767).astype(np.int16)
    with wave.open(path, "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
