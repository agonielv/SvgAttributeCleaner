from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path


def parse_attributes(text: str | list[str]) -> list[str]:
    """Parse attribute names from lines, commas, or whitespace."""
    if isinstance(text, list):
        raw = "\n".join(text)
    else:
        raw = text or ""
    attrs: list[str] = []
    seen: set[str] = set()
    for item in re.split(r"[\s,]+", raw.strip()):
        item = item.strip()
        if item and item not in seen:
            attrs.append(item)
            seen.add(item)
    return attrs


def default_output_path(input_path: str | Path, suffix: str = "_cleaned") -> Path:
    path = Path(input_path)
    return path.with_name(f"{path.stem}{suffix}{path.suffix or '.svg'}")


def iter_svg_files(directory: str | Path, recursive: bool = False) -> list[Path]:
    root = Path(directory)
    pattern = "**/*.svg" if recursive else "*.svg"
    return sorted(p for p in root.glob(pattern) if p.is_file())


def open_path(path: str | Path) -> None:
    target = str(path)
    if sys.platform.startswith("win"):
        os.startfile(target)  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.Popen(["open", target])
    else:
        subprocess.Popen(["xdg-open", target])
