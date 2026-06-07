from cost_workbench.ui_helpers import metric_card_html


def test_metric_card_html_preserves_long_units_and_wraps_value():
    html = metric_card_html("材料密度", "1.05 g/cm³")

    assert "材料密度" in html
    assert "1.05 g/cm³" in html
    assert "word-break:break-word" in html
    assert "white-space:normal" in html
