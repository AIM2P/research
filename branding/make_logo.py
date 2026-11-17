"""AIM²P logo generator: a properly tricolored trefoil knot around a Q.E.D. square.

Outputs SVG masters (text converted to paths, no font dependency) into the
branding folder; PNGs are rendered separately with headless Chrome.
"""
import os
import sys

import numpy as np
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)

# Palette -------------------------------------------------------------------
GOLD, CORAL, TEAL = "#F6B73C", "#EE5A3E", "#1FB28C"
IVORY = "#F7F2E6"
BG_IN, BG_OUT = "#1A3170", "#0A1430"
TEXT = "#F7F2E6"
TEXT_SOFT = "#AEB9D6"

# Classic trefoil: z(t) = i e^{-it} - 2i e^{2it} ------------------------------
# (SVG y axis points down, so the lobe at t = pi points up.)


def pt(t):
    return np.sin(t) + 2 * np.sin(2 * t), np.cos(t) - 2 * np.cos(2 * t)


# Crossings: by mirror symmetry one sits on x = 0 where cos t = -1/4; the other
# two follow by the 3-fold rotation t -> t + 2pi/3.
T0 = np.arccos(-0.25)
PAIRS = [((T0 + k * 2 * np.pi / 3) % (2 * np.pi), (-T0 + k * 2 * np.pi / 3) % (2 * np.pi)) for k in range(3)]
TS = sorted(t for p in PAIRS for t in p)
# Alternating diagram: every other passage goes over.
OVER_T = TS[0::2]
UNDER_T = TS[1::2]
# Knot-diagram "arcs" run from under-crossing to under-crossing; giving each
# arc its own colour is a valid tricoloring (3 colours meet at every crossing),
# which is the classic proof that the trefoil is knotted.
_u = UNDER_T
ARCS_T = [(_u[2] - 2 * np.pi, _u[0]), (_u[0], _u[1]), (_u[1], _u[2])]
ARC_COLOURS = [TEAL, GOLD, CORAL]  # gold = arc containing the top lobe (t = pi)
ARCS = [(a, b, c) for (a, b), c in zip(ARCS_T, ARC_COLOURS)]
OVERS = []
for t in OVER_T:
    for (a, b), c in zip(ARCS_T, ARC_COLOURS):
        if a < t < b or a < t - 2 * np.pi < b:
            OVERS.append((t, c))
SPEED_AT_CROSSING = float(np.sqrt(17 + 8 * np.cos(3 * T0)))


def bbox(stroke):
    ts = np.linspace(0, 2 * np.pi, 4000)
    x, y = pt(ts)
    h = stroke / 2
    return x.min() - h, x.max() + h, y.min() - h, y.max() + h


def knot(cx, cy, scale, uid, stroke=0.60, gap=0.17, L_over=2.0, L_cut=1.45, sq=0.62, W=1024, H=1024):
    """(cx, cy) is the centre of the knot's bounding box."""
    x0, x1, y0, y1 = bbox(stroke)
    ox = cx - scale * (x0 + x1) / 2
    oy = cy - scale * (y0 + y1) / 2
    w_over = L_over / SPEED_AT_CROSSING
    w_cut = L_cut / SPEED_AT_CROSSING
    def path(t0, t1, n=360):
        ts = np.linspace(t0, t1, n)
        x, y = pt(ts)
        X, Y = ox + scale * x, oy + scale * y
        return "M" + " L".join(f"{a:.2f},{b:.2f}" for a, b in zip(X, Y))

    s = stroke * scale
    cut = (stroke + 2 * gap) * scale
    out = [f'<mask id="cut-{uid}" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}">',
           f'<rect width="{W}" height="{H}" fill="#fff"/>']
    for t, _ in OVERS:
        out.append(f'<path d="{path(t - w_cut, t + w_cut, 80)}" fill="none" stroke="#000" '
                   f'stroke-width="{cut:.2f}" stroke-linecap="butt" stroke-linejoin="round"/>')
    out.append("</mask>")
    out.append(f'<g mask="url(#cut-{uid})" fill="none" stroke-width="{s:.2f}" stroke-linecap="butt" stroke-linejoin="round">')
    for t0, t1, col in ARCS:
        out.append(f'<path d="{path(t0, t1)}" stroke="{col}"/>')
    out.append("</g>")
    out.append(f'<g fill="none" stroke-width="{s:.2f}" stroke-linecap="butt" stroke-linejoin="round">')
    for t, col in OVERS:
        out.append(f'<path d="{path(t - w_over, t + w_over, 100)}" stroke="{col}"/>')
    out.append("</g>")
    a = sq * scale
    out.append(f'<rect x="{ox - a / 2:.2f}" y="{oy - a / 2:.2f}" width="{a:.2f}" height="{a:.2f}" '
               f'rx="{a * 0.06:.2f}" fill="{IVORY}"/>')
    return "\n".join(out)


def background(W, H, uid):
    return (f'<defs><radialGradient id="bg-{uid}" cx="50%" cy="46%" r="70%">'
            f'<stop offset="0" stop-color="{BG_IN}"/><stop offset="1" stop-color="{BG_OUT}"/>'
            f'</radialGradient></defs><rect width="{W}" height="{H}" fill="url(#bg-{uid})"/>')


def svg(W, H, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">\n'
            f'<title>AIM²P</title>\n{body}\n</svg>\n')


# Text as outlines ----------------------------------------------------------
FONT_PATH = r"C:\Windows\Fonts\bahnschrift.ttf"
_fonts = {}


def font(wght):
    if wght not in _fonts:
        f = TTFont(FONT_PATH)
        _fonts[wght] = instancer.instantiateVariableFont(f, {"wght": wght, "wdth": 100})
    return _fonts[wght]


def text(s, x, y, size, wght, fill, tracking=0.0):
    f = font(wght)
    gs, cmap, upm, hmtx = f.getGlyphSet(), f.getBestCmap(), f["head"].unitsPerEm, f["hmtx"]
    sc = size / upm
    pen = SVGPathPen(gs)
    for ch in s:
        g = cmap.get(ord(ch))
        if g is None:
            raise ValueError(f"missing glyph {ch!r}")
        gs[g].draw(TransformPen(pen, (sc, 0, 0, -sc, x, y)))
        x += hmtx[g][0] * sc + tracking * size
    return f'<path d="{pen.getCommands()}" fill="{fill}"/>', x


def text_width(s, size, wght, tracking=0.0):
    return text(s, 0, 0, size, wght, "#000", tracking)[1]


def cap_height(wght):
    f = font(wght)
    return f["OS/2"].sCapHeight / f["head"].unitsPerEm


def wordmark(x, y, size):
    """AIM²P with a gold superscript 2. Returns (svg, end_x)."""
    parts = []
    p, x = text("AIM", x, y, size, 700, TEXT, 0.02)
    parts.append(p)
    sup = size * 0.52
    p, x = text("2", x + size * 0.01, y - size * cap_height(700) + sup * cap_height(700), sup, 700, GOLD)
    parts.append(p)
    p, x = text("P", x + size * 0.035, y, size, 700, TEXT, 0.02)
    parts.append(p)
    return "\n".join(parts), x


# 1) Avatar 1024x1024 (GitHub organisation picture) --------------------------
W = H = 1024
scale = 128
avatar = background(W, H, "a") + knot(W / 2, H / 2 - 4, scale, "a", W=W, H=H)
open(os.path.join(OUT, "aim2p-logo.svg"), "w", encoding="utf-8").write(svg(W, H, avatar))

# 2) Transparent mark ---------------------------------------------------------
mark = knot(W / 2, H / 2 - 4, scale, "m", W=W, H=H)
open(os.path.join(OUT, "aim2p-mark-transparent.svg"), "w", encoding="utf-8").write(svg(W, H, mark))

# 3) Banner 1280x640 (social preview + README header) ------------------------
W, H = 1280, 640
body = [background(W, H, "b"), knot(372, 318, 74, "b", W=W, H=H)]
tx = 668
wm, wm_end = wordmark(tx, 318, 150)
body.append(wm)
line1 = "African AI for Mathematics"
line2 = "& Mathematical Physics"
for i, ln in enumerate((line1, line2)):
    p, _ = text(ln, tx + 4, 392 + i * 44, 36, 350, TEXT_SOFT, 0.01)
    body.append(p)
# engines legend with the knot colours
lx, ly, ls = tx + 4, 520, 26
for col, label in ((GOLD, "LLM"), (CORAL, "SymPy"), (TEAL, "Lean 4")):
    body.append(f'<rect x="{lx:.1f}" y="{ly - ls * 0.72:.1f}" width="{ls * 0.72:.1f}" height="{ls * 0.72:.1f}" rx="2" fill="{col}"/>')
    p, end = text(label, lx + ls * 1.05, ly, ls, 500, TEXT, 0.02)
    body.append(p)
    lx = end + ls * 1.3
open(os.path.join(OUT, "aim2p-banner.svg"), "w", encoding="utf-8").write(svg(W, H, "\n".join(body)))
print("ok", wm_end, lx)
