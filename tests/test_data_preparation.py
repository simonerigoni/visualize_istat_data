"""Tests for the location-name rewrite steps in data_preparation.ipynb.

The notebook is script-only (no importable functions), so the code cells are
executed against a tiny fixture in a temporary directory.
"""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = REPO_ROOT / "data_preparation.ipynb"


def _code_cells() -> list[str]:
    notebook = json.loads(NOTEBOOK.read_text())
    return [
        "".join(cell.get("source") or [])
        for cell in notebook.get("cells", [])
        if cell.get("cell_type") == "code"
    ]


def test_data_preparation_rebuilds_location_hierarchy(tmp_path, monkeypatch):
    # Indentation encodes the hierarchy used by the notebook:
    # 0 spaces = State, 2 = Geographic Area / Macro Region, 4 = Region,
    # 6 = Province, 8 = Comune.
    (tmp_path / "location_step_0.txt").write_text(
        "\n".join(
            [
                "Italia",
                "  Nord-ovest",
                "  Nord-ovest",
                "    Piemonte",
                "      Torino",
                "        Torino",
                "  Nord-est",
                "",
            ]
        ),
        encoding="UTF-8",
    )
    monkeypatch.chdir(tmp_path)

    namespace = {"__name__": "__main__"}
    for source in _code_cells():
        exec(compile(source, str(NOTEBOOK), "exec"), namespace)

    step1 = Path("location_step_1.txt").read_text(encoding="UTF-8")
    step2 = Path("location_step_2.csv").read_text(encoding="UTF-8")
    assert "State*Italia;" in step1
    assert "Macro Region*Nord-est;" in step1
    assert "Geographic Area*Nord-est;" not in step1
    lines = step2.splitlines()
    assert lines[0] == "State,Geographic Area,Macro Region,Region,Province,Comune;"
    assert "Italia,Nord-ovest,Nord-ovest,Piemonte,Torino,Torino;" in step2
