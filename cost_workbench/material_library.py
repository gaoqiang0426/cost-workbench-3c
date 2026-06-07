from __future__ import annotations

from typing import Any


MATERIALS: dict[str, dict[str, Any]] = {
    "ABS": {
        "category": "塑料",
        "density_g_cm3": 1.05,
        "price_yuan_kg": 18.0,
        "compatible_processes": ["注塑件", "3D打印"],
        "strength": "中等强度，尺寸稳定性好，适合普通外壳和内部支架。",
        "weight": "密度低，适合轻量化消费电子结构。",
        "cost": "成本较低，量产友好。",
        "surface": "适合喷涂、丝印、镭雕。",
        "risk": "耐热和耐候性一般，卡扣根部需控制应力集中。",
    },
    "PC": {
        "category": "塑料",
        "density_g_cm3": 1.20,
        "price_yuan_kg": 28.0,
        "compatible_processes": ["注塑件"],
        "strength": "韧性和抗冲击性能好。",
        "weight": "比 ABS 稍重。",
        "cost": "材料成本中高。",
        "surface": "可喷涂、硬化、镭雕。",
        "risk": "流动性和内应力需控制，透明件需关注缩水和气纹。",
    },
    "PC+ABS": {
        "category": "塑料",
        "density_g_cm3": 1.14,
        "price_yuan_kg": 24.0,
        "compatible_processes": ["注塑件"],
        "strength": "兼顾 PC 韧性和 ABS 加工性，是 3C 外壳常用材料。",
        "weight": "重量适中。",
        "cost": "成本中等，适合外观件和结构件。",
        "surface": "适合喷涂、丝印、镭雕、电镀级需指定牌号。",
        "risk": "需关注熔接线、缩水和喷涂附着力。",
    },
    "PA66+GF": {
        "category": "塑料",
        "density_g_cm3": 1.35,
        "price_yuan_kg": 36.0,
        "compatible_processes": ["注塑件"],
        "strength": "玻纤增强，刚性和耐疲劳性好。",
        "weight": "比普通塑料重。",
        "cost": "成本偏高。",
        "surface": "通常用于内部结构，外观喷涂需谨慎。",
        "risk": "各向异性明显，易翘曲，模流和浇口位置很关键。",
    },
    "POM": {
        "category": "塑料",
        "density_g_cm3": 1.41,
        "price_yuan_kg": 25.0,
        "compatible_processes": ["注塑件"],
        "strength": "耐磨、自润滑，适合滑块和传动小件。",
        "weight": "密度较高。",
        "cost": "成本中等。",
        "surface": "通常不做喷涂。",
        "risk": "收缩率较大，尺寸精度需重点确认。",
    },
    "AL6061": {
        "category": "铝合金",
        "density_g_cm3": 2.70,
        "price_yuan_kg": 32.0,
        "compatible_processes": ["CNC铝件", "铝合金冲压"],
        "strength": "综合强度和加工性好。",
        "weight": "轻量，适合支架和散热结构。",
        "cost": "材料中等，加工费受去料率影响大。",
        "surface": "适合阳极氧化、喷砂、拉丝。",
        "risk": "小 R、深腔和高外观等级会推高 CNC 成本。",
    },
    "AL5052": {
        "category": "铝合金",
        "density_g_cm3": 2.68,
        "price_yuan_kg": 30.0,
        "compatible_processes": ["钣金件", "铝合金冲压"],
        "strength": "成形性和耐蚀性好，适合冲压/折弯铝件。",
        "weight": "轻量。",
        "cost": "材料中等，冲压批量越大越有优势。",
        "surface": "适合阳极、喷涂、拉丝。",
        "risk": "折弯半径和纹向需确认，避免开裂。",
    },
    "SUS304": {
        "category": "不锈钢",
        "density_g_cm3": 7.93,
        "price_yuan_kg": 38.0,
        "compatible_processes": ["钣金件", "CNC铝件"],
        "strength": "强度和耐腐蚀性好。",
        "weight": "密度高，重量敏感件需谨慎。",
        "cost": "材料成本较高，加工硬化明显。",
        "surface": "适合拉丝、抛光、电解、喷砂。",
        "risk": "加工硬化和回弹明显，折弯补偿需确认。",
    },
    "SPCC": {
        "category": "钢/五金",
        "density_g_cm3": 7.85,
        "price_yuan_kg": 8.0,
        "compatible_processes": ["钣金件"],
        "strength": "普通冷轧钢板，强度和成形性均衡。",
        "weight": "偏重。",
        "cost": "材料便宜，适合内部支架。",
        "surface": "常见电镀、喷粉、喷涂。",
        "risk": "需防锈处理，外观件需控制表面瑕疵。",
    },
    "Zamak 3": {
        "category": "锌合金",
        "density_g_cm3": 6.60,
        "price_yuan_kg": 24.0,
        "compatible_processes": ["锌合金压铸"],
        "strength": "流动性好，适合复杂小型装饰和结构件。",
        "weight": "密度高，手感重。",
        "cost": "中高批量有优势。",
        "surface": "适合电镀、喷涂、烤漆。",
        "risk": "披锋、气孔、缩水和电镀不良需重点控制。",
    },
    "SLA树脂": {
        "category": "原型材料",
        "density_g_cm3": 1.15,
        "price_yuan_kg": 120.0,
        "compatible_processes": ["3D打印"],
        "strength": "适合外观验证，强度有限。",
        "weight": "轻量。",
        "cost": "单件成本偏高，不适合量产。",
        "surface": "可打磨、喷涂。",
        "risk": "耐热、耐冲击和长期可靠性不足。",
    },
}


def material_names_for_process(process: str) -> list[str]:
    return [
        name
        for name, data in MATERIALS.items()
        if process in data["compatible_processes"]
    ]


def get_material(name: str) -> dict[str, Any]:
    if name not in MATERIALS:
        supported = ", ".join(MATERIALS)
        raise ValueError(f"Unsupported material: {name}. Supported: {supported}")
    return MATERIALS[name]


def all_material_names() -> list[str]:
    return list(MATERIALS)

