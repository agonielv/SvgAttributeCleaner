from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def write_report(results: list[dict[str, Any]] | dict[str, Any], report_path: str | Path) -> Path:
    path = Path(report_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    items = results if isinstance(results, list) else [results]
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_files": len(items),
        "successful_files": sum(1 for item in items if item.get("success")),
        "failed_files": sum(1 for item in items if not item.get("success")),
        "total_removed": sum(int(item.get("total_removed", 0)) for item in items),
        "results": items,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
