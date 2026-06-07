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
    if importer is None:
        try:
            import cadquery as cq  # type: ignore

            importer = cq.importers
        except Exception as exc:
            return {
                "status": "缺少几何内核",
                "errorMessage": str(exc),
                "message": "已读取 STEP 基础信息，但当前环境未安装 cadquery/OCP，无法计算真实长宽高、体积和表面积。",
                "lengthMm": None,
                "widthMm": None,
                "heightMm": None,
                "bboxVolumeMm3": None,
                "volumeMm3": None,
                "volumeUtilization": None,
                "outerSurfaceAreaMm2": None,
            }

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
        return {
            "status": "解析失败",
            "errorMessage": str(exc),
            "message": "STEP 文件读取失败，请检查文件是否为有效实体模型，或改用手动尺寸/截图分析。",
            "lengthMm": None,
            "widthMm": None,
            "heightMm": None,
            "bboxVolumeMm3": None,
            "volumeMm3": None,
            "volumeUtilization": None,
            "outerSurfaceAreaMm2": None,
        }
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
