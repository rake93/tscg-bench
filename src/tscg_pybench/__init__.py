"""tscg-pybench — independent Python reproduction of the TSCG paper's compression claims.

Paper:  Sakizli, F. "TSCG: Deterministic Tool-Schema Compilation for Agentic LLM Deployments"
        (arXiv:2605.04107, 2026).
Ref:    https://github.com/SKZL-AI/tscg  (TypeScript reference implementation, MIT)
"""

from tscg_pybench.bench import BenchmarkRow, run_benchmark
from tscg_pybench.catalog import list_catalogs, load_catalog
from tscg_pybench.compiler import CompressionResult, TSCGCompiler

__version__ = "0.1.0"
__all__ = [
    "TSCGCompiler",
    "CompressionResult",
    "load_catalog",
    "list_catalogs",
    "run_benchmark",
    "BenchmarkRow",
]
