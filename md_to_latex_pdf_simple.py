#!/usr/bin/env python3
"""
Simplified converter for Markdown files to LaTeX and PDF.
Uses a very basic approach to maximize compatibility and reliability.
"""
import os
import re
import subprocess
import sys
import shutil
from pathlib import Path

def clean_temp_files(base_path):
    """Remove LaTeX temporary files"""
    extensions = ['.aux', '.log', '.out', '.toc', '.lof', '.lot', '.fls', '.fdb_latexmk']
    for ext in extensions:
        try:
            os.remove(f"{base_path}{ext}")
        except FileNotFoundError:
            pass

def escape_latex(text):
    """Escape LaTeX special characters in text"""
    # First, handle backslashes to avoid double escaping
    text = text.replace('\\', '\\textbackslash{}')
    
    # Replace other special characters
    replacements = [
        ('%', '\\%'),
        ('$', '\\$'),
        ('#', '\\#'),
        ('&', '\\&'),
        ('_', '\\_'),
        ('{', '\\{'),
        ('}', '\\}'),
        ('~', '\\textasciitilde{}'),
        ('^', '\\textasciicircum{}'),
    ]
    
    for char, replacement in replacements:
        text = text.replace(char, replacement)
    
    # Handle Unicode characters by replacing them with LaTeX-safe versions
    unicode_replacements = {
        '∏': '$\\prod$',  # Product symbol
        '∑': '$\\sum$',   # Summation
        '∆': '$\\Delta$', # Delta
        '≤': '$\\leq$',   # Less than or equal
        '≥': '$\\geq$',   # Greater than or equal
        '≠': '$\\neq$',   # Not equal
        '≈': '$\\approx$', # Approximately equal
        '→': '$\\rightarrow$', # Right arrow
        '←': '$\\leftarrow$', # Left arrow
        '↑': '$\\uparrow$', # Up arrow
        '↓': '$\\downarrow$', # Down arrow
    }
    
    for char, replacement in unicode_replacements.items():
        text = text.replace(char, replacement)
    
    return text

def md_to_latex_simple(md_content):
    """Convert Markdown content to LaTeX using a very simple approach"""
    # Basic LaTeX document structure - ultra minimal for maximum compatibility
    latex_preamble = r"""
\documentclass[12pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\usepackage{graphicx}
\usepackage{hyperref}
\usepackage{xcolor}
\usepackage{amsmath}
\usepackage[margin=1in]{geometry}

% Define basic colors
\definecolor{linkcolor}{RGB}{0,102,204}

% Setup hyperlinks
\hypersetup{colorlinks=true,linkcolor=linkcolor,citecolor=linkcolor,urlcolor=linkcolor}

\begin{document}
"""

    latex_end = r"""
\end{document}
"""

    # Extract title and author if they exist
    lines = md_content.strip().split('\n')
    title = ""
    
    # Check for title (# Title)
    if lines and lines[0].startswith('# '):
        title = lines[0][2:].strip()
        # Escape special characters in title
        title = escape_latex(title)
        lines = lines[1:]  # Remove title line
    
    # Process title for LaTeX
    latex_title = ""
    if title:
        latex_title = f"\\title{{{title}}}\n\\author{{}}\n\\date{{\\today}}\n\\maketitle\n\\tableofcontents\n\\newpage\n"
    
    # Very basic processing to convert Markdown to LaTeX
    result = []
    in_list = False
    
    # Join remaining lines back together
    md_content = '\n'.join(lines)
    
    # Replace code blocks with simple verbatim environment
    md_content = re.sub(r'```.*?\n(.*?)```', r'\\begin{verbatim}\1\\end{verbatim}', 
                       md_content, flags=re.DOTALL)
    
    # Process each line to handle headers and list items
    lines = md_content.split('\n')
    for i, line in enumerate(lines):
        # Clean up line and escape LaTeX special characters
        if line.strip():
            # Handle headers first (before escaping)
            if line.startswith('# '):
                result.append(f"\\section{{{escape_latex(line[2:])}}}")
            elif line.startswith('## '):
                result.append(f"\\subsection{{{escape_latex(line[3:])}}}")
            elif line.startswith('### '):
                result.append(f"\\subsubsection{{{escape_latex(line[4:])}}}")
            elif line.startswith('#### '):
                result.append(f"\\paragraph{{{escape_latex(line[5:])}}}")
            # Handle list items
            elif line.strip().startswith('* ') or line.strip().startswith('- '):
                # Start list if not already in one
                if not in_list:
                    result.append('\\begin{itemize}')
                    in_list = True
                
                # Add list item with escaped content
                item_text = line.strip()[2:]  # Remove the list marker
                result.append(f"\\item {escape_latex(item_text)}")
            else:
                # If we were in a list and now we're not, close the list
                if in_list and not line.strip() == "":
                    result.append('\\end{itemize}')
                    in_list = False
                
                # Regular text line - just escape it if it's not a verbatim block
                if "\\begin{verbatim}" not in line and "\\end{verbatim}" not in line:
                    line = escape_latex(line)
                
                # Handle bold and italic - must do this after escaping
                line = re.sub(r'\\\*\\\*(.+?)\\\*\\\*', r'\\textbf{\1}', line)
                line = re.sub(r'\\\*(.+?)\\\*', r'\\textit{\1}', line)
                
                # Handle inline code - must do this after escaping
                line = re.sub(r'`([^`]+)`', r'\\texttt{\1}', line)
                
                # Basic link handling - convert [text](url) to simple emphasized text
                line = re.sub(r'\\\[([^\\\]]+)\\\]\\\(([^\\\)]+)\\\)', r'\\textit{\1}', line)
                
                result.append(line)
    
    # Close any open list at the end
    if in_list:
        result.append('\\end{itemize}')
    
    # Join everything together
    latex_content = latex_preamble + latex_title + '\n'.join(result) + latex_end
    
    return latex_content

def process_file(md_file_path):
    """Process a single Markdown file to LaTeX and PDF"""
    print(f"Processing {md_file_path}...")
    
    # Create a clean directory for LaTeX files
    latex_dir = "latex_temp"
    if os.path.exists(latex_dir):
        shutil.rmtree(latex_dir)
    os.makedirs(latex_dir, exist_ok=True)
    
    try:
        # Read the markdown content
        with open(md_file_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        # Get base name for output files
        base_name = os.path.splitext(os.path.basename(md_file_path))[0]
        tex_file_path = f"{latex_dir}/{base_name}.tex"
        
        # Convert to LaTeX using simpler approach
        print(f"Converting Markdown to LaTeX...")
        latex_content = md_to_latex_simple(md_content)
        
        # Write LaTeX file
        with open(tex_file_path, 'w', encoding='utf-8') as f:
            f.write(latex_content)
        
        # Determine output PDF path - place in same directory as source MD file
        output_dir = os.path.dirname(md_file_path)
        output_pdf = f"{output_dir}/{base_name}.pdf"
        
        # Compile to PDF using pdflatex
        print(f"Compiling {tex_file_path} to PDF...")
        
        # First run - capture output for debugging
        compile_result = subprocess.run(
            ['pdflatex', '-interaction=nonstopmode', f'-output-directory={latex_dir}', tex_file_path],
            capture_output=True,
            text=True
        )
        
        # Check for LaTeX errors and print them
        if compile_result.returncode != 0:
            print(f"Warning: First LaTeX compilation had issues:")
            # Extract and print the relevant error part
            error_output = compile_result.stdout or compile_result.stderr
            error_lines = [line for line in error_output.splitlines() if "error" in line.lower() or "!" in line]
            for line in error_lines[:10]:  # Print first 10 error lines
                print(f"  {line}")
            print("  ...")
            print("Continuing with second pass...")
        
        # Second run for cross-references
        compile_result = subprocess.run(
            ['pdflatex', '-interaction=nonstopmode', f'-output-directory={latex_dir}', tex_file_path],
            capture_output=True,
            text=True
        )
        
        # Copy LaTeX log file for debugging
        log_file = f"{latex_dir}/{base_name}.log"
        if os.path.exists(log_file):
            debug_log = f"{output_dir}/{base_name}.latex.log"
            shutil.copy2(log_file, debug_log)
            print(f"LaTeX log saved to: {debug_log}")
        
        # Check again for errors on second pass
        if compile_result.returncode != 0:
            print(f"Error in LaTeX compilation. See log for details.")
            return False
        
        # Copy the resulting PDF to the output location
        pdf_file = f"{latex_dir}/{base_name}.pdf"
        if os.path.exists(pdf_file):
            shutil.copy2(pdf_file, output_pdf)
            print(f"PDF created: {output_pdf}")
            
            # Verify PDF is valid
            try:
                with open(pdf_file, 'rb') as f:
                    header = f.read(5)
                    if header != b'%PDF-':
                        print(f"Warning: Generated PDF does not have a valid PDF header")
                        return False
            except Exception as e:
                print(f"Error reading PDF file: {e}")
                return False
                
            return True
        else:
            print(f"Error: PDF file not created at {pdf_file}")
            return False
    
    except Exception as e:
        print(f"Error processing file: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function to process Markdown files"""
    import argparse
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Convert Markdown files to LaTeX-based PDFs')
    parser.add_argument('filename', nargs='?', help='Specific Markdown file to convert (if omitted, converts all .md files in the outputs directory)')
    parser.add_argument('--debug', action='store_true', help='Keep temporary files for debugging')
    args = parser.parse_args()
    
    # If a specific file is provided
    if args.filename:
        file_path = Path(args.filename)
        
        # Check if the file exists
        if not file_path.exists():
            print(f"Error: File {args.filename} does not exist.")
            return
        
        # Check if it's a Markdown file
        if not file_path.suffix.lower() == '.md':
            print(f"Error: {args.filename} is not a Markdown file (.md extension required).")
            return
        
        # Process the specified file
        print(f"Processing single file: {file_path}")
        if process_file(file_path):
            print(f"Successfully converted {file_path} to PDF.")
        else:
            print(f"Failed to convert {file_path} to PDF.")
    
    # If no specific file is provided, process all .md files in the outputs directory
    else:
        outputs_dir = Path('outputs')
        
        if not outputs_dir.exists() or not outputs_dir.is_dir():
            print(f"Error: Directory {outputs_dir} does not exist.")
            return
        
        # Get all markdown files
        md_files = list(outputs_dir.glob('*.md'))
        
        if not md_files:
            print(f"No markdown files found in {outputs_dir}")
            return
        
        print(f"Found {len(md_files)} markdown files to process.")
        
        # Process each file
        successful = 0
        for md_file in md_files:
            if process_file(md_file):
                successful += 1
        
        print(f"Processed {successful} out of {len(md_files)} files successfully.")
        print(f"PDF files are available in the same directory as the Markdown files.")
    
    # Clean up temporary files if not in debug mode
    if not args.debug:
        latex_dir = "latex_temp"
        if os.path.exists(latex_dir):
            shutil.rmtree(latex_dir)
            print(f"Cleaned up temporary files in {latex_dir}")
    else:
        print(f"Temporary files kept in latex_temp directory for debugging")

if __name__ == "__main__":
    main()