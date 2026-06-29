from __future__ import annotations

import copy
import re
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

try:
    from lxml import etree
except ModuleNotFoundError:  # pragma: no cover - exercised in dependency-light environments
    etree = None  # type: ignore[assignment]

from .utils import default_output_path, iter_svg_files


def _base_result(input_path: str, output_path: str | None, attributes: list[str]) -> dict[str, Any]:
    return {
        "input": str(input_path),
        "output": str(output_path) if output_path else None,
        "attributes": attributes,
        "removed_counts": {attr: 0 for attr in attributes},
        "total_removed": 0,
        "processing_time": 0.0,
        "success": False,
        "error": None,
    }


def _namespace_map(input_path: str | Path) -> dict[str, str]:
    namespaces: dict[str, str] = {}
    for _, item in ET.iterparse(str(input_path), events=("start-ns",)):
        prefix, uri = item
        namespaces[prefix] = uri
    return namespaces


def _attribute_aliases(key: str, nsmap: dict[str | None, str]) -> set[str]:
    aliases = {key}
    if key.startswith("{") and "}" in key:
        uri, local = key[1:].split("}", 1)
        aliases.add(local)
        for prefix, ns_uri in nsmap.items():
            if prefix and ns_uri == uri:
                aliases.add(f"{prefix}:{local}")
    return aliases


def _remove_from_lxml_tree(tree: Any, attributes: list[str]) -> dict[str, int]:
    counts = {attr: 0 for attr in attributes}
    for element in tree.iter():
        if not isinstance(element.tag, str):
            continue
        nsmap = element.nsmap or {}
        for key in list(element.attrib.keys()):
            aliases = _attribute_aliases(key, nsmap)
            matched = next((attr for attr in attributes if attr in aliases), None)
            if matched:
                del element.attrib[key]
                counts[matched] += 1
    return counts


def _remove_from_et_tree(root: ET.Element, attributes: list[str], namespaces: dict[str, str]) -> dict[str, int]:
    counts = {attr: 0 for attr in attributes}
    nsmap: dict[str | None, str] = namespaces.copy()
    for element in root.iter():
        for key in list(element.attrib.keys()):
            aliases = _attribute_aliases(key, nsmap)
            matched = next((attr for attr in attributes if attr in aliases), None)
            if matched:
                del element.attrib[key]
                counts[matched] += 1
    return counts


def _parse_xml_lxml(input_path: str | Path) -> Any:
    parser = etree.XMLParser(remove_blank_text=False, remove_comments=False, resolve_entities=False, no_network=True, huge_tree=True)
    return etree.parse(str(input_path), parser)


def _regex_pattern(attribute: str) -> re.Pattern[str]:
    escaped = re.escape(attribute)
    return re.compile(rf"(?P<space>\s+){escaped}\s*=\s*(?:\"[^\"]*\"|'[^']*')")


def _clean_preserve_format(input_path: Path, output_path: Path | None, attributes: list[str], dry_run: bool) -> dict[str, int]:
    text = input_path.read_text(encoding="utf-8")
    counts = {attr: 0 for attr in attributes}
    cleaned = text
    for attr in attributes:
        pattern = _regex_pattern(attr)
        cleaned, count = pattern.subn("", cleaned)
        counts[attr] = count
    if not dry_run and output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(cleaned, encoding="utf-8")
    return counts


def clean_svg_attributes(
    input_path: str,
    output_path: str | None = None,
    attributes: list[str] | None = None,
    mode: str = "xml",
    preserve_format: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Remove selected attributes from one SVG without deleting elements."""
    started = time.time()
    attrs = [attr for attr in (attributes or []) if attr]
    in_path = Path(input_path)
    out_path = Path(output_path) if output_path else default_output_path(in_path)
    result = _base_result(str(in_path), None if dry_run else str(out_path), attrs)
    try:
        if not attrs:
            raise ValueError("No attributes were provided.")
        if not in_path.exists():
            raise FileNotFoundError(f"Input file does not exist: {in_path}")
        if preserve_format or mode == "regex":
            counts = _clean_preserve_format(in_path, None if dry_run else out_path, attrs, dry_run)
        elif etree is not None:
            tree = _parse_xml_lxml(in_path)
            target_tree = copy.deepcopy(tree) if dry_run else tree
            counts = _remove_from_lxml_tree(target_tree, attrs)
            if not dry_run:
                out_path.parent.mkdir(parents=True, exist_ok=True)
                target_tree.write(str(out_path), encoding="utf-8", xml_declaration=True, pretty_print=False)
        else:
            namespaces = _namespace_map(in_path)
            for prefix, uri in namespaces.items():
                ET.register_namespace(prefix, uri)
            tree = ET.parse(str(in_path))
            root = copy.deepcopy(tree.getroot()) if dry_run else tree.getroot()
            counts = _remove_from_et_tree(root, attrs, namespaces)
            if not dry_run:
                out_path.parent.mkdir(parents=True, exist_ok=True)
                tree.write(str(out_path), encoding="utf-8", xml_declaration=True)
        result["removed_counts"] = counts
        result["total_removed"] = sum(counts.values())
        result["success"] = True
    except Exception as exc:  # noqa: BLE001 - reported to GUI/JSON report
        result["error"] = str(exc)
    finally:
        result["processing_time"] = round(time.time() - started, 4)
    return result


def clean_svg_folder(
    input_dir: str,
    output_dir: str | None,
    attributes: list[str],
    recursive: bool = False,
    preserve_format: bool = False,
    dry_run: bool = False,
) -> list[dict[str, Any]]:
    root = Path(input_dir)
    out_root = Path(output_dir) if output_dir else root / "output_cleaned"
    results: list[dict[str, Any]] = []
    for svg_file in iter_svg_files(root, recursive=recursive):
        relative = svg_file.relative_to(root)
        output_path = out_root / relative.with_name(f"{relative.stem}_cleaned{relative.suffix}")
        results.append(clean_svg_attributes(str(svg_file), str(output_path), attributes, preserve_format=preserve_format, dry_run=dry_run))
    return results
