"""Sanity checks against kospel-cmi-lib (no Home Assistant import)."""

import math
from datetime import timedelta

from kospel_cmi.controller.device import EkcoM3


def test_ekco_m3_required_registers_nonempty() -> None:
    """Library owns the register set for strict refresh."""
    assert len(EkcoM3.REQUIRED_REGISTERS) > 0


def test_communication_threshold_math_matches_plan() -> None:
    """~90s debounce at 15s scan ≈ 6 failures (matches const.COMMUNICATION_FAILURE_THRESHOLD)."""
    scan = timedelta(seconds=15)
    assert max(1, int(math.ceil(90.0 / scan.total_seconds()))) == 6
