from cost_workbench.cost_engine import estimate_injection_molding_cost
from cost_workbench.report_generator import build_report, generate_pdf_report


def _sample_cost_result():
    return estimate_injection_molding_cost(
        product_weight_g=50,
        material_price_per_kg=20,
        injection_cycle_s=30,
        machine_tonnage="120T",
        cavities=2,
        defect_rate=0.05,
        mold_amortization_per_piece=0.8,
    )


def test_build_report_contains_two_pages_and_cost_items():
    report = build_report(
        part_name="遥控器上盖",
        process="注塑件",
        cost_result=_sample_cost_result(),
        inputs={
            "产品克重(g)": 50,
            "材料单价(元/kg)": 20,
            "注塑周期(s)": 30,
            "机台吨位": "120T",
            "一模出数": 2,
            "不良率": "5%",
            "模具费摊销": 0.8,
        },
    )

    assert report["title"] == "3C 结构件成本预估报告"
    assert report["part_name"] == "遥控器上盖"
    assert len(report["pages"]) == 2
    assert report["pages"][0]["name"] == "分析与成本"
    assert report["pages"][1]["name"] == "局部优化建议"
    assert report["cost_breakdown"][0]["成本项"] == "材料费"
    assert report["total_price"] == 2.58


def test_generate_pdf_report_returns_pdf_bytes():
    report = build_report(
        part_name="注塑验证件",
        process="注塑件",
        cost_result=_sample_cost_result(),
        inputs={"产品克重(g)": 50},
    )

    pdf_bytes = generate_pdf_report(report)

    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 1000
