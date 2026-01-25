# CLI tools for Continuous Label Printer

Using label printers with continuous label rolls, e.g. Brother QL 700, have a unique usablity issue: the general concept of a fixed paper size doesn't make sense. While the width is fixed, the length can and should be adjusted for whatever is printed.

As an alternative to vendor-provided UI label editors, this project provides two tools to create and print custom labels with ease.

The tool `create-label.py` allows to enter a multi-line label and create a preview. If the preview looks good, it can be either saved to a PDF or printed directly. The rendering code uses a fixed font, but automatically reduces the font size until each line fits without clipping. Optionally, each line can be resized individually.

A saved PDF can be printed with the tool `print-pdf.py` at a later time.


## Installation

The tools are written in Python and require additional packages.

Please use the Python package manager of choice to install:
- pypdf
- reportlab
- prompt_toolkit


### Installation using Python venv module

To use the built-in Python virtual environment:
- `python -m venv venv`
- `source venv/bin/activate`
- `pip3 install -r requirements.txt`

It's sufficient to activate the virtual environment later.


## Configuration

Before you can use the tools, please specify the PRINTER_NAME and the LABEL_WIDTH_MM in the configuration file `config.py`.


## Technical Background

The main issue with continous paper is that there's no fixed paper size, which requires to manually provide the paper size as an optional argument to the lp (lineprint) command line tool. The `print-pdf.py` uses the height of the specified PDF and provides it.

