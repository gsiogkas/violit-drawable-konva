"""Demo app for violit-drawable-konva.

    violit run demo/app.py --reload --localhost --port 8031
"""

from __future__ import annotations

import json

import violit as vl
from PIL import Image, ImageDraw

from violit_drawable_konva import (
    ensure_registered,
    sample_spline,
    spline_control_points,
    splines_from_json,
    vl_canvas,
)

app = vl.App(title="Violit Drawable Konva Demo", theme="light")
ensure_registered(app)

drawing_mode = app.state("freedraw", key="drawing_mode")
stroke_width = app.state(3, key="stroke_width")
stroke_color = app.state("#111111", key="stroke_color")
bg_color = app.state("#ffffff", key="bg_color")
bg_file = app.state(None, key="bg_file")
use_sample_bg = app.state(False, key="use_sample_bg")
show_spline_points = app.state(False, key="show_spline_points")
canvas_payload = app.state(
    {"image_data_url": None, "json_data": None},
    key="canvas_payload",
)

MODES = (
    "freedraw",
    "line",
    "rect",
    "rect_crop",
    "circle",
    "transform",
    "polygon",
    "spline",
    "point",
    "pan",
)

CANVAS_W = 720
CANVAS_H = 420


def _sample_background() -> Image.Image:
    img = Image.new("RGB", (CANVAS_W, CANVAS_H), "#dce8f5")
    draw = ImageDraw.Draw(img)
    step = 40
    for x in range(0, CANVAS_W, step):
        draw.line([(x, 0), (x, CANVAS_H)], fill="#b7c9dc", width=1)
    for y in range(0, CANVAS_H, step):
        draw.line([(0, y), (CANVAS_W, y)], fill="#b7c9dc", width=1)
    draw.rectangle([80, 60, 280, 200], outline="#2a6f97", width=3)
    draw.text((90, 70), "sample bg", fill="#1b4332")
    return img


def _background_image():
    if use_sample_bg.value:
        return _sample_background()
    return bg_file.value


with app.sidebar:
    app.markdown("### Configuration")
    app.selectbox("Drawing tool", options=list(MODES), bind=drawing_mode)
    app.slider("Stroke width", min_value=1, max_value=40, step=1, bind=stroke_width)
    app.color_picker("Stroke color", bind=stroke_color)
    app.color_picker("Background color", bind=bg_color)
    app.file_uploader(
        "Background image",
        type=[".png", ".jpg", ".jpeg", ".webp"],
        bind=bg_file,
        key="bg_upload",
    )
    app.checkbox("Use sample background", bind=use_sample_bg)
    app.checkbox("Show spline control points", bind=show_spline_points)
    app.markdown(
        """
**Tips**

- **polygon**: left-click points, right-click to close
- **spline**: left-click control points, right-click to finish;
  double-click / Backspace / Undo removes the last point
- **transform**: double-click an object to remove it
- Background image overrides background color (same as Streamlit)
"""
    )

app.markdown("# Drawable Konva (Violit)")
app.markdown(
    "Same Konva canvas as `streamlit-drawable-konva`, hosted via "
    "`register_js_widget`."
)

# Pass Violit State / callables (not .value) so the JS widget gets update() on change.
vl_canvas(
    app,
    fill_color="rgba(255, 165, 0, 0.3)",
    stroke_width=stroke_width,
    stroke_color=stroke_color,
    background_color=bg_color,
    background_image=_background_image,
    height=CANVAS_H,
    width=CANVAS_W,
    drawing_mode=drawing_mode,
    display_toolbar=True,
    spline_show_control_points=show_spline_points,
    key="demo_canvas",
    bind=canvas_payload,
)


@app.reactivity
def scene_panel():
    payload = canvas_payload.value or {}
    json_data = payload.get("json_data")
    if not json_data:
        app.markdown("_Draw something to see coordinates / scene JSON here._")
        return

    import pandas as pd

    objects = json_data.get("objects") or []
    app.markdown(f"**Objects:** {len(objects)}")

    if objects:
        # Flatten scene objects so x/y/width/height/points are visible (like Streamlit demo).
        rows = []
        for obj in objects:
            row = {
                "id": obj.get("id"),
                "type": obj.get("type"),
                "x": obj.get("x"),
                "y": obj.get("y"),
                "width": obj.get("width"),
                "height": obj.get("height"),
                "radius": obj.get("radius"),
                "points": obj.get("points"),
                "groupId": obj.get("groupId"),
            }
            rows.append(row)
        df = pd.DataFrame(rows)
        # stringify nested lists for the grid
        if "points" in df.columns:
            df["points"] = df["points"].map(
                lambda v: "" if v is None else str(v)
            )
        app.markdown("#### Coordinates (from `json_data.objects`)")
        app.dataframe(df, height=220, hide_index=True, key="objects_df")

    for spline in splines_from_json(json_data):
        control = spline_control_points(spline)
        dense = sample_spline(spline, samples_per_segment=8)
        app.markdown(
            f"**Spline `{spline.get('id')}`** — {len(control)} control points "
            f"→ {len(dense)} sampled"
        )
        app.dataframe(
            pd.DataFrame(control, columns=["x", "y"]),
            height=160,
            hide_index=True,
            key=f"spline_ctrl_{spline.get('id')}",
        )

    app.markdown("#### Raw `json_data`")
    app.code(json.dumps(json_data, indent=2)[:6000], language="json")


scene_panel()

app.run()
