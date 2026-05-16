"""Tool-schema catalog loader. Reads OpenAI-style tool arrays from fixtures/."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

FIXTURE_DIR = Path(__file__).resolve().parents[2] / "fixtures" / "tools"


def fixture_dir() -> Path:
    return FIXTURE_DIR


def list_catalogs(directory: Path | None = None) -> list[Path]:
    d = directory or FIXTURE_DIR
    if not d.exists():
        raise FileNotFoundError(f"Catalog directory not found: {d}")
    return sorted(p for p in d.glob("*.json") if p.is_file())


def load_catalog(name_or_path: str | Path, directory: Path | None = None) -> list[dict[str, Any]]:
    path = Path(name_or_path)
    if not path.is_absolute() and not path.exists():
        d = directory or FIXTURE_DIR
        candidate = d / path
        if candidate.exists():
            path = candidate
        else:
            candidate_json = d / f"{path.stem}.json"
            if candidate_json.exists():
                path = candidate_json
    if not path.exists():
        raise FileNotFoundError(f"Catalog not found: {name_or_path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"Catalog {path} must be a JSON array of tool definitions")
    return data
