import os, math

base = os.path.expanduser("~/earthquake_ws/damaged_building_map_filled")
STAND_OFF = 1.2     # metres between robot and wall
CLEARANCE = 0.6     # metres of free space needed around the robot

# ---- read the yaml (resolution + origin) ----
res, origin = 0.05, (0.0, 0.0)
for line in open(base + ".yaml"):
    if line.startswith("resolution:"):
        res = float(line.split(":")[1])
    if line.startswith("origin:"):
        nums = line.split("[")[1].split("]")[0].split(",")
        origin = (float(nums[0]), float(nums[1]))

# ---- read the pgm ----
data = open(base + ".pgm", "rb").read()
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
px = data[i:i + w * h]

def occ(x, y):  return px[y * w + x] == 0
def free(x, y): return px[y * w + x] == 254

# ---- find the 4 walls: rows/columns with a long line of black pixels ----
MIN_LINE = int(2.0 / res)
cols = [x for x in range(w) if sum(occ(x, y) for y in range(h)) >= MIN_LINE]
rows = [y for y in range(h) if sum(occ(x, y) for x in range(w)) >= MIN_LINE]
x_l, x_r, y_t, y_b = cols[0], cols[-1], rows[0], rows[-1]   # pixel positions

def to_map(cx, cy):          # pixel -> map metres
    return origin[0] + (cx + 0.5) * res, origin[1] + (h - 1 - cy + 0.5) * res

rad = int(CLEARANCE / res)
def clear(cx, cy):
    if not (0 <= cx < w and 0 <= cy < h) or not free(cx, cy):
        return False
    for yy in range(cy - rad, cy + rad + 1):
        for xx in range(cx - rad, cx + rad + 1):
            if 0 <= xx < w and 0 <= yy < h and occ(xx, yy):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= rad * rad:
                    return False
    return True

off = int(STAND_OFF / res)
mid_x, mid_y = (x_l + x_r) // 2, (y_t + y_b) // 2
walls = [
    ("top wall (+y)",    lambda s: (mid_x + s, y_t), (0, 1),  (1, 0)),
    ("right wall (+x)",  lambda s: (x_r, mid_y + s), (-1, 0), (0, 1)),
    ("bottom wall (-y)", lambda s: (mid_x + s, y_b), (0, -1), (1, 0)),
    ("left wall (-x)",   lambda s: (x_l, mid_y + s), (1, 0),  (0, 1)),
]

result = []
for name, wall_at, inward, _ in walls:
    found = None
    for k in range(0, 70):
        for s in ((0,) if k == 0 else (k * 5, -k * 5)):
            wx, wy = wall_at(s)
            sx, sy = wx + inward[0] * off, wy + inward[1] * off
            if clear(sx, sy):
                found = (wx, wy, sx, sy); break
        if found:
            break
    if not found:
        print("No safe spot found for", name); continue
    wx, wy, sx, sy = found
    X, Y = to_map(sx, sy)
    WX, WY = to_map(wx, wy)
    yaw = math.atan2(WY - Y, WX - X)
    result.append((name, X, Y, yaw))

with open(os.path.expanduser("~/earthquake_ws/waypoints.txt"), "w") as f:
    for name, X, Y, yaw in result:
        f.write("%.2f %.2f %.3f\n" % (X, Y, yaw))
        print("%-18s stand at x=%.2f y=%.2f, face yaw=%.2f rad" % (name, X, Y, yaw))
print("Saved ~/earthquake_ws/waypoints.txt")
