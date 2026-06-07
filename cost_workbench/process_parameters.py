from __future__ import annotations

from typing import Any


def summarize_process_parameters(process: str, values: dict[str, Any]) -> dict[str, Any]:
    if process == "注塑件":
        return {
            "process_fee_multiplier": 1.0,
            "extra_process_fee": 0.0,
            "summary": [
                f"注塑机台：{values.get('machine_tonnage', '120T')}",
                f"注塑周期：{values.get('injection_cycle_s', 30)} s",
                f"一模出数：{values.get('cavities', 1)}",
                f"模具摊销：{values.get('mold_amortization_per_piece', 0)} 元/件",
            ],
        }

    if process == "CNC铝件":
        machine_factor = {"3轴CNC": 1.0, "4轴CNC": 1.2, "5轴CNC": 1.55}[values["cnc_machine"]]
        setup_factor = 1 + max(values["setup_count"] - 1, 0) * 0.08
        time_factor = 1 + max(values["machining_time_min"] - 20, 0) / 120
        return {
            "process_fee_multiplier": round(machine_factor * setup_factor * time_factor, 3),
            "extra_process_fee": 0.0,
            "summary": [
                f"机台：{values['cnc_machine']}",
                f"装夹次数：{values['setup_count']} 次",
                f"单件机加工时间：{values['machining_time_min']} min",
            ],
        }

    if process == "铝合金冲压":
        press_factor = {"45T": 0.9, "80T": 1.0, "110T": 1.18, "160T": 1.35}[values["press_tonnage"]]
        station_factor = 1 + max(values["station_count"] - 3, 0) * 0.06
        return {
            "process_fee_multiplier": round(press_factor * station_factor, 3),
            "extra_process_fee": values["die_amortization_per_piece"],
            "summary": [
                f"冲床吨位：{values['press_tonnage']}",
                f"工站数：{values['station_count']}",
                f"冲压模具摊销：{values['die_amortization_per_piece']} 元/件",
            ],
        }

    if process == "钣金件":
        cut_factor = {"激光切割": 1.22, "数冲": 1.0, "模具冲裁": 0.82}[values["cutting_method"]]
        bend_factor = 1 + values["bend_count"] * 0.035
        return {
            "process_fee_multiplier": round(cut_factor * bend_factor, 3),
            "extra_process_fee": values["rivet_count"] * 0.08,
            "summary": [
                f"开料方式：{values['cutting_method']}",
                f"折弯次数：{values['bend_count']}",
                f"压铆数量：{values['rivet_count']}",
            ],
        }

    if process == "锌合金压铸":
        machine_factor = {"88T": 0.92, "160T": 1.0, "280T": 1.32}[values["die_cast_machine"]]
        cycle_factor = 1 + max(values["die_cast_cycle_s"] - 35, 0) / 180
        cavity_factor = max(0.65, 1 / max(values["die_cast_cavities"], 1))
        return {
            "process_fee_multiplier": round(machine_factor * cycle_factor * cavity_factor, 3),
            "extra_process_fee": values["die_cast_mold_amortization"],
            "summary": [
                f"压铸机：{values['die_cast_machine']}",
                f"压铸周期：{values['die_cast_cycle_s']} s",
                f"一模出数：{values['die_cast_cavities']}",
                f"模具摊销：{values['die_cast_mold_amortization']} 元/件",
            ],
        }

    if process == "3D打印":
        tech_factor = {"SLA": 1.0, "SLS": 1.35, "FDM": 0.75, "MJF": 1.45}[values["print_technology"]]
        time_factor = 1 + values["print_time_h"] / 20
        post_factor = {"基础去支撑": 1.0, "打磨喷漆": 1.35, "精修外观": 1.65}[values["post_process"]]
        return {
            "process_fee_multiplier": round(tech_factor * time_factor * post_factor, 3),
            "extra_process_fee": 0.0,
            "summary": [
                f"打印工艺：{values['print_technology']}",
                f"打印时间：{values['print_time_h']} h",
                f"后处理：{values['post_process']}",
            ],
        }

    raise ValueError(f"Unsupported process parameters: {process}")

