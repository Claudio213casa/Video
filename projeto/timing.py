import json, re, sys
import numpy as np, soundfile as sf

WAV = sys.argv[1]; TXT = sys.argv[2]; OUT = sys.argv[3]
sr = 44100
x, sr = sf.read(WAV, dtype='float32')
if x.ndim > 1: x = x.mean(axis=1)
D = len(x)/sr
hop = 441; win = 882
n = (len(x)-win)//hop
rms = np.sqrt(np.mean(x[:n*hop].reshape(n, hop)**2, axis=1))
floor = np.percentile(rms, 20)
peak = rms.max()
thr = max(floor*4, peak*0.06)
speech = rms > thr
# smooth: close gaps < 0.12 s, drop segments < 0.09 s
def close(mask, gap_frames):
    idx = np.flatnonzero(np.diff(mask.astype(int)))
    segs = list(zip(idx[::2], idx[1::2]))
    return mask
# scipy not installed; do manual morph ops
def dilate(m, k):
    out = m.copy()
    for i in range(1, k+1):
        out[i:] |= m[:-i]; out[:-i] |= m[i:]
    return out
def erode(m, k):
    out = m.copy()
    for i in range(1, k+1):
        out[i:] &= m[:-i]; out[:-i] &= m[i:]
    return out
m = dilate(speech, 12)      # close gaps <= 120 ms
m = erode(m, 12)
# segments > 90 ms
segs = []
i = 0
while i < n:
    if m[i]:
        j = i
        while j < n and m[j]: j += 1
        if (j-i)*hop/sr >= 0.09: segs.append((i*hop/sr, j*hop/sr))
        i = j
    else: i += 1
speech_total = sum(e-s for s, e in segs)
print('speech regions:', len(segs), 'speech total %.2f s of %.2f s' % (speech_total, D), file=sys.stderr)

# phrases: sentence-level split
lines = [l.strip() for l in open(TXT, encoding='utf-8') if l.strip()]
phrases = []
for li, line in enumerate(lines):
    line = re.sub(r'^"|"$', '', line)
    for part in re.split(r'(?<=[.,:!?])\s+', line):
        if part: phrases.append(part)

def syls(w):
    w = re.sub(r'[^a-zà-ú]', '', w.lower())
    if not w: return 1
    v = 'aeiouáéíóúâêôãõà'
    cnt, prev = 0, False
    for ch in w:
        cur = ch in v
        if cur and not prev: cnt += 1
        prev = cur
    return max(1, cnt)

words = []
for pi, p in enumerate(phrases):
    ws = p.split()
    for wi, w in enumerate(ws):
        words.append((pi, wi, syls(w)))
total_syl = sum(s for _, _, s in words)
k = speech_total/total_syl

t = segs[0][0]; si = 0
placed = []
for pi, wi, s in words:
    dur = k*s
    # if inside silence, jump to next speech start, record pause
    while si < len(segs) and t >= segs[si][1]:
        si += 1
    if si >= len(segs):
        e = min(t+dur, D); placed.append((pi, wi, t, e)); t = e; continue
    if t < segs[si][0]: t = segs[si][0]
    e = t+dur
    # cap word end at region end (remainder continues in next region)
    if e > segs[si][1]: e = segs[si][1]
    placed.append((pi, wi, t, e)); t = e

# phrase spans + internal pause fraction
phrases_out = []
for pi, p in enumerate(phrases):
    ws = [(w, s, e) for (tpi, w, s, e) in [(a, b, c, d) for a, b, c, d in placed] if False]
ws = [(a, b, c, d) for a, b, c, d in placed]
for pi, p in enumerate(phrases):
    spans = [(c, d) for (a, b, c, d) in ws if a == pi]
    start, end = spans[0][0], spans[-1][1]
    # internal silence between first word start and last word end
    internal = 0.0
    for (rs, re_) in segs:
        for (c1, d1), (c2, d2) in zip(spans, spans[1:]):
            gap_s, gap_e = d1, c2
            ov = max(0, min(gap_e, re_)-max(gap_s, rs))
            internal += ov
    nwords = len(spans)
    phrases_out.append(dict(i=pi, text=p, f0=round(start*30), f1=round(end*30),
                            t0=round(start, 3), t1=round(end, 3), words=nwords,
                            pause_ms=round(internal*1000)))
json.dump(dict(duration=D, frames=round(D*30), phrases=phrases_out),
          open(OUT+'/phrases.json', 'w'), ensure_ascii=False, indent=1)
for p in phrases_out:
    print('f%4d-%4d  %5.2fs  pausa%4dms  %s' % (p['f0'], p['f1'], p['t1']-p['t0'], p['pause_ms'], p['text']))
