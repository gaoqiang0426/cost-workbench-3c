from __future__ import annotations

import re
import tempfile
from pathlib import Path
from typing import Any


def analyze_step_file(file_name: str, content: bytes) -> dict[str, Any]:
    extension = Path(file_name).suffix.lower()
    text = content[:250_000].decode("utf-8", errors="ignore")
    schema_match = re.search(r"FILE_SCHEMA\s*\(\s*\(\s*'([^']+)'", text, re.I)
    entity_count = len(re.findall(r"^#\d+\s*=", text, re.M))
    geometry = parse_step_geometry(file_name, content)

    base = {
        "file_name": file_name,
        "extension": extension,
        "size_kb": round(len(content) / 1024, 1),
        "schema": schema_match.group(1) if schema_match else "未识别",
        "entity_count": entity_count,
    }
    base.update(geometry)
    return base


def parse_step_geometry(
    file_name: str,
    content: bytes,
    importer: Any | None = None,
) -> dict[str, Any]:
    if importer is False:
        return _parse_step_point_bounds(content)

    if importer is None:
        try:
            import cadquery as cq  # type: ignore

            importer = cq.importers
        except Exception as exc:
            lightweight = _parse_step_point_bounds(content)
            if lightweight["status"] == "轻量解析成功":
                lightweight["errorMessage"] = str(exc)
                return lightweight
            return _empty_geometry_result(
                "缺少几何内核",
                str(exc),
                "已读取 STEP 基础信息，但当前环境未安装 cadquery/OCP，无法计算真实长宽高、体积和表面积。",
            )

    suffix = Path(file_name).suffix.lower() or ".step"
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(content)
            temp_path = temp_file.name

        workplane = importer.importStep(temp_path)
        shape = _shape_from_workplane(workplane)
        bbox = shape.BoundingBox()

        length = _number_value(bbox, "xlen")
        width = _number_value(bbox, "ylen")
        height = _number_value(bbox, "zlen")
        bbox_volume = length * width * height
        volume = _number_value(shape, "Volume")
        area = _number_value(shape, "Area")

        return {
            "status": "解析成功",
            "errorMessage": "",
            "message": "STEP 几何解析成功，已计算包围盒、体积和外表面积。",
            "lengthMm": round(length, 3),
            "widthMm": round(width, 3),
            "heightMm": round(height, 3),
            "bboxVolumeMm3": round(bbox_volume, 3),
            "volumeMm3": round(volume, 3),
            "volumeUtilization": round(volume / bbox_volume, 4) if bbox_volume else None,
            "outerSurfaceAreaMm2": round(area, 3),
        }
    except Exception as exc:
        lightweight = _parse_step_point_bounds(content)
        if lightweight["status"] == "轻量解析成功":
            lightweight["errorMessage"] = str(exc)
            return lightweight
        return _empty_geometry_result(
            "解析失败",
            str(exc),
            "STEP 文件读取失败，请检查文件是否为有效实体模型，或改用手动尺寸/截图分析。",
        )
    finally:
        if temp_path:
            try:
                Path(temp_path).unlink(missing_ok=True)
            except Exception:
                pass


def analyze_images(images: list[dict[str, Any]]) -> dict[str, Any]:
    items = []
    for image in images:
        name = image["name"]
        items.append(
            {
                "file_name": name,
                "size_kb": round(image.get("size", 0) / 1024, 1),
                "view_type": infer_view_type(name),
                "status": "已接收",
            }
        )

    return {
        "count": len(items),
        "is_enough_for_report": len(items) >= 3,
        "items": items,
        "message": "至少 3 张 Creo 截图可生成完整报告；当前视图类型为基于文件名的预识别，可由用户后续修正。",
    }


def infer_view_type(file_name: str) -> str:
    lower = file_name.lower()
    if any(key in lower for key in ["iso", "3d", "perspective", "轴测", "透视"]):
        return "3D 视图"
    if any(key in lower for key in ["front", "正", "主视"]):
        return "前视图"
    if any(key in lower for key in ["top", "俯", "上"]):
        return "上视图"
    if any(key in lower for key in ["side", "侧"]):
        return "侧视图"
    if any(key in lower for key in ["section", "detail", "剖", "局部"]):
        return "剖视/局部细节"
    return "未识别"


def _parse_step_point_bounds(content: bytes) -> dict[str, Any]:
    text = content[:2_000_000].decode("utf-8", errors="ignore")
    points: list[tuple[float, float, float]] = []
    pattern = re.compile(
        r"CARTESIAN_POINT\s*\([^()]*,\s*\(\s*([-+0-9.Ee]+)\s*,\s*([-+0-9.Ee]+)\s*,\s*([-+0-9.Ee]+)\s*\)\s*\)",
        re.I,
    )
    for match in pattern.finditer(text):
        try:
            points.append(tuple(float(value) for value in match.groups()))
        except ValueError:
            continue

    if len(points) < 2:
        return _empty_geometry_result(
            "轻量解析失败",
            "",
            "未在 STEP 文本中识别到足够的 CARTESIAN_POINT 坐标，无法估算外形尺寸。",
        )

    xs, ys, zs = zip(*points)
    length = max(xs) - min(xs)
    width = max(ys) - min(ys)
    height = max(zs) - min(zs)
    bbox_volume = length * width * height
    bbox_area = 2 * (length * width + length * height + width * height)

    return {
        "status": "轻量解析成功",
        "errorMessage": "",
        "message": "云端已使用 STEP 坐标点轻量解析外形长宽高；体积为包围盒估算，真实实体体积需完整 CAD 几何内核。",
        "lengthMm": round(length, 3),
        "widthMm": round(width, 3),
        "heightMm": round(height, 3),
        "bboxVolumeMm3": round(bbox_volume, 3),
        "volumeMm3": None,
        "volumeUtilization": None,
        "outerSurfaceAreaMm2": round(bbox_area, 3),
    }


def _empty_geometry_result(status: str, error_message: str, message: str) -> dict[str, Any]:
    return {
        "status": status,
        "errorMessage": error_message,
        "message": message,
        "lengthMm": None,
        "widthMm": None,
        "heightMm": None,
        "bboxVolumeMm3": None,
        "volumeMm3": None,
        "volumeUtilization": None,
        "outerSurfaceAreaMm2": None,
    }


def _shape_from_workplane(workplane: Any) -> Any:
    if hasattr(workplane, "val"):
        return workplane.val()
    if hasattr(workplane, "objects") and workplane.objects:
        return workplane.objects[0]
    return workplane


def _number_value(target: Any, name: str) -> float:
    value = getattr(target, name)
    if callable(value):
        value = value()
    return float(value)
