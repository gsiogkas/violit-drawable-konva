# Violit Drawable Konva

Violit widget wrapping the same Konva canvas used by
[`streamlit-drawable-konva`](https://github.com/gsiogkas/streamlit-drawable-konva).

Requires **Violit ≥ 0.8.29** (`app.register_js_widget`).

## Install (editable)

```bash
cd /devel/dev/cvrlab/violit-drawable-konva
uv venv .venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

Sync the browser IIFE from the Streamlit sibling build (required before demo / packaging):

```bash
# ensure standalone.js exists in streamlit-drawable-konva first
bash scripts/sync_standalone.sh
```

Until you sync, the package falls back to:

`../streamlit-drawable-konva/streamlit_drawable_konva/frontend/build/standalone.js`

## Demo

```bash
source .venv/bin/activate
.venv/bin/violit run demo/app.py --reload --localhost --port 8031
# → http://localhost:8031
```

`demo/app.py` must end with `app.run()` (Violit does not auto-start the server).

Sidebar: drawing tool, stroke, **background color**, **background image** upload
(or “Use sample background”). Pass Violit `State` / callables into `vl_canvas`
(not `.value`) so props update live.

## Tests

```bash
pytest -q
```

## Usage

```python
import violit as vl
from violit_drawable_konva import ensure_registered, vl_canvas

app = vl.App(title="Canvas")
ensure_registered(app)  # optional; also called by vl_canvas

drawing_mode = app.state("polygon", key="drawing_mode")
stroke_width = app.state(3, key="stroke_width")
stroke_color = app.state("#111", key="stroke_color")
bg_file = app.state(None, key="bg_file")
payload = app.state({"image_data_url": None, "json_data": None}, key="c1")

app.file_uploader("Background", type=[".png", ".jpg"], bind=bg_file)

result = vl_canvas(
    app,
    drawing_mode=drawing_mode,  # State, not .value
    stroke_width=stroke_width,
    stroke_color=stroke_color,
    background_image=bg_file,   # UploadedFile / PIL / State / callable
    height=400,
    width=600,
    key="c1",
    bind=payload,
)
# result.json_data / result.image_data
```

Helpers mirror the Streamlit package: `crop_box_from_json`, `objects_by_group`,
`splines_from_json`, `spline_control_points`, `sample_spline`, `sample_catmull_rom`.

## Layout

```
violit_drawable_konva/
  api.py              # ensure_registered, vl_canvas
  payload.py          # camelCase props (shared contract)
  spline.py / helpers.py / scene_helpers.py
  static/standalone.js  # synced IIFE (window.DrawableKonvaCanvas)
demo/app.py
tests/
scripts/sync_standalone.sh
```

## First git commit

Repo is already `git init`'d on `main`. From the package root:

```bash
cd /devel/dev/cvrlab/violit-drawable-konva

# review
git status
git diff --cached
git diff

# stage everything that should ship (standalone.js is intentional)
git add .gitignore LICENSE README.md pyproject.toml \
  demo scripts tests violit_drawable_konva

# optional: leave uv.lock / .venv out (.gitignore already excludes them)

git commit -m "$(cat <<'EOF'
Initial violit-drawable-konva package.

Violit register_js_widget host for the shared Konva standalone bundle,
with demo, tests, and sync script from streamlit-drawable-konva.
EOF
)"

git status
git log -1 --stat
```

Remote (when ready):

```bash
gh repo create gsiogkas/violit-drawable-konva --public --source=. --remote=origin
git push -u origin main
```

## Manual port checklist

1. Build Streamlit frontend (`npm run build` in `streamlit-drawable-konva/.../frontend`) so `build/standalone.js` exists.
2. `bash scripts/sync_standalone.sh` into this package.
3. `uv pip install -e ".[dev]"` (needs `violit>=0.8.29`).
4. `pytest -q`.
5. `violit run demo/app.py --reload --localhost --port 8031`.
6. First commit (see above).
