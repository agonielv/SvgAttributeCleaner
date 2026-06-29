from __future__ import annotations

from pathlib import Path

from svg_attribute_cleaner.cleaner import clean_svg_attributes, clean_svg_folder

FIXTURE = Path(__file__).parent / "fixtures" / "sample.svg"


def test_delete_data_name(tmp_path):
    out = tmp_path / "out.svg"
    result = clean_svg_attributes(str(FIXTURE), str(out), ["data-name"])
    text = out.read_text(encoding="utf-8")
    assert result["success"]
    assert result["removed_counts"]["data-name"] == 3
    assert "data-name" not in text
    assert "<path" in text and "<svg" in text and "<rect" in text


def test_delete_multiple_attributes(tmp_path):
    out = tmp_path / "out.svg"
    result = clean_svg_attributes(str(FIXTURE), str(out), ["data-name", "id"])
    text = out.read_text(encoding="utf-8")
    assert result["total_removed"] == 5
    assert "data-name" not in text
    assert "id=" not in text


def test_missing_attribute_is_zero(tmp_path):
    out = tmp_path / "out.svg"
    result = clean_svg_attributes(str(FIXTURE), str(out), ["missing"])
    assert result["success"]
    assert result["removed_counts"]["missing"] == 0


def test_single_quotes_and_chinese_removed_preserve_mode(tmp_path):
    out = tmp_path / "out.svg"
    result = clean_svg_attributes(str(FIXTURE), str(out), ["data-name"], preserve_format=True)
    text = out.read_text(encoding="utf-8")
    assert result["removed_counts"]["data-name"] == 3
    assert "图层 1" not in text
    assert "data-name='14278031'" not in text


def test_namespaced_attribute_removed(tmp_path):
    out = tmp_path / "out.svg"
    result = clean_svg_attributes(str(FIXTURE), str(out), ["inkscape:label"])
    text = out.read_text(encoding="utf-8")
    assert result["removed_counts"]["inkscape:label"] == 1
    assert "label" not in text


def test_unselected_attributes_are_preserved(tmp_path):
    out = tmp_path / "out.svg"
    clean_svg_attributes(str(FIXTURE), str(out), ["data-name"])
    text = out.read_text(encoding="utf-8")
    assert "viewBox" in text
    assert "d=\"M0 0L10 10\"" in text
    assert "style=\"fill:#dee2e7\"" in text


def test_batch_folder_processing(tmp_path):
    input_dir = tmp_path / "in"
    input_dir.mkdir()
    (input_dir / "a.svg").write_text(FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
    (input_dir / "b.svg").write_text(FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
    output_dir = tmp_path / "out"
    results = clean_svg_folder(str(input_dir), str(output_dir), ["data-name"])
    assert len(results) == 2
    assert (output_dir / "a_cleaned.svg").exists()
    assert (output_dir / "b_cleaned.svg").exists()


def test_dry_run_does_not_write_output(tmp_path):
    out = tmp_path / "out.svg"
    result = clean_svg_attributes(str(FIXTURE), str(out), ["data-name"], dry_run=True)
    assert result["success"]
    assert result["total_removed"] == 3
    assert not out.exists()
