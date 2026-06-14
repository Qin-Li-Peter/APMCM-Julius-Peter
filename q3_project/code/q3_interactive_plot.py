# -*- coding: utf-8 -*-
"""
Generate an offline interactive 3D Pareto plot for Problem 3.

The output is a single HTML file with embedded data and vanilla JavaScript.
It needs no network access or third-party plotting library.
"""
import csv
import json
import os


HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
OUT = os.path.join(ROOT, "outputs")
FIG = os.path.join(ROOT, "figures")


def load_rows():
    rows = []
    with open(os.path.join(OUT, "pareto_front.csv"), newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append(
                {
                    "beta": float(row["beta"]),
                    "gamma": float(row["gamma"]),
                    "Nr": int(float(row["Nr"])),
                    "R": float(row["R*"]),
                    "dP": float(row["dP*"]),
                    "Theta": float(row["Theta*"]),
                }
            )
    return rows


def load_result():
    with open(os.path.join(OUT, "q3_result.json"), encoding="utf-8") as f:
        raw = json.load(f)
    return {
        "knee": {
            "beta": raw["knee"]["beta"],
            "gamma": raw["knee"]["gamma"],
            "Nr": raw["knee"]["Nr"],
            "R": raw["knee"]["R*"],
            "dP": raw["knee"]["dP*"],
            "Theta": raw["knee"]["Theta*"],
        },
        "ideal": {
            "beta": raw["ideal_point"]["beta"],
            "gamma": raw["ideal_point"]["gamma"],
            "Nr": raw["ideal_point"]["Nr"],
            "R": raw["ideal_point"]["R*"],
            "dP": raw["ideal_point"]["dP*"],
            "Theta": raw["ideal_point"]["Theta*"],
        },
    }


def main():
    rows = load_rows()
    result = load_result()
    data_json = json.dumps(rows, ensure_ascii=False, separators=(",", ":"))
    result_json = json.dumps(result, ensure_ascii=False, separators=(",", ":"))

    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>问题三三维 Pareto 前沿交互图</title>
<style>
  :root {{
    color-scheme: light;
    --ink: #243038;
    --muted: #607d8b;
    --line: #d7e0e7;
    --panel: #f7fafc;
    --red: #c92a2a;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
    color: var(--ink);
    background: #ffffff;
  }}
  main {{
    width: min(1180px, 100vw);
    margin: 0 auto;
    padding: 18px 18px 22px;
  }}
  .toolbar {{
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
    margin-bottom: 12px;
  }}
  button, label {{
    height: 34px;
    border: 1px solid #cfd9e1;
    background: #ffffff;
    border-radius: 6px;
    color: var(--ink);
    font-size: 14px;
    padding: 0 12px;
  }}
  button {{
    cursor: pointer;
  }}
  button:hover {{
    background: #f0f5f8;
  }}
  label {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
  }}
  .hint {{
    color: var(--muted);
    font-size: 13px;
  }}
  .stage {{
    width: 100%;
    border: 1px solid #d9e2e8;
    border-radius: 8px;
    overflow: hidden;
    background: white;
  }}
  canvas {{
    display: block;
    width: 100%;
    height: min(68vh, 760px);
    min-height: 540px;
    cursor: grab;
    background: white;
  }}
  canvas:active {{
    cursor: grabbing;
  }}
  .meta {{
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
    margin-top: 12px;
  }}
  .box {{
    border: 1px solid #d9e2e8;
    border-radius: 8px;
    background: var(--panel);
    padding: 10px 12px;
    font-size: 14px;
    line-height: 1.55;
  }}
  .box strong {{
    color: var(--red);
  }}
  @media (max-width: 760px) {{
    .meta {{ grid-template-columns: 1fr; }}
    canvas {{ min-height: 460px; }}
  }}
</style>
</head>
<body>
<main>
  <div class="toolbar">
    <button id="resetBtn">重置视角</button>
    <button id="downloadBtn">下载当前视角 PNG</button>
    <label><input id="labelToggle" type="checkbox" checked> 显示两个标记文字</label>
    <span class="hint">拖动画布旋转，滚轮缩放。三个目标均为越小越好。</span>
  </div>
  <div class="stage">
    <canvas id="plot" width="1600" height="980"></canvas>
  </div>
  <div class="meta">
    <div class="box"><strong>红色五角星：膝点最终方案</strong><br>β=0.21，γ=4.5，N_r=6；R*=0.7355，ΔP*=0.0952，Θ*=0.7911</div>
    <div class="box"><strong>红色三角形：理想点辅助参考</strong><br>β=0.22，γ=4.5，N_r=4；R*=0.7413，ΔP*=0.0848，Θ*=0.7722</div>
  </div>
</main>
<script>
const rows = {data_json};
const result = {result_json};
const colors = {{
  2: "#85B7EB",
  4: "#1D9E75",
  6: "#BA7517",
  8: "#D4537E",
  10: "#534AB7"
}};
const labels = {{
  R: "R* thermal resistance",
  dP: "dP* pressure drop",
  Theta: "Theta* temperature non-uniformity"
}};
const canvas = document.getElementById("plot");
const ctx = canvas.getContext("2d");
const labelToggle = document.getElementById("labelToggle");

const bounds = ["R", "dP", "Theta"].reduce((acc, key) => {{
  const values = rows.map(d => d[key]);
  acc[key] = {{ min: Math.min(...values), max: Math.max(...values) }};
  return acc;
}}, {{}});

let yaw = -0.82;
let pitch = 0.48;
let zoom = 1.04;
let dragging = false;
let last = null;

function norm(value, key) {{
  const b = bounds[key];
  return (value - b.min) / (b.max - b.min || 1);
}}

function pointFromObj(d) {{
  return {{
    x: norm(d.R, "R") - 0.5,
    y: norm(d.dP, "dP") - 0.5,
    z: norm(d.Theta, "Theta") - 0.5
  }};
}}

function rotate(p) {{
  const cy = Math.cos(yaw), sy = Math.sin(yaw);
  const cp = Math.cos(pitch), sp = Math.sin(pitch);
  const x1 = cy * p.x - sy * p.y;
  const y1 = sy * p.x + cy * p.y;
  const z1 = p.z;
  return {{
    x: x1,
    y: cp * y1 - sp * z1,
    z: sp * y1 + cp * z1
  }};
}}

function project(p) {{
  const r = rotate(p);
  const scale = Math.min(canvas.width, canvas.height) * 0.58 * zoom;
  return {{
    x: canvas.width * 0.47 + r.x * scale,
    y: canvas.height * 0.52 - r.y * scale,
    depth: r.z
  }};
}}

function drawLine3(a, b, color, width = 2, dash = []) {{
  const pa = project(a), pb = project(b);
  ctx.save();
  ctx.strokeStyle = color;
  ctx.lineWidth = width;
  ctx.setLineDash(dash);
  ctx.beginPath();
  ctx.moveTo(pa.x, pa.y);
  ctx.lineTo(pb.x, pb.y);
  ctx.stroke();
  ctx.restore();
}}

function drawText(text, x, y, opts = {{}}) {{
  ctx.save();
  ctx.fillStyle = opts.color || "#243038";
  ctx.font = `${{opts.weight || 600}} ${{opts.size || 22}}px -apple-system, BlinkMacSystemFont, Segoe UI, Arial`;
  ctx.textAlign = opts.align || "left";
  ctx.textBaseline = opts.baseline || "middle";
  ctx.fillText(text, x, y);
  ctx.restore();
}}

function starPath(x, y, outer, inner) {{
  ctx.beginPath();
  for (let i = 0; i < 10; i++) {{
    const r = i % 2 === 0 ? outer : inner;
    const a = -Math.PI / 2 + i * Math.PI / 5;
    const px = x + Math.cos(a) * r;
    const py = y + Math.sin(a) * r;
    if (i === 0) ctx.moveTo(px, py);
    else ctx.lineTo(px, py);
  }}
  ctx.closePath();
}}

function trianglePath(x, y, r) {{
  ctx.beginPath();
  for (let i = 0; i < 3; i++) {{
    const a = -Math.PI / 2 + i * Math.PI * 2 / 3;
    const px = x + Math.cos(a) * r;
    const py = y + Math.sin(a) * r;
    if (i === 0) ctx.moveTo(px, py);
    else ctx.lineTo(px, py);
  }}
  ctx.closePath();
}}

function drawMarker(screen, shape, size) {{
  ctx.save();
  ctx.fillStyle = "#C92A2A";
  ctx.strokeStyle = "#111";
  ctx.lineWidth = 2.2;
  if (shape === "star") starPath(screen.x, screen.y, size, size * 0.42);
  else trianglePath(screen.x, screen.y, size);
  ctx.fill();
  ctx.stroke();
  ctx.restore();
}}

function drawLegend() {{
  const x = canvas.width - 330;
  let y = 78;
  drawText("Legend", x, y, {{ size: 24, weight: 700 }});
  y += 34;
  Object.keys(colors).forEach(nr => {{
    ctx.save();
    ctx.fillStyle = colors[nr];
    ctx.globalAlpha = 0.82;
    ctx.beginPath();
    ctx.arc(x + 10, y, 9, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
    drawText(`N_r=${{nr}}`, x + 30, y + 1, {{ size: 18, weight: 500 }});
    y += 30;
  }});
  y += 10;
  drawMarker({{ x: x + 10, y }}, "star", 13);
  drawText("Knee: final solution", x + 30, y + 1, {{ size: 18, weight: 500 }});
  y += 34;
  drawMarker({{ x: x + 10, y }}, "triangle", 12);
  drawText("Ideal-point reference", x + 30, y + 1, {{ size: 18, weight: 500 }});
}}

function drawAxes() {{
  const origin = {{ x: -0.5, y: -0.5, z: -0.5 }};
  const xEnd = {{ x: 0.5, y: -0.5, z: -0.5 }};
  const yEnd = {{ x: -0.5, y: 0.5, z: -0.5 }};
  const zEnd = {{ x: -0.5, y: -0.5, z: 0.5 }};
  for (const t of [0, 0.25, 0.5, 0.75, 1]) {{
    const v = t - 0.5;
    drawLine3({{ x: v, y: -0.5, z: -0.5 }}, {{ x: v, y: 0.5, z: -0.5 }}, "#d9e2e8", 1, [7, 7]);
    drawLine3({{ x: -0.5, y: v, z: -0.5 }}, {{ x: 0.5, y: v, z: -0.5 }}, "#d9e2e8", 1, [7, 7]);
    drawLine3({{ x: -0.5, y: -0.5, z: v }}, {{ x: 0.5, y: -0.5, z: v }}, "#d9e2e8", 1, [7, 7]);
    drawLine3({{ x: -0.5, y: -0.5, z: v }}, {{ x: -0.5, y: 0.5, z: v }}, "#d9e2e8", 1, [7, 7]);
  }}
  drawLine3(origin, xEnd, "#243038", 2.4);
  drawLine3(origin, yEnd, "#243038", 2.4);
  drawLine3(origin, zEnd, "#243038", 2.4);
  const px = project(xEnd), py = project(yEnd), pz = project(zEnd);
  drawText(labels.R, px.x + 10, px.y + 14, {{ size: 20, weight: 700 }});
  drawText(labels.dP, py.x + 10, py.y + 14, {{ size: 20, weight: 700 }});
  drawText(labels.Theta, pz.x + 10, pz.y - 10, {{ size: 20, weight: 700 }});
}}

function draw() {{
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = "#fff";
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  drawText("3D Pareto front of objective space", 54, 50, {{ size: 26, weight: 800 }});
  drawText("Drag to rotate, wheel to zoom. All three objectives are minimized.", 54, 84, {{ size: 18, weight: 500, color: "#607d8b" }});
  drawAxes();

  const projected = rows.map(d => {{
    const p = project(pointFromObj(d));
    return {{ ...p, d }};
  }}).sort((a, b) => a.depth - b.depth);

  for (const p of projected) {{
    ctx.save();
    ctx.globalAlpha = 0.68;
    ctx.fillStyle = colors[p.d.Nr] || "#777";
    ctx.beginPath();
    ctx.arc(p.x, p.y, 4.4, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }}

  const ideal = project(pointFromObj(result.ideal));
  const knee = project(pointFromObj(result.knee));
  drawMarker(ideal, "triangle", 20);
  drawMarker(knee, "star", 24);
  if (labelToggle.checked) {{
    drawText("Knee chosen", knee.x + 28, knee.y - 8, {{ size: 19, weight: 800 }});
    drawText("Ideal ref.", ideal.x + 28, ideal.y + 12, {{ size: 19, weight: 800 }});
  }}
  drawLegend();
}}

function resizeCanvasForDisplay() {{
  const rect = canvas.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;
  canvas.width = Math.round(rect.width * dpr);
  canvas.height = Math.round(rect.height * dpr);
  draw();
}}

canvas.addEventListener("pointerdown", e => {{
  dragging = true;
  last = {{ x: e.clientX, y: e.clientY }};
  canvas.setPointerCapture(e.pointerId);
}});
canvas.addEventListener("pointermove", e => {{
  if (!dragging) return;
  const dx = e.clientX - last.x;
  const dy = e.clientY - last.y;
  yaw += dx * 0.008;
  pitch += dy * 0.008;
  pitch = Math.max(-1.35, Math.min(1.35, pitch));
  last = {{ x: e.clientX, y: e.clientY }};
  draw();
}});
canvas.addEventListener("pointerup", () => dragging = false);
canvas.addEventListener("pointercancel", () => dragging = false);
canvas.addEventListener("wheel", e => {{
  e.preventDefault();
  zoom *= e.deltaY < 0 ? 1.08 : 0.92;
  zoom = Math.max(0.56, Math.min(2.4, zoom));
  draw();
}}, {{ passive: false }});

document.getElementById("resetBtn").addEventListener("click", () => {{
  yaw = -0.82;
  pitch = 0.48;
  zoom = 1.04;
  draw();
}});
document.getElementById("downloadBtn").addEventListener("click", () => {{
  draw();
  const a = document.createElement("a");
  a.download = "q3_pareto_3d_current_view.png";
  a.href = canvas.toDataURL("image/png");
  a.click();
}});
labelToggle.addEventListener("change", draw);
window.addEventListener("resize", resizeCanvasForDisplay);
resizeCanvasForDisplay();
</script>
</body>
</html>
"""

    os.makedirs(FIG, exist_ok=True)
    out_path = os.path.join(FIG, "fig2_pareto_3d_interactive.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(out_path)


if __name__ == "__main__":
    main()
