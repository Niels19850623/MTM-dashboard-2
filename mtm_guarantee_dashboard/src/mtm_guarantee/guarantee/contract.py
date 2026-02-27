from __future__ import annotations

from dataclasses import dataclass


@dataclass
class GuaranteeContract:
    coverage_pct: float = 1.0
    attachment: float = 0.0
    detachment: float = 1.0
    limit_pct: float = 1.0
    mode: str = "default_triggered"
