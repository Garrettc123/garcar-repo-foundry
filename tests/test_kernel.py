import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_kernel_parses():
    ast.parse((ROOT / "kernel" / "app.py").read_text())
