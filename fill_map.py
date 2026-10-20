import os, zlib, struct
from collections import deque

base = os.path.expanduser("~/earthquake_ws/damaged_building_map")
data = open(base + ".pgm", "rb").read()

# --- read the PGM header ---
tokens, i = [], 0
while len(tokens) < 4:
    if data[i:i+1] == b"#":
        while data[i:i+1] != b"\n":
            i += 1
    elif data[i:i+1].isspace():
        i += 1
    else:
        j = i
        while not data[j:j+1].isspace():
            j += 1
        tokens.append(data[i:j])
        i = j
i += 1
w, h = int(tokens[1]), int(tokens[2])
px = bytearray(data[i:i + w * h])

def save_png(path, pixels):
    raw = b"".join(b"\x00" + bytes(pixels[y*w:(y+1)*w]) for y in range(h))
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 0, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")
    open(path, "wb").write(png)

save_png(base + "_before.png", px)

def unknown(v):
    return v not in (0, 254)   # 0 = wall, 254 = free, anything else = unknown

seen = bytearray(w * h)
filled = 0
for start in range(w * h):
    if seen[start] or not unknown(px[start]):
        continue
    comp, touches_border = [], False
    q = deque([start]); seen[start] = 1
    while q:
        p = q.popleft(); comp.append(p)
        x, y = p % w, p // w
        if x == 0 or y == 0 or x == w-1 or y == h-1:
            touches_border = True
        for nx, ny in ((x+1, y), (x-1, y), (x, y+1), (x, y-1)):
            if 0 <= nx < w and 0 <= ny < h:
                n = ny * w + nx
                if not seen[n] and unknown(px[n]):
                    seen[n] = 1; q.append(n)
    if not touches_border:
        for p in comp:
            px[p] = 254
        filled += len(comp)

open(base + "_filled.pgm", "wb").write(b"P5\n%d %d\n255\n" % (w, h) + bytes(px))
save_png(base + "_after.png", px)
print("Done. Pixels filled:", filled)
