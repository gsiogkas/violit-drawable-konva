"""Python API for the Violit drawable Konva widget."""

from __future__ import annotations

import base64
import io
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional

from violit_drawable_konva.payload import build_component_data

WIDGET_NAME = "drawable_konva"
STATIC_MOUNT_PATH = "/violit-drawable-konva"

_PACKAGE_ROOT = Path(__file__).resolve().parent
_STATIC_CANDIDATES = (
    _PACKAGE_ROOT / "static" / "standalone.js",
    # Dev fallback: sibling streamlit-drawable-konva build output
    _PACKAGE_ROOT.parents[1]
    / "streamlit-drawable-konva"
    / "streamlit_drawable_konva"
    / "frontend"
    / "build"
    / "standalone.js",
)


def _resolve_standalone() -> Path:
    for path in _STATIC_CANDIDATES:
        if path.is_file():
            return path
    raise FileNotFoundError(
        "standalone.js not found. Run scripts/sync_standalone.sh from the "
        "repo root after building streamlit-drawable-konva, or place "
        "standalone.js under violit_drawable_konva/static/."
    )


# Packaged static dir (standalone.js lives here after sync).
STATIC_DIR = _PACKAGE_ROOT / "static"


@dataclass
class CanvasResult:
    """Latest canvas output (mirrors streamlit-drawable-konva)."""

    image_data: Optional[Any] = None  # numpy ndarray when available
    json_data: Optional[dict] = None


_MOUNT_JS = r"""
var api = window.DrawableKonvaCanvas;
if (!api || typeof api.mount !== "function") {
  console.error("DrawableKonvaCanvas.mount missing — is standalone.js loaded?");
  return {};
}
var controller = api.mount(element, props || {}, function (payload) {
  emit("change", payload);
});
return {
  update: function (nextProps) {
    if (controller && typeof controller.update === "function") {
      controller.update(nextProps || {});
    }
  },
  destroy: function () {
    if (controller && typeof controller.destroy === "function") {
      controller.destroy();
    }
  }
};
"""


def _data_url_to_image(data_url: str):
    from PIL import Image

    _, encoded = data_url.split(";base64,", 1)
    return Image.open(io.BytesIO(base64.b64decode(encoded)))


def _image_to_data_url(img) -> str:
    from PIL import Image

    if not isinstance(img, Image.Image):
        raise TypeError("background_image must be a PIL Image")
    buf = io.BytesIO()
    img.convert("RGBA").save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{b64}"


def _resize_img(img, height: int, width: int):
    return img.resize((width, height))


def ensure_registered(app: Any) -> None:
    """Register the JS widget and mount static assets on ``app`` (idempotent)."""
    if getattr(app, "_vl_drawable_konva_registered", False):
        return

    standalone = _resolve_standalone()
    static_dir = str(standalone.parent)

    # Serve the IIFE bundle.
    from fastapi.staticfiles import StaticFiles

    fastapi = getattr(app, "fastapi", None)
    if fastapi is None:
        raise RuntimeError("Violit app has no .fastapi attribute")

    # Avoid double-mount errors on reload.
    routes = {getattr(r, "path", None) for r in getattr(fastapi, "routes", [])}
    if STATIC_MOUNT_PATH not in routes:
        fastapi.mount(
            STATIC_MOUNT_PATH,
            StaticFiles(directory=static_dir),
            name="violit_drawable_konva_static",
        )

    app.register_js_widget(
        WIDGET_NAME,
        mount_js=_MOUNT_JS,
        js=[f"{STATIC_MOUNT_PATH}/standalone.js"],
        events=["change"],
        expose_method=False,
    )
    app._vl_drawable_konva_registered = True


def _concrete(value: Any) -> Any:
    """Unwrap a Violit State-like object for one-shot uses (layout CSS, PIL)."""
    if hasattr(value, "value") and hasattr(value, "set"):
        return value.value
    return value


def _is_stateful(value: Any) -> bool:
    return hasattr(value, "value") and hasattr(value, "set")


def _coerce_pil_image(source: Any):
    """Turn a PIL image, file-like, path, or data-URL into a PIL Image."""
    from PIL import Image

    if source is None:
        return None
    if isinstance(source, Image.Image):
        return source
    if isinstance(source, str) and source.startswith("data:image"):
        return _data_url_to_image(source)
    if isinstance(source, (bytes, bytearray)):
        return Image.open(io.BytesIO(source))
    if hasattr(source, "read"):
        try:
            source.seek(0)
        except Exception:
            pass
        return Image.open(source)
    return Image.open(source)


def _background_image_to_data_url(source: Any, height: int, width: int) -> Optional[str]:
    """Resize ``source`` to canvas size and return a PNG data URL, or None."""
    if source is None:
        return None
    img = _coerce_pil_image(source)
    if img is None:
        return None
    return _image_to_data_url(_resize_img(img, height, width))


def _reactive_or_value(value: Any, resolve: Callable[[Any], Any]) -> Any:
    """If ``value`` is State/callable, return a zero-arg resolver; else resolve now."""
    if _is_stateful(value):

        def _resolve_state() -> Any:
            return resolve(value.value)

        return _resolve_state
    if callable(value) and not isinstance(value, type):

        def _resolve_call() -> Any:
            return resolve(value())

        return _resolve_call
    return resolve(value)


def vl_canvas(
    app: Any,
    *,
    fill_color: Any = "#eee",
    stroke_width: Any = 20,
    stroke_color: Any = "black",
    background_color: Any = "",
    background_image: Any = None,
    update_host: Any = True,
    height: Any = 400,
    width: Any = 600,
    drawing_mode: Any = "freedraw",
    initial_drawing: Optional[dict] = None,
    display_toolbar: Any = True,
    point_display_radius: Any = 3,
    enable_viewport_controls: Any = True,
    transform_options: Optional[dict] = None,
    spline_show_control_points: Any = False,
    spline_control_point_radius: Any = 5,
    key: Optional[str] = None,
    bind: Any = None,
    on_change: Optional[Callable[[dict], None]] = None,
) -> CanvasResult:
    """Render a drawable Konva canvas in a Violit app.

    Parameters mirror ``streamlit_drawable_konva.st_canvas`` where possible.
    ``update_host`` maps to the frontend ``realtimeUpdateStreamlit`` flag.

    Prefer ``bind=`` a Violit ``State`` for reactive access to the latest
    ``{image_data_url, json_data}`` payload, or read the returned ``CanvasResult``.

    Pass Violit ``State`` (not ``.value``) for ``drawing_mode``, stroke props,
    ``background_image``, etc. so the JS widget receives ``update()`` when they
    change. ``background_image`` accepts a PIL image, file-like (e.g. Violit
    ``UploadedFile``), path, bytes, data URL, or a State/callable yielding one.
    When an image is set, ``background_color`` is cleared (same as Streamlit).
    """
    ensure_registered(app)

    widget_key = key or "drawable_konva"
    result_key = f"vl_drawable_konva_result__{widget_key}"

    if bind is not None:
        result_state = bind
    else:
        store = getattr(app, "_vl_drawable_konva_states", None)
        if store is None:
            store = {}
            app._vl_drawable_konva_states = store
        if result_key not in store:
            store[result_key] = app.state(
                {"image_data_url": None, "json_data": None},
                key=result_key,
            )
        result_state = store[result_key]

    layout_h = int(_concrete(height))
    layout_w = int(_concrete(width))

    def _resolve_bg_image(src: Any) -> Optional[str]:
        return _background_image_to_data_url(src, layout_h, layout_w)

    background_image_url = _reactive_or_value(background_image, _resolve_bg_image)

    def _resolve_bg_color(color: Any) -> Any:
        # Image wins over solid background (streamlit-drawable-konva behavior).
        img_url = (
            background_image_url()
            if callable(background_image_url)
            else background_image_url
        )
        if img_url:
            return ""
        return color if color is not None else ""

    if (
        _is_stateful(background_image)
        or callable(background_image)
        or _is_stateful(background_color)
        or callable(background_color)
    ):

        def bg_color() -> Any:
            color = (
                background_color.value
                if _is_stateful(background_color)
                else background_color()
                if callable(background_color) and not isinstance(background_color, type)
                else background_color
            )
            return _resolve_bg_color(color)
    else:
        bg_color = _resolve_bg_color(background_color)

    if initial_drawing is None:
        base_scene: dict[str, Any] = {"version": "konva-1", "objects": []}
    else:
        base_scene = dict(initial_drawing)

    if callable(bg_color) and not isinstance(bg_color, type):

        def scene() -> dict[str, Any]:
            out = dict(base_scene)
            out["background"] = bg_color()
            return out
    else:
        scene = dict(base_scene)
        scene["background"] = bg_color

    props = build_component_data(
        fill_color=fill_color,
        stroke_width=stroke_width,
        stroke_color=stroke_color,
        background_color=bg_color,
        background_image_url=background_image_url,
        update_streamlit=update_host,
        height=height,
        width=width,
        drawing_mode=drawing_mode,
        initial_drawing=scene,
        display_toolbar=display_toolbar,
        point_display_radius=point_display_radius,
        enable_viewport_controls=enable_viewport_controls,
        transform_options=transform_options,
        spline_show_control_points=spline_show_control_points,
        spline_control_point_radius=spline_control_point_radius,
    )

    def _handle_change(payload: Any = None) -> None:
        data = payload if isinstance(payload, dict) else {}
        result_state.set(
            {
                "image_data_url": data.get("image_data_url"),
                "json_data": data.get("json_data"),
            }
        )
        if on_change is not None:
            on_change(data)

    app.widget(
        WIDGET_NAME,
        key=widget_key,
        on_change=_handle_change,
        style=f"width:{layout_w}px;min-height:{layout_h}px;",
        **props,
    )

    current = result_state.value or {}
    image_data = None
    image_data_url = current.get("image_data_url")
    if image_data_url:
        try:
            import numpy as np

            image_data = np.asarray(_data_url_to_image(image_data_url))
        except Exception:
            image_data = None

    return CanvasResult(image_data=image_data, json_data=current.get("json_data"))
