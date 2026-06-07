from cost_workbench.cost_engine import estimate_process_cost
from cost_workbench.material_library import get_material
from cost_workbench.optimization import generate_optimization_suggestions


def test_injection_optimization_uses_actual_weight_and_surface_treatment():
    analysis = {
        "material_name": "PC+ABS",
        "weight_g": 95,
        "surface_area_cm2": 180,
        "surface_treatment": "喷涂",
        "complexity": "高",
    }
    cost_result = estimate_process_cost(
        process="注塑件",
        product_weight_g=95,
        material_price_per_kg=24,
        batch_qty=1000,
        complexity="高",
        surface_treatment="喷涂",
        surface_area_cm2=180,
        injection_cycle_s=35,
        machine_tonnage="120T",
        cavities=2,
        defect_rate=0.05,
        mold_amortization_per_piece=0.8,
    )

    suggestions = generate_optimization_suggestions(
        "注塑件", get_material("PC+ABS"), analysis, cost_result
    )

    assert any("厚胶位" in item["建议动作"] for item in suggestions["降低成本"])
    assert any("95.0 g" in item["工程原因"] for item in suggestions["减少重量"])

