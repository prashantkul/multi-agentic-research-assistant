#!/bin/bash
# Script to convert Markdown files to PDFs using an improved LaTeX approach
# Usage: ./convert_to_pdf.sh [markdown_file.md]
#   If a markdown file is specified, only that file will be converted
#   If no file is specified, all markdown files in the outputs directory will be converted

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is required but not found. Please install Python 3."
    exit 1
fi

# Check if pdflatex is installed
if ! command -v pdflatex &> /dev/null; then
    echo "pdflatex is required but not found. Please install TeX Live or another LaTeX distribution."
    echo "On macOS: brew install --cask mactex"
    echo "On Ubuntu: sudo apt-get install texlive-latex-extra"
    echo "On Windows: Install MiKTeX or TeX Live"
    exit 1
fi

# Make the script executable
chmod +x md_to_latex_pdf_improved.py

# Check if a specific file was provided
if [ $# -eq 0 ]; then
    # No arguments, convert all files in outputs directory
    echo "Starting conversion of all Markdown files in the outputs directory..."
    python3 md_to_latex_pdf_improved.py
else
    # Convert the specified file
    echo "Starting conversion of $1 to PDF..."
    python3 md_to_latex_pdf_improved.py "$1"
fi

# Check if conversion was successful
if [ $? -eq 0 ]; then
    echo "Conversion complete!"
else
    echo "Error during conversion. Please check the error messages above."
    exit 1
fi