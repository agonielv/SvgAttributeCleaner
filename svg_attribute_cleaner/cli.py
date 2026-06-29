from __future__ import annotations

import argparse
from pathlib import Path

from .cleaner import clean_svg_attributes, clean_svg_folder
from .report import write_report
from .utils import parse_attributes


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Clean selected attributes from SVG files.")
    parser.add_argument("--input", help="Input SVG file")
    parser.add_argument("--output", help="Output SVG file")
    parser.add_argument("--input-dir", help="Input folder containing SVG files")
    parser.add_argument("--output-dir", help="Output folder for cleaned SVG files")
    parser.add_argument("--attrs", required=True, help="Attributes to remove, separated by comma, whitespace, or newlines")
    parser.add_argument("--recursive", action="store_true", help="Process SVG files in subfolders")
    parser.add_argument("--dry-run", action="store_true", help="Preview removal counts without writing SVG files")
    parser.add_argument("--preserve-format", action="store_true", help="Use cautious regex mode to preserve original formatting")
    parser.add_argument("--report", help="JSON report path")
    parser.add_argument("--gui", action="store_true", help="Launch GUI")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.gui:
        from .gui import main as gui_main
        gui_main()
        return 0
    attrs = parse_attributes(args.attrs)
    if args.input_dir:
        results = clean_svg_folder(args.input_dir, args.output_dir, attrs, recursive=args.recursive, preserve_format=args.preserve_format, dry_run=args.dry_run)
        report_dir = Path(args.output_dir or Path(args.input_dir) / "output_cleaned")
    elif args.input:
        result = clean_svg_attributes(args.input, args.output, attrs, preserve_format=args.preserve_format, dry_run=args.dry_run)
        results = [result]
        report_dir = Path(args.output).parent if args.output else Path(args.input).parent
    else:
        parser.error("Provide --input or --input-dir, or use --gui.")
    report_path = Path(args.report) if args.report else report_dir / "clean_report.json"
    write_report(results, report_path)
    for item in results:
        status = "OK" if item["success"] else "FAIL"
        print(f"{status}: {item['input']} -> {item.get('output')} removed={item['total_removed']} error={item.get('error')}")
    print(f"Report: {report_path}")
    return 0 if all(item["success"] for item in results) else 1
