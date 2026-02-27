from __future__ import annotations

from pathlib import Path


def save_tearsheet(path: str, summary_md: str) -> str:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(summary_md)
    return str(p)
