# -*- coding: utf-8 -*-
"""
Matplotlib-free SVG fallback for q2 plots.

Reads q2_run.py outputs and writes the same three SVG figure files expected by
the README. This is useful on machines where matplotlib is not installed.
"""
import json
import os

import numpy as np
import pandas as pd


HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "outputs")
FIG = os.path.join(HERE, "..", "figures")
os.makedirs(FIG, exist_ok=True)

TARGETS = ["R*", "dP*", "Theta*"]
MODELS = ["PhysElasticNet", "GP_Kriging", "QuadRSM", "RandomForest"]
MLAB = {
    "PhysElasticNet": "Phys ElasticNet",
    "GP_Kriging": "GP (Kriging)",
    "QuadRSM": "Quad RSM",
    "RandomForest": "Random Forest",
}
COL = {
    "PhysElasticNet": "#534AB7",
    "GP_Kriging": "#0F6E56",
    "QuadRSM": "#BA7517",
    "RandomForest": "#888780",
}


def esc(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def text(x, y, body, size=12, anchor="middle", fill="#202124", weight="normal"):
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" '
        f'font-family="Arial, Helvetica, sans-serif" text-anchor="{anchor}" '
        f'font-weight="{weight}" fill="{fill}">{esc(body)}</text>'
    )


def line(x1, y1, x2, y2, stroke="#d0d0d0", width=1, dash=""):
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    return (
        f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
        f'stroke="{stroke}" stroke-width="{width}"{dash_attr}/>'
    )


def rect(x, y, w, h, fill, stroke="none"):
    return (
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
        f'fill="{fill}" stroke="{stroke}"/>'
    )


def circle(x, y, r, fill, stroke="white", opacity=0.8):
    return (
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{fill}" '
        f'stroke="{stroke}" stroke-width="0.6" opacity="{opacity}"/>'
    )


def polyline(points, stroke, width=2):
    pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    return f'<polyline points="{pts}" fill="none" stroke="{stroke}" stroke-width="{width}"/>'


def svg(width, height, body):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">\n'
        '<rect width="100%" height="100%" fill="white"/>\n'
        + "\n".join(body)
        + "\n</svg>\n"
    )


def save(name, content):
    with open(os.path.join(FIG, name), "w", encoding="utf-8") as f:
        f.write(content)


def map_y(v, lo, hi, top, bottom):
    if hi == lo:
        return (top + bottom) / 2
    return bottom - (v - lo) / (hi - lo) * (bottom - top)


def map_x(v, lo, hi, left, right):
    if hi == lo:
        return (left + right) / 2
    return left + (v - lo) / (hi - lo) * (right - left)


def plot_model_comparison(res):
    width, height = 760, 430
    left, right, top, bottom = 70, 730, 55, 330
    body = []
    body.append(text(width / 2, 28, "Four-model comparison (leave-one-out)", 16, weight="bold"))

    for q in [0.4, 0.6, 0.8, 1.0]:
        y = map_y(q, 0.4, 1.02, top, bottom)
        body.append(line(left, y, right, y, "#e3e3e3"))
        body.append(text(left - 12, y + 4, f"{q:.1f}", 10, anchor="end", fill="#5f6368"))
    body.append(line(left, top, left, bottom, "#5f6368"))
    body.append(line(left, bottom, right, bottom, "#5f6368"))
    body.append(text(22, (top + bottom) / 2, "LOO Q2", 12, anchor="middle"))

    group_w = (right - left) / len(TARGETS)
    bar_w = 28
    for ti, target in enumerate(TARGETS):
        cx = left + group_w * (ti + 0.5)
        body.append(text(cx, bottom + 28, target, 12))
        for mi, model in enumerate(MODELS):
            q2 = res[target][model]["Q2_LOO"]
            x = cx + (mi - 1.5) * (bar_w + 4) - bar_w / 2
            y = map_y(q2, 0.4, 1.02, top, bottom)
            body.append(rect(x, y, bar_w, bottom - y, COL[model]))

    lx, ly = 170, 365
    for i, model in enumerate(MODELS):
        x = lx + (i % 2) * 250
        y = ly + (i // 2) * 24
        body.append(rect(x, y - 11, 14, 14, COL[model]))
        body.append(text(x + 22, y, MLAB[model], 11, anchor="start"))
    save("fig1_model_comparison.svg", svg(width, height, body))


def plot_gp_pred_actual(res, npz):
    width, height = 1080, 390
    margin = 56
    panel_w = 310
    gap = 36
    top, bottom = 62, 310
    body = []
    body.append(text(width / 2, 28, "GP (Kriging) leave-one-out: predicted vs actual", 16, weight="bold"))
    for i, target in enumerate(TARGETS):
        left = margin + i * (panel_w + gap)
        right = left + panel_w
        y = npz[f"{target}__actual"]
        yh = npz[f"{target}__GP_Kriging"]
        lo = float(min(y.min(), yh.min()))
        hi = float(max(y.max(), yh.max()))
        pad = (hi - lo) * 0.05 if hi > lo else 1.0
        lo -= pad
        hi += pad

        body.append(text((left + right) / 2, 50, f"{target}  Q2={res[target]['GP_Kriging']['Q2_LOO']:.4f}", 13))
        for frac in [0, 0.25, 0.5, 0.75, 1]:
            gx = left + frac * (right - left)
            gy = top + frac * (bottom - top)
            body.append(line(gx, top, gx, bottom, "#eeeeee"))
            body.append(line(left, gy, right, gy, "#eeeeee"))
        body.append(line(left, bottom, right, bottom, "#5f6368"))
        body.append(line(left, top, left, bottom, "#5f6368"))
        body.append(line(left, bottom, right, top, "#888780", 1, "5,5"))

        for actual, pred in zip(y, yh):
            x = map_x(float(actual), lo, hi, left, right)
            yy = map_y(float(pred), lo, hi, top, bottom)
            body.append(circle(x, yy, 3.4, "#0F6E56"))
        body.append(text((left + right) / 2, bottom + 32, f"actual {target}", 11))
        body.append(text(left - 34, (top + bottom) / 2, f"pred {target}", 11))
    save("fig2_gp_pred_vs_actual.svg", svg(width, height, body))


def plot_main_effects(df):
    width, height = 1080, 840
    left0, top0 = 62, 56
    panel_w, panel_h = 290, 205
    gap_x, gap_y = 45, 48
    vars_ = ["beta", "gamma", "Nr"]
    labels = {"beta": "beta", "gamma": "gamma", "Nr": "Nr"}
    target_cols = {"R*": "R", "dP*": "dP", "Theta*": "Theta"}
    target_colours = {"R*": "#185FA5", "dP*": "#A32D2D", "Theta*": "#0F6E56"}
    body = [text(width / 2, 28, "Main effects (group means)", 16, weight="bold")]

    for i, target in enumerate(TARGETS):
        for j, var in enumerate(vars_):
            left = left0 + j * (panel_w + gap_x)
            top = top0 + i * (panel_h + gap_y)
            right = left + panel_w
            bottom = top + panel_h
            grouped = df.groupby(var)[target_cols[target]].mean().reset_index()
            xs = grouped[var].to_numpy(dtype=float)
            ys = grouped[target_cols[target]].to_numpy(dtype=float)
            xlo, xhi = float(xs.min()), float(xs.max())
            ylo, yhi = float(ys.min()), float(ys.max())
            ypad = (yhi - ylo) * 0.08 if yhi > ylo else 1.0
            ylo -= ypad
            yhi += ypad

            for frac in [0, 0.25, 0.5, 0.75, 1]:
                gx = left + frac * (right - left)
                gy = top + frac * (bottom - top)
                body.append(line(gx, top, gx, bottom, "#eeeeee"))
                body.append(line(left, gy, right, gy, "#eeeeee"))
            body.append(line(left, bottom, right, bottom, "#5f6368"))
            body.append(line(left, top, left, bottom, "#5f6368"))
            pts = [(map_x(x, xlo, xhi, left, right), map_y(y, ylo, yhi, top, bottom)) for x, y in zip(xs, ys)]
            body.append(polyline(pts, target_colours[target]))
            for x, y in pts:
                body.append(circle(x, y, 3.8, target_colours[target]))
            body.append(text((left + right) / 2, top - 10, f"{target} vs {labels[var]}", 12))
            body.append(text((left + right) / 2, bottom + 28, labels[var], 11))
            if j == 0:
                body.append(text(left - 36, (top + bottom) / 2, f"mean {target}", 11))
    save("fig3_main_effects.svg", svg(width, height, body))


def main():
    with open(os.path.join(OUT, "results.json"), encoding="utf-8") as f:
        res = json.load(f)["results"]
    npz = np.load(os.path.join(OUT, "loo_predictions.npz"))
    df = pd.read_csv(os.path.join(OUT, "data_clean.csv"))
    plot_model_comparison(res)
    plot_gp_pred_actual(res, npz)
    plot_main_effects(df)
    print("[已保存到 figures/] fig1_model_comparison.svg | fig2_gp_pred_vs_actual.svg | fig3_main_effects.svg")


if __name__ == "__main__":
    main()
