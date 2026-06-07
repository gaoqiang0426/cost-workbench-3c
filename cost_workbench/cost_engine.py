from __future__ import annotations

from dataclasses import dataclass
from typing import Any


MACHINE_RATES_YUAN_PER_SECOND = {
    "90T": 0.016,
    "120T": 0.022,
    "160T": 0.028,
}

SUPPLIER_MARGIN_RATE = 0.15


@dataclass(frozen=True)
class ProcessRule:
    material_loss_rate: float
    base_process_fee: float
    complexity_multiplier: dict[str, float]
    batch_discount: dict[str, float]
    notes: tuple[str, ...]


PROCESS_RULES: dict[str, ProcessRule] = {
    "CNC铝件": ProcessRule(
        material_loss_rate=0.45,
        base_process_fee=8.5,
        complexity_multiplier={"低": 0.8, "中": 1.0, "高": 1.45},
        batch_discount={"small": 1.25, "medium": 1.0, "large": 0.82},
        notes=(
            "CNC 成本受装夹次数、去料率、深腔、小刀具和表面要求影响明显。",
            "铝件材料费按较高去料损耗估算，STEP 体积接入后应优先用实际毛坯策略修正。",
        ),
    ),
    "钣金件": ProcessRule(
        material_loss_rate=0.18,
        base_process_fee=2.8,
        complexity_multiplier={"低": 0.85, "中": 1.0, "高": 1.35},
        batch_discount={"small": 1.2, "medium": 1.0, "large": 0.78},
        notes=(
            "钣金件加工费主要来自冲裁、折弯、压铆、焊接和表面处理。",
            "展开面积、折弯次数和压铆件数量会显著改变报价。",
        ),
    ),
    "铝合金冲压": ProcessRule(
        material_loss_rate=0.22,
        base_process_fee=3.2,
        complexity_multiplier={"低": 0.85, "中": 1.0, "高": 1.4},
        batch_discount={"small": 1.35, "medium": 0.95, "large": 0.68},
        notes=(
            "铝合金冲压适合中高批量薄板结构，模具费和排样利用率是核心成本项。",
            "折弯纹向、拉伸深度、回弹和平面度会影响良率和工站数量。",
        ),
    ),
    "锌合金压铸": ProcessRule(
        material_loss_rate=0.12,
        base_process_fee=3.6,
        complexity_multiplier={"低": 0.9, "中": 1.0, "高": 1.3},
        batch_discount={"small": 1.35, "medium": 1.0, "large": 0.72},
        notes=(
            "压铸适合中高批量，模具费、后加工和良率是关键成本项。",
            "薄壁、披锋、滑块结构和外观面要求会增加制造风险。",
        ),
    ),
    "3D打印": ProcessRule(
        material_loss_rate=0.08,
        base_process_fee=12.0,
        complexity_multiplier={"低": 0.85, "中": 1.0, "高": 1.25},
        batch_discount={"small": 1.0, "medium": 0.92, "large": 0.85},
        notes=(
            "3D 打印适合验证件和小批量，成本受打印时间、支撑、后处理和材料影响。",
            "若转量产，应重新评估注塑、压铸或 CNC 工艺路线。",
        ),
    ),
}

SURFACE_TREATMENT_RATES_YUAN_PER_CM2 = {
    "无": 0.0,
    "阳极氧化": 0.018,
    "喷涂": 0.022,
    "喷砂": 0.012,
    "电镀": 0.035,
    "拉丝": 0.02,
}


def estimate_injection_molding_cost(
    product_weight_g: float,
    material_price_per_kg: float,
    injection_cycle_s: float,
    machine_tonnage: str,
    cavities: int,
    defect_rate: float,
    mold_amortization_per_piece: float,
    supplier_margin_rate: float = SUPPLIER_MARGIN_RATE,
) -> dict[str, Any]:
    """Estimate unit price for an injection molded plastic part.

    Formula:
    - material fee = product weight / 1000 * material unit price
    - process fee = injection cycle * machine second rate / cavities
    - mold fee = amortization per piece
    - defect adjustment = base subtotal / yield - base subtotal
    - final unit price = yield-adjusted subtotal * (1 + supplier margin)
    """

    _validate_positive(product_weight_g, "product_weight_g")
    _validate_positive(material_price_per_kg, "material_price_per_kg")
    _validate_positive(injection_cycle_s, "injection_cycle_s")
    _validate_positive(cavities, "cavities")
    _validate_non_negative(mold_amortization_per_piece, "mold_amortization_per_piece")
    _validate_rate(defect_rate, "defect_rate")
    _validate_rate(supplier_margin_rate, "supplier_margin_rate")

    if machine_tonnage not in MACHINE_RATES_YUAN_PER_SECOND:
        supported = ", ".join(MACHINE_RATES_YUAN_PER_SECOND)
        raise ValueError(
            f"Unsupported machine tonnage: {machine_tonnage}. Supported: {supported}"
        )

    material_fee = product_weight_g / 1000 * material_price_per_kg
    process_fee = (
        injection_cycle_s * MACHINE_RATES_YUAN_PER_SECOND[machine_tonnage] / cavities
    )
    mold_fee = mold_amortization_per_piece
    raw_subtotal = material_fee + process_fee + mold_fee
    adjusted_subtotal = raw_subtotal / (1 - defect_rate)
    defect_adjustment = adjusted_subtotal - raw_subtotal
    unit_price = adjusted_subtotal * (1 + supplier_margin_rate)

    return _build_result(
        process="注塑件",
        items={
            "材料费": material_fee,
            "加工费": process_fee,
            "模具分摊费": mold_fee,
            "不良率调整": defect_adjustment,
        },
        supplier_margin_rate=supplier_margin_rate,
        unit_price=unit_price,
        notes=[
            f"{machine_tonnage} 机台费率为 {MACHINE_RATES_YUAN_PER_SECOND[machine_tonnage]} 元/秒。",
            "材料费按产品净重估算，浇口、流道和粉碎回用比例需由工艺确认。",
            "加工费按周期、机台吨位和一模出数估算；实际报价还会受换模、调机和自动化程度影响。",
        ],
    )


def estimate_process_cost(
    process: str,
    product_weight_g: float,
    material_price_per_kg: float,
    batch_qty: int,
    complexity: str,
    surface_treatment: str,
    surface_area_cm2: float,
    supplier_margin_rate: float = SUPPLIER_MARGIN_RATE,
    injection_cycle_s: float = 30,
    machine_tonnage: str = "120T",
    cavities: int = 1,
    defect_rate: float = 0.03,
    mold_amortization_per_piece: float = 0.0,
    process_fee_multiplier: float = 1.0,
    extra_process_fee: float = 0.0,
) -> dict[str, Any]:
    if process == "注塑件":
        result = estimate_injection_molding_cost(
            product_weight_g=product_weight_g,
            material_price_per_kg=material_price_per_kg,
            injection_cycle_s=injection_cycle_s,
            machine_tonnage=machine_tonnage,
            cavities=cavities,
            defect_rate=defect_rate,
            mold_amortization_per_piece=mold_amortization_per_piece,
            supplier_margin_rate=supplier_margin_rate,
        )
        surface_fee = _surface_fee(surface_treatment, surface_area_cm2)
        if surface_fee:
            return _append_item(
                result,
                "表面处理费",
                surface_fee,
                "塑胶件喷涂、镭雕、电镀等二次工艺需按外观面面积和遮蔽要求确认。",
            )
        return result

    if process not in PROCESS_RULES:
        supported = ", ".join(["注塑件", *PROCESS_RULES])
        raise ValueError(f"Unsupported process: {process}. Supported: {supported}")

    _validate_positive(product_weight_g, "product_weight_g")
    _validate_positive(material_price_per_kg, "material_price_per_kg")
    _validate_positive(batch_qty, "batch_qty")
    _validate_non_negative(surface_area_cm2, "surface_area_cm2")
    _validate_positive(process_fee_multiplier, "process_fee_multiplier")
    _validate_non_negative(extra_process_fee, "extra_process_fee")
    _validate_rate(supplier_margin_rate, "supplier_margin_rate")

    rule = PROCESS_RULES[process]
    if complexity not in rule.complexity_multiplier:
        supported = ", ".join(rule.complexity_multiplier)
        raise ValueError(f"Unsupported complexity: {complexity}. Supported: {supported}")

    material_fee = (
        product_weight_g / 1000
        * material_price_per_kg
        * (1 + rule.material_loss_rate)
    )
    process_fee = (
        rule.base_process_fee
        * rule.complexity_multiplier[complexity]
        * _batch_factor(batch_qty, rule)
        * process_fee_multiplier
        + extra_process_fee
    )
    surface_fee = _surface_fee(surface_treatment, surface_area_cm2)
    inspection_packaging_fee = max(0.25, process_fee * 0.06)
    raw_subtotal = material_fee + process_fee + surface_fee + inspection_packaging_fee
    adjusted_subtotal = raw_subtotal / (1 - 0.02)
    yield_adjustment = adjusted_subtotal - raw_subtotal
    unit_price = adjusted_subtotal * (1 + supplier_margin_rate)

    return _build_result(
        process=process,
        items={
            "材料费": material_fee,
            "加工费": process_fee,
            "表面处理费": surface_fee,
            "检验包装费": inspection_packaging_fee,
            "良率调整": yield_adjustment,
        },
        supplier_margin_rate=supplier_margin_rate,
        unit_price=unit_price,
        notes=list(rule.notes),
    )


def breakdown_rows(result: dict[str, Any]) -> list[dict[str, Any]]:
    rows = [
        {"成本项": name, "金额(元/件)": value}
        for name, value in result["items"].items()
    ]
    rows.append({"成本项": "供应商管理利润率", "金额(元/件)": result["margin_amount"]})
    rows.append({"成本项": "最终单件预估价", "金额(元/件)": result["unit_price"]})
    return rows


def _append_item(
    result: dict[str, Any], name: str, amount: float, note: str
) -> dict[str, Any]:
    items = dict(result["items"])
    items[name] = _money(amount)
    subtotal_before_margin = sum(items.values())
    unit_price = subtotal_before_margin * (1 + result["supplier_margin_rate"])

    return _build_result(
        process=result["process"],
        items=items,
        supplier_margin_rate=result["supplier_margin_rate"],
        unit_price=unit_price,
        notes=[*result["notes"], note],
    )


def _build_result(
    process: str,
    items: dict[str, float],
    supplier_margin_rate: float,
    unit_price: float,
    notes: list[str],
) -> dict[str, Any]:
    rounded_items = {name: _money(amount) for name, amount in items.items()}
    subtotal_before_margin = _money(sum(rounded_items.values()))
    rounded_unit_price = _money(unit_price)

    return {
        "process": process,
        "items": rounded_items,
        "subtotal_before_margin": subtotal_before_margin,
        "supplier_margin_rate": supplier_margin_rate,
        "margin_amount": _money(rounded_unit_price - subtotal_before_margin),
        "unit_price": rounded_unit_price,
        "notes": notes,
    }


def _surface_fee(surface_treatment: str, surface_area_cm2: float) -> float:
    _validate_non_negative(surface_area_cm2, "surface_area_cm2")
    if surface_treatment not in SURFACE_TREATMENT_RATES_YUAN_PER_CM2:
        supported = ", ".join(SURFACE_TREATMENT_RATES_YUAN_PER_CM2)
        raise ValueError(
            f"Unsupported surface treatment: {surface_treatment}. Supported: {supported}"
        )
    return surface_area_cm2 * SURFACE_TREATMENT_RATES_YUAN_PER_CM2[surface_treatment]


def _batch_factor(batch_qty: int, rule: ProcessRule) -> float:
    if batch_qty < 500:
        return rule.batch_discount["small"]
    if batch_qty <= 5000:
        return rule.batch_discount["medium"]
    return rule.batch_discount["large"]


def _validate_positive(value: float, name: str) -> None:
    if value <= 0:
        raise ValueError(f"{name} must be greater than 0")


def _validate_non_negative(value: float, name: str) -> None:
    if value < 0:
        raise ValueError(f"{name} must be greater than or equal to 0")


def _validate_rate(value: float, name: str) -> None:
    if value < 0 or value >= 1:
        raise ValueError(f"{name} must be between 0 and 1")


def _money(value: float) -> float:
    return round(value + 1e-9, 2)
