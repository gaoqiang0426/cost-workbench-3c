from pathlib import Path

from cost_workbench.consultation import CONSULTATION_NOTE, qr_code_path


def test_consultation_qr_asset_and_note_are_available():
    assert CONSULTATION_NOTE == "咨询更详细准确报价及工艺信息，请扫码，备注微信号"
    assert qr_code_path() == Path(__file__).parents[1] / "docs" / "default.jpg"
    assert qr_code_path().exists()
