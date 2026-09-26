"""Spline helpers for reading Konva spline objects from scene JSON."""

from __future__ import annotations

from typing import Any, Optional, Sequence


def _flat_to_pairs(
    flat: Sequence[float], offset_x: float = 0.0, offset_y: float = 0.0
) -> list[tuple[float, float]]:
    pairs: list[tuple[float, float]] = []
    for i in range(0, len(flat) - 1, 2):
        pairs.append((offset_x + float(flat[i]), offset_y + float(flat[i + 1])))
    return pairs


def splines_from_json(json_data: Optional[dict]) -> list[dict[str, Any]]:
    """Return all ``type: "spline"`` objects from a scene dict."""
    if not json_data:
        return []
    return [obj for obj in json_data.get("objects", []) if obj.get("type") == "spline"]


def spline_control_points(obj: dict[str, Any]) -> list[tuple[float, float]]:
    """Return click/control points for one spline object."""
    flat = obj.get("points") or []
    return _flat_to_pairs(flat, float(obj.get("x") or 0), float(obj.get("y") or 0))


def sample_catmull_rom(
    control_points: Sequence[tuple[float, float]],
    *,
    tension: float = 0.5,
    samples_per_segment: int = 16,
) -> list[tuple[float, float]]:
    """Densify an open Catmull-Rom spline through ``control_points``."""
    pts = list(control_points)
    n = len(pts)
    if n == 0:
        return []
    if n == 1:
        return [pts[0]]
    if n == 2 or tension <= 0:
        return _linear_samples(pts, max(samples_per_segment, 2))

    if samples_per_segment < 2:
        samples_per_segment = 2

    out: list[tuple[float, float]] = []
    for i in range(n - 1):
        p0 = pts[max(i - 1, 0)]
        p1 = pts[i]
        p2 = pts[i + 1]
        p3 = pts[min(i + 2, n - 1)]
        for step in range(samples_per_segment):
            t = step / samples_per_segment
            out.append(_catmull_point(p0, p1, p2, p3, t, tension))
    out.append(pts[-1])
    return out


def sample_spline(
    obj: dict[str, Any],
    *,
    samples_per_segment: int = 16,
) -> list[tuple[float, float]]:
    """Sample a spline object from scene JSON into a dense polyline."""
    control = spline_control_points(obj)
    tension = float(obj.get("tension", 0.5))
    return sample_catmull_rom(
        control,
        tension=tension,
        samples_per_segment=samples_per_segment,
    )


def _linear_samples(
    pts: Sequence[tuple[float, float]],
    samples_per_segment: int,
) -> list[tuple[float, float]]:
    if len(pts) == 1:
        return [pts[0]]
    out: list[tuple[float, float]] = []
    for i in range(len(pts) - 1):
        x1, y1 = pts[i]
        x2, y2 = pts[i + 1]
        for step in range(samples_per_segment):
            t = step / samples_per_segment
            out.append((x1 + (x2 - x1) * t, y1 + (y2 - y1) * t))
    out.append(pts[-1])
    return out


def _catmull_point(
    p0: tuple[float, float],
    p1: tuple[float, float],
    p2: tuple[float, float],
    p3: tuple[float, float],
    t: float,
    tension: float,
) -> tuple[float, float]:
    t2 = t * t
    t3 = t2 * t
    s = tension * 0.5
    x = s * (
        (2 * p1[0])
        + (-p0[0] + p2[0]) * t
        + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2
        + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3
    )
    y = s * (
        (2 * p1[1])
        + (-p0[1] + p2[1]) * t
        + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
        + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3
    )
    return (x, y)
