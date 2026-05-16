"""Tests for tscg_bench.compiler."""

from __future__ import annotations

import pytest

from tscg_bench.compiler import CompressionResult, TSCGCompiler

CALC_TOOL: dict = {
    "type": "function",
    "function": {
        "name": "calculator",
        "description": "Performs basic arithmetic operations on numbers and expressions.",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "Math expression to evaluate."},
            },
            "required": ["expression"],
        },
    },
}

SEARCH_TOOL: dict = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "Search the web and return ranked results from major providers.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query."},
                "limit": {"type": "integer", "default": 10},
            },
            "required": ["query"],
        },
    },
}


@pytest.fixture(scope="module")
def compiler() -> TSCGCompiler:
    return TSCGCompiler()


def test_compress_returns_compression_result(compiler: TSCGCompiler) -> None:
    result = compiler.compress([CALC_TOOL, SEARCH_TOOL])
    assert isinstance(result, CompressionResult)
    assert result.compressed
    assert result.original_tokens > 0
    assert result.compressed_tokens > 0
    assert result.compressed_tokens < result.original_tokens
    assert 0 < result.savings_pct < 100


def test_savings_pct_matches_token_arithmetic(compiler: TSCGCompiler) -> None:
    r = compiler.compress([CALC_TOOL, SEARCH_TOOL])
    expected = 100.0 * (r.original_tokens - r.compressed_tokens) / r.original_tokens
    assert abs(r.savings_pct - expected) < 0.05


def test_char_savings_pct_computed(compiler: TSCGCompiler) -> None:
    r = compiler.compress([CALC_TOOL, SEARCH_TOOL])
    expected = 100.0 * (r.original_chars - r.compressed_chars) / r.original_chars
    assert abs(r.char_savings_pct - expected) < 0.05


def test_applied_principles_subset_of_eight(compiler: TSCGCompiler) -> None:
    r = compiler.compress([CALC_TOOL, SEARCH_TOOL])
    eight = {"SDM", "CAS", "CFO", "DRO", "TAS", "CFL", "SAD", "CCP"}
    assert set(r.applied_principles).issubset(eight)
    assert len(r.applied_principles) >= 3


def test_theorem_3_1_holds_on_realistic_catalog(compiler: TSCGCompiler) -> None:
    """Paper's Theorem 3.1: >=51% token savings on well-formed schemas."""
    catalog = [CALC_TOOL, SEARCH_TOOL] * 5
    r = compiler.compress(catalog)
    assert r.meets_theorem_3_1, (
        f"Theorem 3.1 violated: got {r.savings_pct}% savings on a 10-tool catalog"
    )


def test_batch_compress(compiler: TSCGCompiler) -> None:
    results = compiler.compress_batch([[CALC_TOOL], [SEARCH_TOOL], [CALC_TOOL, SEARCH_TOOL]])
    assert len(results) == 3
    assert all(r.savings_pct >= 0 for r in results)
