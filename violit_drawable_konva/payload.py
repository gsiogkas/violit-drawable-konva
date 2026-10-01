"""Build canvas widget props (shared camelCase contract with the Konva frontend).

Violit resolves ``State`` / zero-arg callables on each render, so those may be
passed through for reactive fields (e.g. ``drawingMode``).
"""

from __future__ import annotations

import inspect
from typing import Any, Optional


def _is_reactive(value: Any) -> bool:
    if callable(value) and not inspect.isclass(value):
        # Duck-type Violit State / ComputedState without importing violit here.
        if hasattr(value, "value") and hasattr(value, "set"):
            return True
        try:
            signature = inspect.signature(value)
        except (TypeError, ValueError):
            return False
        return all(
            parameter.kind
            in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
            or parameter.default is not inspect.Parameter.empty
            for parameter in signature.parameters.values()
        )
    return hasattr(value, "value") and hasattr(value, "set")


def _unwrap(value: Any) -> Any:
    if hasattr(value, "value") and hasattr(value, "set"):
        return value.value
    if callable(value) and not inspect.isclass(value) and _is_reactive(value):
        return value()
    return value


def build_component_data(
    *,
    fill_color: Any,
    stroke_width: Any,
    stroke_color: Any,
    background_color: Any,
    background_image_url: Any,
    update_streamlit: Any,
    height: Any,
    width: Any,
    drawing_mode: Any,
    initial_drawing: Any,
    display_toolbar: Any,
    point_display_radius: Any,
    enable_viewport_controls: Any,
    transform_options: Optional[Any] = None,
    spline_show_control_points: Any = False,
    spline_control_point_radius: Any = 5,
    tools: Optional[Any] = None,
    display_tool_picker: Any = False,
) -> dict[str, Any]:
    if _is_reactive(drawing_mode) or _is_reactive(update_streamlit):
        def realtime_update() -> bool:
            mode = _unwrap(drawing_mode)
            enabled = bool(_unwrap(update_streamlit))
            return enabled and mode not in ("polygon", "spline")

        realtime: Any = realtime_update
    else:
        realtime = bool(update_streamlit) and drawing_mode not in ("polygon", "spline")

    if tools is None:
        tools_prop: Any = []
    elif _is_reactive(tools):
        tools_prop = tools
    else:
        tools_prop = list(tools) if tools else []

    return {
        "fillColor": fill_color,
        "strokeWidth": stroke_width,
        "strokeColor": stroke_color,
        "backgroundColor": background_color,
        "backgroundImageURL": background_image_url,
        "realtimeUpdateStreamlit": realtime,
        "canvasHeight": height,
        "canvasWidth": width,
        "drawingMode": drawing_mode,
        "initialDrawing": initial_drawing,
        "displayToolbar": display_toolbar,
        "displayRadius": point_display_radius,
        "enableViewportControls": enable_viewport_controls,
        "transformOptions": transform_options or {},
        "splineShowControlPoints": spline_show_control_points,
        "splineControlPointRadius": spline_control_point_radius,
        "tools": tools_prop,
        "displayToolPicker": display_tool_picker,
    }
