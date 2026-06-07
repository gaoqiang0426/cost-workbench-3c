from __future__ import annotations

from typing import Any


def generate_optimization_suggestions(
    process: str,
    material: dict[str, Any],
    analysis: dict[str, Any],
    cost_result: dict[str, Any],
) -> dict[str, list[dict[str, str]]]:
    suggestions = {
        "提高强度": [],
        "降低成本": [],
        "减少重量": [],
    }

    weight_g = float(analysis.get("weight_g") or 0)
    surface_area_cm2 = float(analysis.get("surface_area_cm2") or 0)
    complexity = analysis.get("complexity", "中")
    surface_treatment = analysis.get("surface_treatment", "无")
    unit_price = float(cost_result.get("unit_price") or 0)

    if process == "注塑件":
        suggestions["提高强度"].append(
            _item(
                "S1",
                "螺丝柱、卡扣根部增加圆角和加强筋",
                f"{material['category']}材料在尖角和根部容易形成应力集中，当前材料为{analysis['material_name']}。",
                "强度和跌落可靠性提升，模具局部复杂度小幅增加。",
            )
        )
        if weight_g > 60 or complexity == "高":
            suggestions["降低成本"].append(
                _item(
                    "C1",
                    "把厚胶位改为薄壁加筋结构",
                    "厚胶位会增加冷却时间、缩水风险和不良率，注塑周期成本会被放大。",
                    "加工费和不良率下降，需同步确认筋位缩水和外观面印痕。",
                )
            )
        if surface_treatment != "无":
            suggestions["降低成本"].append(
                _item(
                    "C2",
                    "减少非关键外观面的二次表面处理",
                    f"当前表面处理为{surface_treatment}，面积越大遮蔽和良率成本越高。",
                    "表面处理费下降，外观等级边界需重新定义。",
                )
            )
    elif process in {"CNC铝件", "铝合金冲压"}:
        suggestions["提高强度"].append(
            _item(
                "S1",
                "受力转角放大内 R 并保留连续材料",
                "铝合金在尖角、窄桥和折弯根部容易产生应力集中。",
                "疲劳和装配可靠性提升，局部空间需确认。",
            )
        )
        if process == "CNC铝件":
            suggestions["降低成本"].append(
                _item(
                    "C1",
                    "减少深腔、小 R 和多次翻面装夹",
                    "CNC 成本主要由机时驱动，深腔和小刀具会显著拉长加工时间。",
                    "加工费下降，外形和装配避位需要重新评审。",
                )
            )
        else:
            suggestions["降低成本"].append(
                _item(
                    "C1",
                    "优化排样并统一折弯方向",
                    "冲压件成本受排样利用率、工站数量和回弹校正影响。",
                    "材料损耗和加工工站下降，模具设计需同步确认。",
                )
            )
    elif process == "钣金件":
        suggestions["提高强度"].append(
            _item(
                "S1",
                "长边增加翻边或压筋",
                "钣金薄板刚度受截面高度影响明显，翻边和压筋比单纯加厚更高效。",
                "强度提升，重量变化较小，折弯顺序需确认。",
            )
        )
        suggestions["降低成本"].append(
            _item(
                "C1",
                "减少压铆件数量并合并折弯工序",
                "压铆、攻牙和多次折弯都会增加人工与设备节拍。",
                "加工费下降，装配方式需重新验证。",
            )
        )
    elif process == "锌合金压铸":
        suggestions["提高强度"].append(
            _item(
                "S1",
                "厚薄过渡区增加圆角并优化浇口方向",
                "压铸件在厚薄突变处容易产生缩水、气孔和裂纹。",
                "强度和电镀良率提升，模具流道需评估。",
            )
        )
        suggestions["降低成本"].append(
            _item(
                "C1",
                "减少高亮电镀外观面的抛光面积",
                "抛光和电镀对气孔、披锋和基材缺陷非常敏感。",
                "表面处理费和返工率下降，外观定义需确认。",
            )
        )
    else:
        suggestions["提高强度"].append(
            _item(
                "S1",
                "调整打印方向，使主受力方向避开层间弱面",
                "3D 打印件强度具有方向性，层间结合通常弱于层内。",
                "强度提升，打印时间和支撑量可能变化。",
            )
        )
        suggestions["降低成本"].append(
            _item(
                "C1",
                "减少支撑和高外观后处理区域",
                "打印成本受打印时间、支撑清理和人工打磨影响。",
                "加工费下降，外观验证面需明确。",
            )
        )

    if weight_g > 80:
        suggestions["减少重量"].append(
            _item(
                "W1",
                "低受力厚壁区域增加减重槽或改为筋位支撑",
                f"当前估算重量为{weight_g:.1f} g，重量偏高会同时推高材料费和运输/装配负担。",
                "重量和材料费下降，需校核局部刚度。",
            )
        )
    elif surface_area_cm2 > 150 and surface_treatment != "无":
        suggestions["减少重量"].append(
            _item(
                "W1",
                "收敛外观处理边界并减少非功能外露面积",
                f"当前外表面积估算为{surface_area_cm2:.1f} cm2，且包含{surface_treatment}。",
                "表面处理费下降，外观一致性需确认。",
            )
        )
    else:
        suggestions["减少重量"].append(
            _item(
                "W1",
                "保留当前重量策略，优先通过局部筋位微调",
                "当前重量和表面积没有触发明显减重风险。",
                "风险较低，适合作为下一轮结构微调项。",
            )
        )

    if unit_price > 10:
        suggestions["降低成本"].append(
            _item(
                "C3",
                "针对最高成本项做供应商询价复核",
                f"当前单件预估价为{unit_price:.2f}元，已进入需要拆分复核的区间。",
                "可快速识别材料、加工或表面处理中的主要成本驱动。",
            )
        )

    return suggestions


def _item(code: str, action: str, reason: str, impact: str) -> dict[str, str]:
    return {
        "编号": code,
        "建议动作": action,
        "工程原因": reason,
        "影响": impact,
    }

