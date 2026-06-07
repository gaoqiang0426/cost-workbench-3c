from __future__ import annotations

from pathlib import Path


CONSULTATION_NOTE = "咨询更详细准确报价及工艺信息，请扫码，备注微信号"


def qr_code_path() -> Path:
    return Path(__file__).parents[1] / "docs" / "default.jpg"
