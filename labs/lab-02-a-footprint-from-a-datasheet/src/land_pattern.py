"""The course's land-pattern arithmetic for TI's RHL0024A, from data/rhl0024a.json.

This is the method Lab 02 teaches, written out once so that the checker and the reference
solution use the same numbers. For each pair of opposite sides, with every length in mm:

    L  = the body across those sides (min..max)       C_L = L_max - L_min
    T  = the terminal length (min..max)
    S  = the span between the terminals' inner ends:  S_max = L_max - 2 T_min
                                                      S_min = L_min - 2 T_max
                                                      C_S = S_max - S_min
    W  = the terminal width (min..max)                C_W = W_max - W_min

    Z  = L_min + 2 J_T + sqrt(C_L^2 + F^2 + P^2)       outer edge to outer edge of the pads
    G  = S_max - 2 J_H - sqrt(C_S^2 + F^2 + P^2)       inner edge to inner edge
    X  = W_min + 2 J_S + sqrt(C_W^2 + F^2 + P^2)       pad width

J_T, J_H and J_S are IPC-7351B's solder-fillet goals for a no-lead part with a toe fillet,
at nominal density: toe 0.30, heel 0.00, side -0.04. They are the values KiCad's footprint
generator transcribes from IPC-7351B table 3-15 (src/kilibs/config/ipc_configs/ipc_7351b.yaml
in gitlab.com/kicad/libraries/kicad-footprint-generator, commit 090252c, as the course plan
records in its fact P2). F is the board fabricator's tolerance and P the placement
machine's; the course uses F = 0.10 and P = 0.05.

KiCad's library convention (KLC F6.3) then wants at least 0.2 mm of clearance between the
exposed pad and every other pad. Where G puts a pad's inner end closer than that to the
exposed pad, the inner end moves out to 0.2 mm from it, and the pad gets shorter.
"""
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(HERE), "data", "rhl0024a.json")

GOALS = {"toe": 0.30, "heel": 0.00, "side": -0.04}
F = 0.10
P = 0.05
EP_CLEARANCE = 0.20       # KLC F6.3
COURTYARD = 0.25          # KLC F5.3, the default courtyard clearance


def drawing():
    with open(DATA) as f:
        return json.load(f)


def side(body, term_len, term_width):
    """Z, G and X (and the intermediate numbers) for one pair of sides."""
    l_min, l_max = body["min"], body["max"]
    t_min, t_max = term_len["min"], term_len["max"]
    w_min, w_max = term_width["min"], term_width["max"]
    c_l = l_max - l_min
    s_max = l_max - 2 * t_min
    s_min = l_min - 2 * t_max
    c_s = s_max - s_min
    c_w = w_max - w_min
    fp = F ** 2 + P ** 2
    z = l_min + 2 * GOALS["toe"] + math.sqrt(c_l ** 2 + fp)
    g = s_max - 2 * GOALS["heel"] - math.sqrt(c_s ** 2 + fp)
    x = w_min + 2 * GOALS["side"] + math.sqrt(c_w ** 2 + fp)
    return {"L_min": l_min, "L_max": l_max, "C_L": c_l, "S_min": s_min, "S_max": s_max,
            "C_S": c_s, "C_W": c_w, "Z": z, "G": g, "X": x}


def compute():
    """Everything the footprint needs, rounded to 0.01 mm where it gets typed in."""
    d = drawing()
    ep_x, ep_y = d["exposed_pad_x"]["nom"], d["exposed_pad_y"]["nom"]
    out = {"exposed_pad": (ep_x, ep_y)}
    # The 20 pins on the long sides (2-11, 14-23) point along x, so they straddle the body's
    # x dimension; the 4 on the short sides (1, 12, 13, 24) point along y.
    for name, body, ep_half in (("long", d["body_x"], ep_x / 2), ("short", d["body_y"], ep_y / 2)):
        s = side(body, d["terminal_length"], d["terminal_width"])
        z, g, x = round(s["Z"], 2), round(s["G"], 2), round(s["X"], 2)
        gap = g / 2 - ep_half
        inner = max(g / 2, ep_half + EP_CLEARANCE)
        outer = z / 2
        s.update({"Z_r": z, "G_r": g, "X_r": x, "gap_at_G": gap, "inner": inner,
                  "length": round(outer - inner, 2), "centre": round((outer + inner) / 2, 2)})
        out[name] = s
    return out


if __name__ == "__main__":
    c = compute()
    for name in ("long", "short"):
        s = c[name]
        print(f"{name:5}  Z {s['Z']:.4f} -> {s['Z_r']:.2f}   G {s['G']:.4f} -> {s['G_r']:.2f}   "
              f"X {s['X']:.4f} -> {s['X_r']:.2f}   gap at G {s['gap_at_G']:.3f}   "
              f"inner {s['inner']:.3f}   length {s['length']:.2f}   centre {s['centre']:.2f}")
