"""Scene JSON helpers shared with streamlit-drawable-konva."""

from __future__ import annotations

from typing import Optional


def crop_box_from_json(
    json_data: Optional[dict],
) -> Optional[tuple[int, int, int, int]]:
    """Return ``(x, y, width, height)`` for the crop object in a scene, if any."""
    if not json_data:
        return None
    for obj in json_data.get("objects", []):
        if obj.get("type") != "crop":
            continue
        try:
            return (
                int(obj["x"]),
                int(obj["y"]),
                int(obj["width"]),
                int(obj["height"]),
            )
        except (KeyError, TypeError, ValueError):
            return None
    return None


def objects_by_group(json_data: Optional[dict]) -> dict[str, list[str]]:
    """Map group ids (or ungrouped object ids) to member object ids."""
    if not json_data:
        return {}

    children_by_group: dict[str, list[str]] = {}
    for obj in json_data.get("objects", []):
        if obj.get("type") == "group":
            children_by_group[obj["id"]] = list(obj.get("children") or [])

    result: dict[str, list[str]] = {}
    for obj in json_data.get("objects", []):
        if obj.get("type") == "group":
            continue
        gid = obj.get("groupId")
        if gid:
            result.setdefault(gid, []).append(obj["id"])
        else:
            result.setdefault(obj["id"], []).append(obj["id"])

    for gid, children in children_by_group.items():
        if gid not in result:
            result[gid] = list(children)

    return result
