from __future__ import annotations

from pathlib import Path

from svg_attribute_cleaner.cli import main
from svg_attribute_cleaner.utils import parse_attributes

FIXTURE = Path(__file__).parent / "fixtures" / "sample.svg"


def test_cli_file(tmp_path):
    out = tmp_path / "out.svg"
    report = tmp_path / "report.json"
    code = main(["--input", str(FIXTURE), "--output", str(out), "--attrs", "data-name,id", "--report", str(report)])
    assert code == 0
    assert out.exists()
    assert report.exists()


def test_parse_attributes_multiple_separators():
    assert parse_attributes("data-name\ninkscape:label sodipodi:nodetypes,class") == [
        "data-name",
        "inkscape:label",
        "sodipodi:nodetypes",
        "class",
    ]


def test_gui_import_does_not_start_window():
    import svg_attribute_cleaner.gui as gui

    assert hasattr(gui, "SvgAttributeCleanerApp")
