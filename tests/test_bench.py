"""Tests for tscg_pybench.bench end-to-end runner."""

from __future__ import annotations

from pathlib import Path

from tscg_pybench.bench import BenchmarkRow, run_benchmark, write_csv


def test_run_benchmark_smoke() -> None:
    rows = run_benchmark(
        catalogs=["small_5tools"],
        profiles=("balanced",),
        models=("gpt-4",),
        independent_check=False,
    )
    assert len(rows) == 1
    r = rows[0]
    assert isinstance(r, BenchmarkRow)
    assert r.catalog_name == "small_5tools"
    assert r.n_tools >= 5
    assert r.savings_pct_tscg > 0
    assert r.compressed_tokens_tscg < r.original_tokens_tscg


def test_run_benchmark_multi_profile() -> None:
    rows = run_benchmark(
        catalogs=["small_5tools"],
        profiles=("balanced", "aggressive"),
        models=("gpt-4",),
        independent_check=False,
    )
    assert len(rows) == 2
    profiles = {r.profile for r in rows}
    assert profiles == {"balanced", "aggressive"}


def test_write_csv_roundtrip(tmp_path: Path) -> None:
    rows = run_benchmark(
        catalogs=["small_5tools"],
        profiles=("balanced",),
        models=("gpt-4",),
        independent_check=False,
    )
    out = write_csv(rows, tmp_path / "out.csv")
    assert out.exists()
    text = out.read_text(encoding="utf-8")
    assert "catalog_name" in text
    assert "small_5tools" in text
    assert text.count("\n") >= 2
