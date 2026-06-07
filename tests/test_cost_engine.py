from cost_workbench.cost_engine import (
    MACHINE_RATES_YUAN_PER_SECOND,
    estimate_injection_molding_cost,
    estimate_process_cost,
)


def test_injection_molding_cost_breakdown_uses_requested_formula():
    result = estimate_injection_molding_cost(
        product_weight_g=50,
        material_price_per_kg=20,
        injection_cycle_s=30,
        machine_tonnage="120T",
        cavities=2,
        defect_rate=0.05,
        mold_amortization_per_piece=0.8,
    )

    assert MACHINE_RATES_YUAN_PER_SECOND == {
        "90T": 0.016,
        "120T": 0.022,
        "160T": 0.028,
    }
    assert result["items"]["材料费"] == 1.0
    assert result["items"]["加工费"] == 0.33
    assert result["items"]["模具分摊费"] == 0.8
    assert result["items"]["不良率调整"] == 0.11
    assert result["subtotal_before_margin"] == 2.24
    assert result["supplier_margin_rate"] == 0.15
    assert result["unit_price"] == 2.58


def test_injection_molding_rejects_unknown_machine_tonnage():
    try:
        estimate_injection_molding_cost(
            product_weight_g=10,
            material_price_per_kg=18,
            injection_cycle_s=25,
            machine_tonnage="200T",
            cavities=1,
            defect_rate=0.02,
            mold_amortization_per_piece=0.1,
        )
    except ValueError as exc:
        assert "Unsupported machine tonnage" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_process_cost_supports_cnc_and_surface_treatment():
    result = estimate_process_cost(
        process="CNC铝件",
        product_weight_g=80,
        material_price_per_kg=32,
        batch_qty=500,
        complexity="中",
        surface_treatment="阳极氧化",
        surface_area_cm2=120,
        supplier_margin_rate=0.15,
    )

    assert result["process"] == "CNC铝件"
    assert result["items"]["材料费"] > 0
    assert result["items"]["加工费"] > 0
    assert result["items"]["表面处理费"] > 0
    assert result["unit_price"] > result["subtotal_before_margin"]


def test_process_cost_supports_multiple_3c_routes():
    processes = ["注塑件", "CNC铝件", "铝合金冲压", "钣金件", "锌合金压铸", "3D打印"]

    for process in processes:
        result = estimate_process_cost(
            process=process,
            product_weight_g=45,
            material_price_per_kg=28,
            batch_qty=1000,
            complexity="高",
            surface_treatment="喷涂",
            surface_area_cm2=85,
            supplier_margin_rate=0.15,
            injection_cycle_s=28,
            machine_tonnage="90T",
            cavities=2,
            defect_rate=0.03,
            mold_amortization_per_piece=0.2,
        )

        assert result["process"] == process
        assert result["unit_price"] > 0
        assert result["items"]["材料费"] >= 0
        assert result["notes"]
