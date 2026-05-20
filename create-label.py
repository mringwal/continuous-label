#!/usr/bin/env python3

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from prompt_toolkit import prompt
from prompt_toolkit.key_binding import KeyBindings
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from config import LABEL_WIDTH_MM, PRINTER_NAME


# Script goal:
# - Render text labels as PDFs sized for a continuous 62mm roll.
# - Preview the result, then optionally save or print it.

# Usage:
# - Interactive (no text arg): `python3 label.py`
# - One-liner: `python3 label.py "Line 1"` or `python3 label.py $'Line 1\nLine 2'`
# - Options: `--fit global|line`, `--margin-mm 3`, `--dry-run`

## Configuration

# Font to use
FONT_NAME = "Arial"
FONT_SIZE_PT = 20
LINE_SPACING = 1.2

# Label margins
TOP_PADDING_PT = 5
BOTTOM_PADDING_PT = 10
SIDE_MARGIN_MM = 3.0

# In 'global' fit mode, font size is reduced for all lines equally
# While in 'line' fit mode, the font is only reduced for too-long lines
FIT_MODE = "global"


def register_arial() -> None:
    arial_candidates = [
        "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        os.path.expanduser("~/Library/Fonts/Arial.ttf"),
    ]
    for path in arial_candidates:
        if os.path.exists(path):
            pdfmetrics.registerFont(TTFont(FONT_NAME, path))
            return
    raise FileNotFoundError(
        "Arial.ttf not found. Install Arial or update the path in label.py."
    )


def render_pdf(
    text: str,
    output_path: Path,
    fit_mode: str = FIT_MODE,
    side_margin_mm: float = SIDE_MARGIN_MM,
) -> float:
    width = LABEL_WIDTH_MM * mm
    lines = text.splitlines() or [""]

    register_arial()

    if fit_mode not in {"global", "line"}:
        raise ValueError("fit_mode must be 'global' or 'line'")

    max_width_pt = width - (2 * side_margin_mm * mm)
    if fit_mode == "global":
        widest_line = max(
            pdfmetrics.stringWidth(line, FONT_NAME, FONT_SIZE_PT)
            for line in lines
        )
        scale = min(1.0, max_width_pt / widest_line) if widest_line > 0 else 1.0
        base_font_size = max(1.0, FONT_SIZE_PT * scale)
        font_sizes = [base_font_size] * len(lines)
    else:
        font_sizes = []
        for line in lines:
            line_width = pdfmetrics.stringWidth(line, FONT_NAME, FONT_SIZE_PT)
            scale = min(1.0, max_width_pt / line_width) if line_width > 0 else 1.0
            font_sizes.append(max(1.0, FONT_SIZE_PT * scale))

    leading = max(font_sizes) * LINE_SPACING
    text_height = (len(lines) - 1) * leading + max(font_sizes)
    height = max(text_height + TOP_PADDING_PT + BOTTOM_PADDING_PT, 1)

    c = canvas.Canvas(str(output_path), pagesize=(width, height))

    y_start = height - TOP_PADDING_PT - max(font_sizes)
    for i, (line, font_size) in enumerate(zip(lines, font_sizes)):
        c.setFont(FONT_NAME, font_size)
        line_width = pdfmetrics.stringWidth(line, FONT_NAME, font_size)
        x = (side_margin_mm * mm) + max(0, (max_width_pt - line_width) / 2)
        y = y_start - (i * leading)
        c.drawString(x, y, line)

    c.showPage()
    c.save()
    return height / mm


def open_pdf(path: Path) -> None:
    if sys.platform == "darwin":
        subprocess.run(["open", str(path)], check=False)
    elif sys.platform.startswith("win"):
        os.startfile(str(path))  # type: ignore[attr-defined]
    else:
        subprocess.run(["xdg-open", str(path)], check=False)


def print_pdf(path: Path, height_mm: float, dry_run: bool) -> None:
    page_size = f"Custom.{LABEL_WIDTH_MM:.0f}x{height_mm:.0f}mm"
    lp_cmd = [
        "lp",
        "-d",
        PRINTER_NAME,
        "-o",
        f"PageSize={page_size}",
        str(path),
    ]
    if dry_run:
        print("Dry run — lp command would be:\n")
        print(" ".join(lp_cmd))
        return
    try:
        subprocess.run(lp_cmd, check=True)
    except subprocess.CalledProcessError as exc:
        print(f"Printing failed: {exc}", file=sys.stderr)

def prompt_label_text(existing_text: str = "") -> str:
    bindings = KeyBindings()

    @bindings.add("escape", eager=True)
    def _(event):
        event.app.exit(result=event.app.current_buffer.text)

    return prompt(
        "Label text (Esc to finish):\n",
        multiline=True,
        default=existing_text,
        key_bindings=bindings,
    ).strip()


def interactive_flow(dry_run: bool, fit_mode: str, side_margin_mm: float) -> int:

    text = prompt_label_text()
    if not text:
        print("Error: label text is required.", file=sys.stderr)
        return 1

    while True:
        with tempfile.NamedTemporaryFile(
            suffix=".pdf",
            delete=False,
            prefix="label_preview_",
        ) as tmp:
            preview_path = Path(tmp.name)

        height_mm = render_pdf(text, preview_path, fit_mode, side_margin_mm)
        open_pdf(preview_path)

        if fit_mode == "global":
            fit_mode_other = "line"
        else:
            fit_mode_other = "global"

        print(
            "\nWhat next?\n"
            "1) edit again\n"
            "2) switch to '" + fit_mode_other + "' fit mode\n"
            "3) save as label.pdf\n"
            "4) print\n"
            "5) exit"
        )
        choice = input("> ").strip()

        if choice == "1":
            text = prompt_label_text(text)
            if not text:
                print("Error: label text is required.", file=sys.stderr)
                return 1
        elif choice == "2":
            fit_mode = fit_mode_other
        elif choice == "3":
            output_path = Path("label.pdf").resolve()
            render_pdf(text, output_path, fit_mode, side_margin_mm)
            print(f"Wrote {output_path}")
            return 0
        elif choice == "4":
            print_pdf(preview_path, height_mm, dry_run)
        elif choice == "5":
            return 0
        else:
            print("Please choose 1..5")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render a label to PDF (interactive when no text is given)."
    )
    parser.add_argument(
        "text",
        nargs="?",
        help="Label text to render; omit to enter interactive mode",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="label.pdf",
        help="Output PDF path",
    )
    parser.add_argument(
        "--fit",
        choices=["global", "line"],
        default=FIT_MODE,
        help="Font fit mode when lines exceed label width",
    )
    parser.add_argument(
        "--margin-mm",
        type=float,
        default=SIDE_MARGIN_MM,
        help="Non-printable side margin in millimeters",
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="Show the print command without running it",
    )
    args = parser.parse_args()

    if not args.text:
        return interactive_flow(args.dry_run, args.fit, args.margin_mm)

    text = args.text.strip()
    if not text:
        print("Error: label text is required.", file=sys.stderr)
        return 1

    output_path = Path(args.output).resolve()
    render_pdf(text, output_path, args.fit, args.margin_mm)
    open_pdf(output_path)
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
