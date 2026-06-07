from cost_workbench.process_parameters import summarize_process_parameters


def test_cnc_parameters_increase_process_multiplier_for_5_axis_and_setups():
    result = summarize_process_parameters(
        "CNC铝件",
        {"cnc_machine": "5轴CNC", "setup_count": 3, "machining_time_min": 50},
    )

    assert result["process_fee_multiplier"] > 1.7
    assert "5轴CNC" in result["summary"][0]


def test_sheet_metal_parameters_add_rivet_extra_fee():
    result = summarize_process_parameters(
        "钣金件",
        {"cutting_method": "激光切割", "bend_count": 6, "rivet_count": 8},
    )

    assert result["process_fee_multiplier"] > 1.3
    assert result["extra_process_fee"] == 0.64


def test_only_injection_parameters_use_injection_specific_summary():
    result = summarize_process_parameters(
        "注塑件",
        {
            "machine_tonnage": "120T",
            "injection_cycle_s": 30,
            "cavities": 2,
            "mold_amortization_per_piece": 0.8,
        },
    )

    assert result["process_fee_multiplier"] == 1.0
    assert result["extra_process_fee"] == 0.0
    assert "注塑机台" in result["summary"][0]

