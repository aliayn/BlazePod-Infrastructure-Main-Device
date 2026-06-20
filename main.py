#!/usr/bin/env python3
"""
Run the full Blazepod clone research workflow.

This entry point coordinates the existing tools in this workspace:
1. Optionally refresh Iranian part pricing.
2. Build the English deep-dive DOCX.
3. Build the BOM XLSX.
4. Build the Farsi PDF.

Typical usage:
    python main.py
    python main.py --use-existing-parts
    python main.py --skip-pdf
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DEFAULT_QUERIES = ROOT / ".tmp" / "part_queries.json"
DEFAULT_PARTS = ROOT / ".tmp" / "iran_parts.json"
DEFAULT_RESEARCH = ROOT / ".tmp" / "blazepod_research.json"
DEFAULT_EXPORT = ROOT / "export"


def run_command(command: list[str]) -> None:
    """Run a workflow command and stop immediately if it fails."""
    print(f"\n$ {' '.join(command)}")
    subprocess.run(command, cwd=ROOT, check=True)


def require_file(path: Path, purpose: str) -> None:
    if path.exists():
        return
    raise SystemExit(
        f"Missing {purpose}: {path}\n"
        "Run the workflow preparation steps or restore the .tmp input files first."
    )


def summarize_parts(parts_path: Path) -> None:
    if not parts_path.exists():
        return

    with parts_path.open(encoding="utf-8") as file:
        parts = json.load(file)

    total = len(parts)
    priced = sum(
        1
        for part in parts
        if any(result.get("price_toman") for result in part.get("results", []))
    )
    needs_confirmation = [
        part.get("id", part.get("query", "unknown"))
        for part in parts
        if part.get("needs_confirmation")
    ]

    print("\nSummary")
    print(f"- BOM pricing: {priced}/{total} parts have an automatic price.")
    if needs_confirmation:
        print(f"- Needs manual confirmation: {', '.join(needs_confirmation)}")
    else:
        print("- Needs manual confirmation: none")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run all deliverable builders for this workspace."
    )
    parser.add_argument(
        "--queries",
        type=Path,
        default=DEFAULT_QUERIES,
        help="Path to part query input JSON.",
    )
    parser.add_argument(
        "--parts",
        type=Path,
        default=DEFAULT_PARTS,
        help="Path to part pricing JSON.",
    )
    parser.add_argument(
        "--research",
        type=Path,
        default=DEFAULT_RESEARCH,
        help="Path to research JSON.",
    )
    parser.add_argument(
        "--export-dir",
        type=Path,
        default=DEFAULT_EXPORT,
        help="Directory for final deliverables.",
    )
    parser.add_argument(
        "--use-existing-parts",
        action="store_true",
        help="Skip live shop fetching and reuse the existing parts JSON.",
    )
    parser.add_argument(
        "--skip-docx",
        action="store_true",
        help="Skip the English DOCX deliverable.",
    )
    parser.add_argument(
        "--skip-bom",
        action="store_true",
        help="Skip the BOM XLSX deliverable.",
    )
    parser.add_argument(
        "--skip-pdf",
        action="store_true",
        help="Skip the Farsi PDF deliverable.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=15,
        help="Per-request timeout in seconds for shop fetching.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Delay between shop requests in seconds.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    queries_path = args.queries.resolve()
    parts_path = args.parts.resolve()
    research_path = args.research.resolve()
    export_dir = args.export_dir.resolve()
    export_dir.mkdir(parents=True, exist_ok=True)

    require_file(research_path, "research input")

    if args.use_existing_parts:
        require_file(parts_path, "parts input")
    else:
        require_file(queries_path, "part queries input")
        run_command(
            [
                sys.executable,
                "tools/iran_parts.py",
                "--queries",
                str(queries_path),
                "--out",
                str(parts_path),
                "--timeout",
                str(args.timeout),
                "--delay",
                str(args.delay),
            ]
        )

    if not args.skip_docx:
        run_command(
            [
                sys.executable,
                "tools/build_doc.py",
                "--research",
                str(research_path),
                "--out",
                str(export_dir / "blazepod-deep-dive.docx"),
            ]
        )

    if not args.skip_bom:
        require_file(parts_path, "parts input")
        run_command(
            [
                sys.executable,
                "tools/build_bom.py",
                "--parts",
                str(parts_path),
                "--out",
                str(export_dir / "blazepod-clone-bom.xlsx"),
            ]
        )

    if not args.skip_pdf:
        require_file(parts_path, "parts input")
        run_command(
            [
                sys.executable,
                "tools/build_farsi_pdf.py",
                "--research",
                str(research_path),
                "--parts",
                str(parts_path),
                "--out",
                str(export_dir / "blazepod-clone-fa.pdf"),
                "--html-cache",
                str(ROOT / ".tmp" / "farsi.html"),
            ]
        )

    summarize_parts(parts_path)
    print(f"\nDone. Deliverables are in: {export_dir}")


if __name__ == "__main__":
    main()
