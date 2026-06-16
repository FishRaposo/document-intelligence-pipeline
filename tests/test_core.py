"""Smoke test that the end-to-end demo runs and exits 0."""

import os
import runpy
import sys


def test_demo_runs(capsys):
    demo_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../examples/run_demo.py")
    )
    sys.argv = [demo_path]
    try:
        runpy.run_path(demo_path, run_name="__main__")
    except SystemExit as exc:
        assert exc.code in (0, None)
    out = capsys.readouterr().out
    assert "Demo complete." in out
    assert "[OK]" in out
    assert "[DUP]" in out
    assert "[QUAR]" in out
