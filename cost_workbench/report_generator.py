from __future__ import annotations

from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from cost_workbench.cost_engine import breakdown_rows


REPORT_TITLE = "3C 结构件成本预估报告"


def build_report(
    part_name: str,
    process: str,
    cost_result: dict[str, Any],
    inputs: dict[str, Any],
    route_steps: list[dict[str, str]] | None = None,
    suggestions: dict[str, list[dict[str, str]]] | None = None,
) -> dict[str, Any]:
    cost_breakdown = breakdown_rows(cost_result)
    report_suggestions = suggestions or _optimization_suggestions(process)

    return {
        "title": REPORT_TITLE,
        "part_name": part_name or "未命名结构件",
        "process": process,
        "inputs": inputs,
        "cost_breakdown": cost_breakdown,
        "total_price": cost_result["unit_price"],
        "notes": cost_result.get("notes", []),
        "risks": _risk_notes(process, inputs, cost_result),
        "suggestions": report_suggestions,
        "route_steps": route_steps or [],
        "pages": [
            {
                "name": "分析与成本",
                "sections": ["输入摘要", "成本拆解", "工艺风险"],
            },
            {
                "name": "局部优化建议",
                "sections": ["提高强度", "降低成本", "减少重量"],
            },
        ],
    }


def generate_pdf_report(report: dict[str, Any]) -> bytes:
    _register_chinese_font()

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
        title=report["title"],
    )

    styles = _styles()
    story = [
        Paragraph(report["title"], styles["TitleCN"]),
        Spacer(1, 5 * mm),
        Paragraph(f"零件名称：{report['part_name']}", styles["BodyCN"]),
        Paragraph(f"工艺路线：{report['process']}", styles["BodyCN"]),
        Paragraph(f"最终单件预估价：{report['total_price']:.2f} 元/件", styles["HighlightCN"]),
        Spacer(1, 5 * mm),
        Paragraph("第一页：分析与成本", styles["HeadingCN"]),
        Spacer(1, 3 * mm),
        Paragraph("输入摘要", styles["SubHeadingCN"]),
        _dict_table(report["inputs"]),
        Spacer(1, 4 * mm),
        Paragraph("成本拆解", styles["SubHeadingCN"]),
        _rows_table(report["cost_breakdown"]),
        Spacer(1, 4 * mm),
        Paragraph("工艺风险与说明", styles["SubHeadingCN"]),
    ]

    for note in [*report["notes"], *report["risks"]]:
        story.append(Paragraph(f"• {note}", styles["BodyCN"]))

    if report.get("route_steps"):
        story.extend(
            [
                Spacer(1, 4 * mm),
                Paragraph("工艺路线", styles["SubHeadingCN"]),
                _route_table(report["route_steps"]),
            ]
        )

    story.extend(
        [
            PageBreak(),
            Paragraph("第二页：局部优化建议", styles["HeadingCN"]),
            Spacer(1, 4 * mm),
        ]
    )

    for group_name, items in report["suggestions"].items():
        story.append(Paragraph(group_name, styles["SubHeadingCN"]))
        for item in items:
            story.append(
                Paragraph(
                    f"{item['编号']}：{item['建议动作']}。原因：{item['工程原因']}。影响：{item['影响']}",
                    styles["BodyCN"],
                )
            )
        story.append(Spacer(1, 3 * mm))

    doc.build(story)
    return buffer.getvalue()


def _register_chinese_font() -> None:
    if "STSong-Light" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "TitleCN": ParagraphStyle(
            "TitleCN",
            parent=base["Title"],
            fontName="STSong-Light",
            fontSize=18,
            leading=24,
            textColor=colors.HexColor("#1f2937"),
        ),
        "HeadingCN": ParagraphStyle(
            "HeadingCN",
            parent=base["Heading1"],
            fontName="STSong-Light",
            fontSize=15,
            leading=20,
            spaceBefore=6,
            spaceAfter=6,
        ),
        "SubHeadingCN": ParagraphStyle(
            "SubHeadingCN",
            parent=base["Heading2"],
            fontName="STSong-Light",
            fontSize=12,
            leading=16,
            spaceBefore=4,
            spaceAfter=4,
        ),
        "BodyCN": ParagraphStyle(
            "BodyCN",
            parent=base["BodyText"],
            fontName="STSong-Light",
            fontSize=9.5,
            leading=14,
        ),
        "HighlightCN": ParagraphStyle(
            "HighlightCN",
            parent=base["BodyText"],
            fontName="STSong-Light",
            fontSize=12,
            leading=16,
            textColor=colors.HexColor("#0f766e"),
        ),
    }


def _dict_table(values: dict[str, Any]) -> Table:
    rows = [["参数", "数值"], *[[str(key), str(value)] for key, value in values.items()]]
    return _table(rows, [55 * mm, 110 * mm])


def _rows_table(rows: list[dict[str, Any]]) -> Table:
    table_rows = [["成本项", "金额(元/件)"]]
    table_rows.extend([[row["成本项"], f"{row['金额(元/件)']:.2f}"] for row in rows])
    return _table(table_rows, [90 * mm, 45 * mm])


def _route_table(rows: list[dict[str, str]]) -> Table:
    table_rows = [["步骤", "工序", "说明", "成本项"]]
    for index, row in enumerate(rows, start=1):
        table_rows.append(
            [str(index), row["name"], row["description"], row["cost_item"]]
        )
    return _table(table_rows, [12 * mm, 30 * mm, 90 * mm, 28 * mm])


def _table(rows: list[list[str]], col_widths: list[float]) -> Table:
    table = Table(rows, colWidths=col_widths, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), "STSong-Light"),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e5e7eb")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#111827")),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def _risk_notes(
    process: str, inputs: dict[str, Any], cost_result: dict[str, Any]
) -> list[str]:
    notes = [
        "当前报价为早期预估，正式报价需结合结构图纸、外观面定义和供应商制程能力确认。",
        "缺少 STEP 实际体积时，材料费仍需在后续几何解析完成后校准。",
    ]
    if process == "注塑件":
        notes.append("注塑件需重点确认壁厚均匀性、缩水、披锋、拔模角和模具穴数。")
    if cost_result["unit_price"] < 0.5:
        notes.append("单件价格较低，需注意最小订单量、包装、损耗和物流成本是否被低估。")
    if inputs.get("不良率") in {"0%", "0.0%"}:
        notes.append("不良率设置为 0，量产阶段通常需要保留爬坡良率风险。")
    return notes


def _optimization_suggestions(process: str) -> dict[str, list[dict[str, str]]]:
    common = {
        "提高强度": [
            {
                "编号": "S1",
                "建议动作": "在螺丝柱、卡扣根部或受力转角增加圆角和加强筋",
                "工程原因": "降低应力集中，提高装配和跌落可靠性",
                "影响": "强度提升，重量和模具复杂度小幅增加",
            }
        ],
        "降低成本": [
            {
                "编号": "C1",
                "建议动作": "减少非关键外观面的二次表面处理面积",
                "工程原因": "喷涂、电镀、阳极等表面处理按面积和遮蔽复杂度计费",
                "影响": "成本下降，外观一致性需工程确认",
            }
        ],
        "减少重量": [
            {
                "编号": "W1",
                "建议动作": "在低受力厚壁区域增加减重槽或调整为筋位支撑",
                "工程原因": "降低材料用量并改善成型冷却",
                "影响": "重量下降，需避免缩水和局部强度不足",
            }
        ],
    }

    if process == "CNC铝件":
        common["降低成本"].append(
            {
                "编号": "C2",
                "建议动作": "放大内 R 并减少深腔加工",
                "工程原因": "小刀具和深腔会显著增加加工时间与断刀风险",
                "影响": "加工费下降，结构空间需同步确认",
            }
        )
    elif process == "注塑件":
        common["降低成本"].append(
            {
                "编号": "C2",
                "建议动作": "优化壁厚均匀性并减少厚胶位",
                "工程原因": "厚胶位会增加周期、缩水和不良率",
                "影响": "周期和不良率下降，模具流动性需评估",
            }
        )
    return common
