"""Synth music + SFX stems. Pure numpy. Times in frames (30 fps), D = 60.92 s."""
import numpy as np, soundfile as sf, os

SR = 44100
D = 60.92
N = int(D * SR)
RNG = np.random.default_rng(7)

def t_of(f): return f / 30.0

def place(buf, sig, t0):
    i0 = int(t0 * SR)
    i1 = min(N, i0 + len(sig))
    if i1 <= i0: return
    buf[i0:i1] += sig[:i1 - i0]

def env_ad(n, a, d):
    e = np.ones(n)
    na = max(1, int(a * SR)); nd = max(1, int(d * SR))
    na = min(na, n)
    e[:na] = np.linspace(0, 1, na)
    rest = n - na
    nd = min(nd, rest)
    e[na:na + nd] *= np.linspace(1, 0, nd) ** 1.5
    return e

def kick(dur=0.28):
    n = int(dur * SR); t = np.arange(n) / SR
    f = 150 * np.exp(-t * 18) + 44
    return 1.15 * np.sin(2 * np.pi * np.cumsum(f) / SR) * env_ad(n, 0.002, dur)

def snare(dur=0.16):
    n = int(dur * SR); t = np.arange(n) / SR
    noise = RNG.standard_normal(n)
    tone = 190 * np.sin(2 * np.pi * t * (1 + 0.3 * np.exp(-t * 30)))
    body = 0.5 * tone * env_ad(n, 0.001, dur)
    ns = noise * env_ad(n, 0.001, dur * 0.9)
    # simple one-pole lowpass on noise
    out = np.empty(n); acc = 0.0
    for i in range(n):
        acc += 0.35 * (ns[i] - acc); out[i] = acc
    norm = np.sqrt(np.mean((0.4 * out) ** 2)) + 1e-9
    return (0.45 * body + 0.4 * out / norm * 0.25) * 0.9

def pluck(freq, dur=0.34):
    n = int(dur * SR); t = np.arange(n) / SR
    s = np.sin(2 * np.pi * freq * t) + 0.4 * np.sin(4 * np.pi * freq * t) + 0.2 * np.sin(6 * np.pi * freq * t)
    return s * env_ad(n, 0.004, dur) * 0.25

def brass_pad(freqs, dur, amp=0.10):
    n = int(dur * SR); t = np.arange(n) / SR
    s = np.zeros(n)
    for fr in freqs:
        s += np.sin(2 * np.pi * fr * t + RNG.uniform(0, 6)) + 0.5 * np.sin(4 * np.pi * fr * t)
    vib = 1 + 0.004 * np.sin(2 * np.pi * 0.9 * t)
    s *= env_ad(n, dur * 0.25, dur * 0.5) * amp * vib
    return s

def lowpass(x, alpha):
    y = np.empty_like(x); acc = 0.0
    for i in range(len(x)):
        acc += alpha * (x[i] - acc); y[i] = acc
    return y

def drone(dur, base=52):
    n = int(dur * SR); t = np.arange(n) / SR
    s = np.zeros(n)
    for fr in (base, base * 1.5, base * 2.02):
        s += np.sin(2 * np.pi * fr * t + RNG.uniform(0, 6)) * (0.5 if fr == base else 0.22)
    wob = 1 + 0.03 * np.sin(2 * np.pi * 0.35 * t)
    return s * wob * env_ad(n, 1.2, dur * 0.6) * 0.25

# ------------------------------------------------------------- music stem
music = np.zeros(N)
BPM = 112.0
beat = 60.0 / BPM
NOTE = dict(A2=110.0, C3=130.81, D3=146.83, E3=164.81, F3=174.61, G3=196.0, A3=220.0, C4=261.63, E4=329.63)
chords = [(['A2', 'E3', 'A3', 'C4'], 0), (['F3', 'A3', 'C4', 'E4'], 2), (['C3', 'G3', 'C4', 'E4'], 4), (['G3', 'D3', 'A3', 'C4'], 6)]
STING = t_of(1085)
bass_line = ['A2', 'A2', 'E3', 'A2', 'G3', 'G3', 'D3', 'G3']  # per half-bar steps

t = 0.0
bar = 0
while t < STING - 0.3:
    ch, ci = chords[bar % 4][0], chords[bar % 4][1]
    for b in range(4):
        bt = t + b * beat
        if bt > STING - 0.3: break
        place(music, kick(0.30), bt)
        if b in (1, 3):
            place(music, snare(0.16), bt)
    # octave bass, eighth notes
    for e8 in range(8):
        bt = t + e8 * beat / 2
        seq = bass_line[(bar * 2 + e8 // 2) % 8] if bar % 2 == 0 else 'A2'
        f = NOTE[seq] * (2 if e8 % 4 == 3 else 1)
        place(music, pluck(f, beat / 2 * 0.9), bt)
    # pad every 2 bars
    if bar % 2 == 0:
        place(music, brass_pad([NOTE[n] for n in ch], beat * 8, amp=0.055), t)
    bar += 1
    t += 4 * beat

# tail: drone after the sting till end
music[int(STING * SR):] += drone(D - STING + 0.4)[:N - int(STING * SR)]
# little beat drop fade just before sting
fade = int(0.35 * SR)
music[int(STING * SR) - fade:int(STING * SR)] *= np.linspace(1, 0, fade)
sf.write('audio/music.wav', np.clip(music, -2, 2).astype('float32'), SR)

# ------------------------------------------------------------- sfx stem
sfx = np.zeros(N)

def noise_hit(dur, lp=0.25, amp=0.9):
    n = int(dur * SR)
    x = RNG.standard_normal(n) * env_ad(n, 0.003, dur)
    x = lowpass(x, lp)
    m = np.max(np.abs(x)) + 1e-9
    return x / m * amp

def thunk(amp=0.9):
    n = int(0.22 * SR); t = np.arange(n) / SR
    f = 95 * np.exp(-t * 22) + 60
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * env_ad(n, 0.002, 0.22) * amp
    nz = noise_hit(0.14, 0.12, 0.30 * amp)
    body[:len(nz)] += nz
    return body

def whoosh(dur=0.5, amp=0.5, up=True):
    n = int(dur * SR)
    x = RNG.standard_normal(n) * env_ad(n, dur * 0.45, dur * 0.5)
    a = 0.04 if up else 0.35
    y = np.empty(n); acc = 0.0
    for i in range(n):
        a2 = a + (0.35 - a) * (i / n) if up else a - (a - 0.04) * (i / n)
        acc += max(0.02, a2) * (x[i] - acc); y[i] = acc
    m = np.max(np.abs(y)) + 1e-9
    return y / m * amp

def creak(dur=0.6, amp=0.35):
    n = int(dur * SR); t = np.arange(n) / SR
    f = 320 + 90 * np.sin(2 * np.pi * 3.1 * t) + 60 * np.sin(2 * np.pi * 0.7 * t)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR)
    gr = np.sin(2 * np.pi * 47 * t)
    s = s * (0.6 + 0.4 * gr) * env_ad(n, 0.08, dur * 0.8)
    return s * amp

def ting(amp=0.5):
    n = int(1.2 * SR); t = np.arange(n) / SR
    s = np.sin(2 * np.pi * 1318 * t) + 0.6 * np.sin(2 * np.pi * 1975 * t)
    return s * env_ad(n, 0.002, 1.1) * amp

def blip(f0=880, dur=0.09, amp=0.4):
    n = int(dur * SR)
    return np.sin(2 * np.pi * f0 * np.arange(n) / SR) * env_ad(n, 0.004, dur * 0.6) * amp

def moan(amp=0.16, dur=1.6, f0=110):
    n = int(dur * SR); t = np.arange(n) / SR
    fr = f0 * (1 + 0.05 * np.sin(2 * np.pi * 1.3 * t))
    s = np.zeros(n)
    ph = np.cumsum(fr) / SR
    for k, a in ((1, 1.0), (2, 0.5), (3, 0.25)):
        s += a * np.sin(2 * np.pi * ph * k)
    s = lowpass(s, 0.15)
    m = np.max(np.abs(s)) + 1e-9
    return s / m * amp * env_ad(n, 0.3, dur * 0.5)

def beep_ring(amp=0.3):
    s = np.zeros(int(1.0 * SR))
    for k in range(4):
        place(s, blip(1400, 0.12, amp), k * 0.25)
    return s

def chirp(amp=0.22):
    n = int(0.3 * SR); t = np.arange(n) / SR
    fr = 2600 + 900 * np.sin(2 * np.pi * 14 * t)
    return np.sin(2 * np.pi * np.cumsum(fr) / SR) * env_ad(n, 0.01, 0.26) * amp

place(sfx, noise_hit(1.2, 0.06, 0.30), t_of(0))            # wake-rustle
for f in (402, 416, 436):                                   # barricade thunks (0-3 f early x words)
    place(sfx, thunk(0.95), t_of(f))
    place(sfx, noise_hit(0.2, 0.2, 0.2), t_of(f) + 0.03)
place(sfx, whoosh(0.4, 0.30), t_of(372))                    # sofa slide in
for k in range(3):
    place(sfx, beep_ring(0.34), t_of(468) + k * 1.35)       # dial beeps
place(sfx, moan(0.14, 4.0, 105), t_of(506))                 # gemidos no fone
place(sfx, moan(0.10, 2.0, 95), t_of(578))
place(sfx, noise_hit(0.25, 0.3, 0.25), t_of(1020))          # tv on blip
place(sfx, blip(520, 0.15, 0.3), t_of(1020))
place(sfx, noise_hit(0.8, 0.05, 0.18), t_of(1022))          # tv static bed
place(sfx, noise_hit(0.06, 0.5, 0.8), t_of(1084))           # low hit: sting
for k in range(3):
    place(sfx, blip(140 + k * 30, 0.5, 0.30), t_of(1085) + k * 0.5)
place(sfx, whoosh(0.45, 0.5), t_of(1152))                   # run to mirror
place(sfx, creak(0.8, 0.30), t_of(1162))
place(sfx, moan(0.10, 2.2, 98), t_of(1249))
place(sfx, ting(0.4), t_of(1450))                           # key / lotérica
place(sfx, creak(0.7, 0.2), t_of(1430))
for k in range(4):                                          # birds on the wide
    place(sfx, chirp(0.18), t_of(810) + k * 0.9)
place(sfx, creak(0.5, 0.25), t_of(1816))                    # sign drops
place(sfx, thunk(0.8), t_of(1827))
for k in range(3):                                          # final moan swell
    place(sfx, moan(0.14, 2.2, 100 + k * 8), t_of(1660) + k * 1.9)
sf.write('audio/sfx.wav', np.clip(sfx, -2, 2).astype('float32'), SR)
print('stems ok: music %.1f s, sfx peak %.2f' % (D, np.max(np.abs(sfx))))
