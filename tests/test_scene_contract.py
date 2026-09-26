from __future__ import annotations

from typing import Any

from violit_drawable_konva.payload import build_component_data


def test_build_component_data_defaults():
    data = build_component_data(
        fill_color="#eee",
        stroke_width=3,
        stroke_color="#000",
        background_color="#fff",
        background_image_url=None,
        update_streamlit=True,
        height=400,
        width=600,
        drawing_mode="freedraw",
        initial_drawing={"version": "konva-1", "objects": []},
        display_toolbar=True,
        point_display_radius=3,
        enable_viewport_controls=True,
    )
    assert data["transformOptions"] == {}
    assert data["drawingMode"] == "freedraw"
    assert data["canvasHeight"] == 400


def test_build_component_data_forwards_transform_options():
    opts = {"allow_scale": False, "allow_rotate": True}
    data = build_component_data(
        fill_color="#eee",
        stroke_width=3,
        stroke_color="#000",
        background_color="#fff",
        background_image_url=None,
        update_streamlit=True,
        height=300,
        width=500,
        drawing_mode="transform",
        initial_drawing={"version": "konva-1", "objects": []},
        display_toolbar=True,
        point_display_radius=3,
        enable_viewport_controls=False,
        transform_options=opts,
    )
    assert data["transformOptions"] == opts


def test_build_component_data_spline_defers_realtime_updates():
    data = build_component_data(
        fill_color="#eee",
        stroke_width=3,
        stroke_color="#000",
        background_color="#fff",
        background_image_url=None,
        update_streamlit=True,
        height=400,
        width=600,
        drawing_mode="spline",
        initial_drawing={"version": "konva-1", "objects": []},
        display_toolbar=True,
        point_display_radius=3,
        enable_viewport_controls=True,
    )
    assert data["drawingMode"] == "spline"
    assert data["realtimeUpdateStreamlit"] is False


def test_build_component_data_spline_control_points():
    data = build_component_data(
        fill_color="#eee",
        stroke_width=3,
        stroke_color="#000",
        background_color="#fff",
        background_image_url=None,
        update_streamlit=True,
        height=400,
        width=600,
        drawing_mode="spline",
        initial_drawing={"version": "konva-1", "objects": []},
        display_toolbar=True,
        point_display_radius=3,
        enable_viewport_controls=True,
        spline_show_control_points=True,
        spline_control_point_radius=7,
    )
    assert data["splineShowControlPoints"] is True
    assert data["splineControlPointRadius"] == 7


def test_build_component_data_polygon_defers_realtime_updates():
    data = build_component_data(
        fill_color="#eee",
        stroke_width=3,
        stroke_color="#000",
        background_color="#fff",
        background_image_url=None,
        update_streamlit=True,
        height=400,
        width=600,
        drawing_mode="polygon",
        initial_drawing={"version": "konva-1", "objects": []},
        display_toolbar=True,
        point_display_radius=3,
        enable_viewport_controls=True,
    )
    assert data["realtimeUpdateStreamlit"] is False


def test_build_component_data_reactive_drawing_mode():
    mode = {"value": "freedraw"}

    class FakeState:
        def __init__(self):
            self._v = "freedraw"

        @property
        def value(self):
            return self._v

        def set(self, v):
            self._v = v

    state = FakeState()
    data = build_component_data(
        fill_color="#eee",
        stroke_width=3,
        stroke_color="#000",
        background_color="#fff",
        background_image_url=None,
        update_streamlit=True,
        height=400,
        width=600,
        drawing_mode=state,
        initial_drawing={"version": "konva-1", "objects": []},
        display_toolbar=True,
        point_display_radius=3,
        enable_viewport_controls=True,
    )
    assert data["drawingMode"] is state
    assert callable(data["realtimeUpdateStreamlit"])
    assert data["realtimeUpdateStreamlit"]() is True
    state.set("spline")
    assert data["realtimeUpdateStreamlit"]() is False


def test_spline_control_points_and_sampling():
    from violit_drawable_konva import (
        sample_spline,
        spline_control_points,
        splines_from_json,
    )

    scene = {
        "objects": [
            {
                "id": "s1",
                "type": "spline",
                "points": [0, 0, 100, 0, 100, 100],
                "tension": 0.5,
            }
        ]
    }
    splines = splines_from_json(scene)
    assert len(splines) == 1
    control = spline_control_points(splines[0])
    assert control == [(0.0, 0.0), (100.0, 0.0), (100.0, 100.0)]

    dense = sample_spline(splines[0], samples_per_segment=4)
    assert len(dense) > len(control)
    assert dense[0] == control[0]
    assert dense[-1] == control[-1]


def test_objects_by_group():
    from violit_drawable_konva import objects_by_group

    scene = {
        "objects": [
            {"id": "g1", "type": "group", "children": ["a", "b"]},
            {"id": "a", "type": "circle", "groupId": "g1"},
            {"id": "b", "type": "circle", "groupId": "g1"},
            {"id": "solo", "type": "rect"},
        ]
    }
    grouped = objects_by_group(scene)
    assert set(grouped["g1"]) == {"a", "b"}
    assert grouped["solo"] == ["solo"]


def test_crop_box_from_json():
    from violit_drawable_konva import crop_box_from_json

    scene: dict[str, Any] = {
        "objects": [
            {"id": "c1", "type": "crop", "x": 10, "y": 20, "width": 100, "height": 50}
        ]
    }
    assert crop_box_from_json(scene) == (10, 20, 100, 50)
    assert crop_box_from_json(None) is None


def test_resolve_standalone_or_dev_fallback():
    from violit_drawable_konva.api import _resolve_standalone

    path = _resolve_standalone()
    assert path.name == "standalone.js"
    assert path.is_file()


def test_background_image_to_data_url():
    from PIL import Image

    from violit_drawable_konva.api import _background_image_to_data_url

    img = Image.new("RGB", (20, 10), color=(255, 0, 0))
    url = _background_image_to_data_url(img, height=40, width=80)
    assert url is not None
    assert url.startswith("data:image/png;base64,")
    assert _background_image_to_data_url(None, 40, 80) is None
