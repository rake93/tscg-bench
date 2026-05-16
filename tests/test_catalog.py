"""Tests for tscg_bench.catalog."""

from __future__ import annotations

import pytest

from tscg_bench.catalog import fixture_dir, list_catalogs, load_catalog


def test_fixture_dir_exists() -> None:
    d = fixture_dir()
    assert d.exists(), f"fixture dir {d} not found"
    assert d.is_dir()


def test_list_catalogs_returns_known_fixtures() -> None:
    names = {p.name for p in list_catalogs()}
    assert "small_5tools.json" in names
    assert "mid_20tools.json" in names
    assert "mcp_filesystem.json" in names


@pytest.mark.parametrize(
    "name,expected_min",
    [("small_5tools", 5), ("mid_20tools", 20), ("mcp_filesystem", 10)],
)
def test_load_catalog_sizes(name: str, expected_min: int) -> None:
    catalog = load_catalog(name)
    assert len(catalog) >= expected_min, (
        f"catalog {name} has only {len(catalog)} tools, expected >= {expected_min}"
    )


def test_load_catalog_shape() -> None:
    catalog = load_catalog("small_5tools")
    for entry in catalog:
        assert entry["type"] == "function"
        fn = entry["function"]
        assert "name" in fn
        assert "description" in fn
        assert "parameters" in fn
        assert fn["parameters"]["type"] == "object"


def test_load_catalog_missing_raises() -> None:
    with pytest.raises(FileNotFoundError):
        load_catalog("does_not_exist")
