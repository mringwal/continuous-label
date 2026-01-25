#!/usr/bin/env python3

# Minimal script to print PDF on 62mm roll of Brother QL-700

# Requirements: pip install pypdf

import sys
import subprocess
import argparse
from pathlib import Path

from pypdf import PdfReader

from config import LABEL_WIDTH_MM, PRINTER_NAME

MAX_WIDTH_MM = LABEL_WIDTH_MM + 0.5
MM_PER_INCH = 25.4
POINTS_PER_INCH = 72.0


def die(msg: str, code: int = 1):
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(code)


def main():
    parser = argparse.ArgumentParser(
        description="Print a PDF label on Brother QL-700 with explicit PageSize"
    )
    parser.add_argument(
        "-n", "--dry-run",
        action="store_true",
        help="Do not print, just show the lp command"
    )
    parser.add_argument(
        "pdf",
        help="PDF file to print"
    )

    args = parser.parse_args()
    pdf_path = Path(args.pdf)

    if not pdf_path.exists():
        die(f"File not found: {pdf_path}")

    if pdf_path.suffix.lower() != ".pdf":
        die("Input file must be a PDF")

    reader = PdfReader(str(pdf_path))

    if len(reader.pages) != 1:
        die("PDF must contain exactly one page")

    page = reader.pages[0]
    media_box = page.mediabox

    width_pt = float(media_box.width)
    height_pt = float(media_box.height)

    # PDF units are points
    width_mm = width_pt * MM_PER_INCH / POINTS_PER_INCH
    height_mm = height_pt * MM_PER_INCH / POINTS_PER_INCH

    if width_mm > MAX_WIDTH_MM:
        die(
            f"PDF width {width_mm:.2f} mm exceeds roll width "
            f"{MAX_WIDTH_MM:.2f} mm"
        )

    # Brother QL CUPS driver accepts Custom size in mm
    page_size = f"Custom.{width_mm:.2f}x{height_mm:.2f}mm"

    lp_cmd = [
        "lp",
        "-d", PRINTER_NAME,
        "-o", f"PageSize={page_size}",
        str(pdf_path),
    ]

    if args.dry_run:
        print("Dry run — lp command would be:\n")
        print(" ".join(lp_cmd))
        print(
            f"\nPDF size: {width_mm:.2f} × {height_mm:.2f} mm"
        )
        return

    try:
        subprocess.run(lp_cmd, check=True)
    except subprocess.CalledProcessError as e:
        die(f"Printing failed: {e}")

    print(
        f"Printed {pdf_path.name} "
        f"({width_mm:.2f} × {height_mm:.2f} mm)"
    )


if __name__ == "__main__":
    main()
