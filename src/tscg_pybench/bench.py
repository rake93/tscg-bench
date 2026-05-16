"""End-to-end benchmark runner. Sweeps catalogs x profiles x models.

Outputs a list of BenchmarkRow records, one per (catalog, profile, model) cell.
Designed to be loaded into a pandas DataFrame for plotting.
"""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from tscg_pybench.catalog import load_catalog
from tscg_pybench.compiler import CompressionResult, Model, Profile, TSCGCompiler
from tscg_pybench.tokens import count_schema_tokens, count_tokens, tiktoken_available


@dataclass(frozen=True)
class BenchmarkRow:
    catalog_name: str
    n_tools: int
    profile: str
    model: str
    original_tokens_tscg: int
    compressed_tokens_tscg: int
    savings_pct_tscg: float
    elapsed_ms: float
    char_savings_pct: float
    meets_theorem_3_1: bool
    applied_principles: tuple[str, ...]
    original_tokens_tiktoken: int | None = None
    compressed_tokens_tiktoken: int | None = None
    savings_pct_tiktoken: float | None = None


def _row(
    catalog_name: str,
    catalog: list[dict],
    result: CompressionResult,
    independent_check: bool,
) -> BenchmarkRow:
    orig_tt: int | None = None
    comp_tt: int | None = None
    sav_tt: float | None = None
    if independent_check and tiktoken_available():
        orig_tt = count_schema_tokens(catalog)
        comp_tt = count_tokens(result.compressed)
        sav_tt = 100.0 * (orig_tt - comp_tt) / orig_tt if orig_tt > 0 else 0.0
    return BenchmarkRow(
        catalog_name=catalog_name,
        n_tools=len(catalog),
        profile=result.profile,
        model=result.model,
        original_tokens_tscg=result.original_tokens,
        compressed_tokens_tscg=result.compressed_tokens,
        savings_pct_tscg=result.savings_pct,
        elapsed_ms=result.elapsed_ms,
        char_savings_pct=result.char_savings_pct,
        meets_theorem_3_1=result.meets_theorem_3_1,
        applied_principles=result.applied_principles,
        original_tokens_tiktoken=orig_tt,
        compressed_tokens_tiktoken=comp_tt,
        savings_pct_tiktoken=None if sav_tt is None else round(sav_tt, 2),
    )


def run_benchmark(
    catalogs: Iterable[str | Path],
    profiles: Iterable[Profile] = ("balanced",),
    models: Iterable[Model] = ("gpt-4",),
    compiler: TSCGCompiler | None = None,
    independent_check: bool = True,
) -> list[BenchmarkRow]:
    """Run TSCG compression over every (catalog, profile, model) cell.

    If ``independent_check`` is True and tiktoken is installed, also recompute
    token counts independently to detect any inflated savings claims.
    """
    compiler = compiler or TSCGCompiler()
    rows: list[BenchmarkRow] = []
    for catalog_ref in catalogs:
        catalog = load_catalog(catalog_ref)
        name = Path(catalog_ref).stem if isinstance(catalog_ref, (str, Path)) else "unknown"
        for profile in profiles:
            for model in models:
                result = compiler.compress(catalog, profile=profile, model=model)
                rows.append(_row(name, catalog, result, independent_check))
    return rows


def write_csv(rows: list[BenchmarkRow], path: Path | str) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return path
    fieldnames = list(asdict(rows[0]).keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            d = asdict(r)
            d["applied_principles"] = ",".join(d["applied_principles"])
            writer.writerow(d)
    return path
