"""mix.py — voice + stems with the kit's level contract:
music = 50% of voice gated RMS (-6 dB), sfx = 50% with peaks capped at 0.7x voice peak,
one linear gain to ~-14 LUFS + -1 dBFS peak limiter on the whole mix. No ducking/comp."""
import numpy as np, soundfile as sf, sys, os

SR = 44100
VOICE = sys.argv[1]
MUSIC = sys.argv[2] if len(sys.argv) > 2 else 'audio/music.wav'
SFX = sys.argv[3] if len(sys.argv) > 3 else 'audio/sfx.wav'
OUT = sys.argv[4] if len(sys.argv) > 4 else 'audio/mix.wav'

# K-weighting (BS.1770-3ish): high-shelf +4dB@1.68k, high-pass 38 Hz
def biquad(x, b, a):
    y = np.zeros_like(x)
    x1 = x2 = y1 = y2 = 0.0
    for i in range(len(x)):
        y[i] = b[0] * x[i] + b[1] * x1 + b[2] * x2 - a[1] * y1 - a[2] * y2
        x2, x1 = x1, x[i]; y2, y1 = y1, y[i]
    return y

def kweight(x):
    # stage 1 shelf
    f0, G, Q = 1681.974450955533, 3.999843853973347, 0.7071752369554196
    K = np.tan(np.pi * f0 / SR)
    Vh = 10 ** (G / 20.0); Vb = Vh ** 0.4996667741545416
    a0_ = 1.0 + K / Q + K * K
    num = [(Vh + Vb * K / Q + K * K), 2 * (K * K - Vh), (Vh - Vb * K / Q + K * K)]
    den = [1.0, 2 * (K * K - 1) / a0_, (1 - K / Q + K * K) / a0_]
    b = [n / a0_ for n in num]
    y = biquad(x, b, den)
    # stage 2 high-pass
    f0, Q = 38.13547087602444, 0.5003270373238773
    K = np.tan(np.pi * f0 / SR)
    b = [1.0, -2.0, 1.0]
    a = [1.0, 2 * (K * K - 1) / (1 + K / Q + K * K), (1 - K / Q + K * K) / (1 + K / Q + K * K)]
    a = [v / a[0] for v in a]
    return biquad(y, b, a)

def gated_rms(x):
    x = kweight(np.asarray(x, dtype='float64'))
    blk = int(0.4 * SR); hop = blk // 4
    n = (len(x) - blk) // hop
    ms = np.array([np.mean(x[i * hop:i * hop + blk] ** 2) for i in range(max(1, n))])
    lufs_blk = 10 * np.log10(ms + 1e-12) - 0.691
    abs_g = lufs_blk > -70.0
    if not abs_g.any(): return float(np.sqrt(np.mean(x ** 2)) + 1e-12)
    rel_thr = 10 * np.log10(np.mean(ms[abs_g]) + 1e-12) - 0.691 - 10.0
    g = abs_g & (lufs_blk > rel_thr)
    if not g.any(): g = abs_g
    return float(np.sqrt(np.mean(ms[g])))

def load_mono(path):
    x, sr = sf.read(path, dtype='float32')
    if x.ndim > 1: x = x.mean(axis=1)
    return x

v = load_mono(VOICE)
m = load_mono(MUSIC); s = load_mono(SFX)
L = max(len(v), len(m), len(s))
v = np.pad(v, (0, L - len(v))); m = np.pad(m, (0, L - len(m))); s = np.pad(s, (0, L - len(s)))

rv, rm, rs = gated_rms(v), gated_rms(m), gated_rms(s)
gm = 0.5 * rv / rm
pv, ps = np.max(np.abs(v)), np.max(np.abs(s))
gs = 0.5 * rv / rs
if ps * gs > 0.7 * pv:
    gs *= (0.7 * pv) / (ps * gs)
    capped = True
else:
    capped = False
mix = v + gm * m + gs * s

# one linear gain to ~-14 LUFS integrated + -1 dBFS peak limiter
i_lufs = 10 * np.log10(gated_rms(mix) ** 2 + 1e-12) - 0.691
gain = 10 ** ((-14.0 - i_lufs) / 20.0)
mix = gain * mix
lim = 10 ** (-1.0 / 20.0)
over = np.abs(mix) > lim
if over.any():
    knee = lim * 0.8
    x = np.abs(mix)
    soft = np.where(x > knee, knee + (lim - knee) * (1 - np.exp(-(x - knee) / max(1e-9, (lim - knee)))), x)
    mix = np.sign(mix) * soft
sf.write(OUT, mix.astype('float32'), SR)

rv_db = 20 * np.log10(rv + 1e-12)
print('voice peak %.3f, gated RMS %.4f (%.1f dB)' % (pv, rv, rv_db))
print('music %.1f dB vs voice (target -6.0)' % (20 * np.log10(gm * rm / rv + 1e-12)))
print('sfx   %.1f dB vs voice (cap: %s, peak now %.3f vs %.3f = 0.7x voice)'
      % (20 * np.log10(gs * rs / rv + 1e-12), capped, np.max(np.abs(gs * s)), 0.7 * pv))
print('integrated LUFS before gain %.1f -> after gain/limiter: measure with QA' % i_lufs)
