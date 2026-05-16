"""Subprocess wrapper around @tscg/core via a Node bridge script."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

Profile = Literal["balanced", "aggressive", "conservative"]
Model = Literal[
    "claude-sonnet", "claude-opus", "claude-haiku",
    "gpt-4", "gpt-5", "gpt-4o-mini",
    "llama-3.1", "llama-3.2",
    "mistral-7b", "mistral-large",
    "gemma-3", "phi-4", "qwen-3", "deepseek-v3",
    "auto",
]

BRIDGE_PATH = Path(__file__).resolve().parent / "bridge.mjs"
DEFAULT_NODE = os.environ.get("TSCG_NODE_BIN", "node")
DEFAULT_TIMEOUT_SEC = int(os.environ.get("TSCG_TIMEOUT_SEC", "30"))


@dataclass(frozen=True)
class CompressionResult:
    compressed: str
    original_chars: int
    compressed_chars: int
    original_tokens: int
    compressed_tokens: int
    savings_pct: float
    elapsed_ms: float
    profile: str
    model: str
    applied_principles: tuple[str, ...]

    @property
    def char_savings_pct(self) -> float:
        if self.original_chars == 0:
            return 0.0
        return 100.0 * (self.original_chars - self.compressed_chars) / self.original_chars

    @property
    def meets_theorem_3_1(self) -> bool:
        """Paper's Theorem 3.1: >=51% token savings on well-formed tool schemas."""
        return self.savings_pct >= 51.0


class TSCGCompiler:
    """Python adapter for @tscg/core via subprocess.

    Spawns a Node bridge per call. Optimised for small catalogs (<100 tools);
    use compress_batch for higher throughput.
    """

    def __init__(
        self,
        node_bin: str = DEFAULT_NODE,
        bridge_path: Path = BRIDGE_PATH,
        package_dir: Path | None = None,
        timeout_sec: int = DEFAULT_TIMEOUT_SEC,
    ) -> None:
        if shutil.which(node_bin) is None:
            raise RuntimeError(
                f"Node binary {node_bin!r} not found on PATH. "
                "Install Node.js 18+ or set TSCG_NODE_BIN."
            )
        if not bridge_path.exists():
            raise FileNotFoundError(f"bridge.mjs not found at {bridge_path}")
        self.node_bin = node_bin
        self.bridge_path = bridge_path
        self.timeout_sec = timeout_sec
        self.package_dir = package_dir or self._discover_package_dir(bridge_path)

    @staticmethod
    def _discover_package_dir(bridge_path: Path) -> Path:
        for parent in [bridge_path.parent, *bridge_path.parents]:
            if (parent / "node_modules" / "@tscg" / "core").exists():
                return parent
        raise RuntimeError(
            "Could not locate node_modules/@tscg/core. "
            "Run `npm install @tscg/core` in the repo root."
        )

    def compress(
        self,
        schema: list[dict[str, Any]],
        profile: Profile = "balanced",
        model: Model = "gpt-4",
    ) -> CompressionResult:
        payload = json.dumps({"schema": schema, "profile": profile, "model": model})
        proc = subprocess.run(
            [self.node_bin, str(self.bridge_path)],
            input=payload,
            capture_output=True,
            text=True,
            cwd=self.package_dir,
            timeout=self.timeout_sec,
            check=False,
        )
        if proc.returncode != 0:
            raise RuntimeError(
                f"TSCG bridge failed (exit {proc.returncode}): {proc.stderr.strip()}"
            )
        data = json.loads(proc.stdout)
        s = data["stats"]
        return CompressionResult(
            compressed=data["compressed"],
            original_chars=s["original_chars"],
            compressed_chars=s["compressed_chars"],
            original_tokens=s["original_tokens"],
            compressed_tokens=s["compressed_tokens"],
            savings_pct=s["savings_pct"],
            elapsed_ms=s["ms"],
            profile=s["profile"],
            model=s["model"],
            applied_principles=tuple(s.get("applied_principles", ())),
        )

    def compress_batch(
        self,
        schemas: list[list[dict[str, Any]]],
        profile: Profile = "balanced",
        model: Model = "gpt-4",
    ) -> list[CompressionResult]:
        return [self.compress(s, profile=profile, model=model) for s in schemas]
