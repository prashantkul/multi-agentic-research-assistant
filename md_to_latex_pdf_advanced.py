#!/usr/bin/env python3
"""
Advanced converter for Markdown files to LaTeX and PDF.
Handles nested lists, tables, code blocks, and other complex elements.
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
    special_chars = {
        '%': '\\%',
        '$': '\\$',
        '#': '\\#',
        '&': '\\&',
        '_': '\\_',
        '{': '\\{',
        '}': '\\}',
        '~': '\\textasciitilde{}',
        '^': '\\textasciicircum{}',
        '\\': '\\textbackslash{}',
    }
    
    # Handle backslash first to avoid double escaping
    if '\\' in text:
        text = text.replace('\\', '\\textbackslash{}')
    
    # Replace other special characters
    for char, replacement in special_chars.items():
        if char != '\\':  # Skip backslash as we already handled it
            text = text.replace(char, replacement)
    
    return text

def sanitize_for_latex(text):
    """Sanitize text for LaTeX commands like section, making it safe for command arguments"""
    # Remove or escape problematic characters for LaTeX command arguments
    # This is different from general text escaping as it's for command arguments
    return text.replace('\\', '').replace('{', '').replace('}', '').replace('&', '\\&')

def md_to_latex_advanced(md_content):
    """Convert Markdown content to LaTeX format with advanced formatting"""
    # Basic LaTeX document structure - using a simpler configuration for reliability
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
\usepackage{titlesec}
\usepackage{enumitem}
\usepackage{listings}

% Define basic colors
\definecolor{linkcolor}{RGB}{0,102,204}
\definecolor{codebg}{RGB}{240,240,240}

% Setup hyperlinks
\hypersetup{colorlinks=true,linkcolor=linkcolor,citecolor=linkcolor,urlcolor=linkcolor}

% Section formatting
\titleformat{\section}{\normalfont\Large\bfseries}{\thesection}{1em}{}
\titleformat{\subsection}{\normalfont\large\bfseries}{\thesubsection}{1em}{}
\titleformat{\subsubsection}{\normalfont\normalsize\bfseries}{\thesubsubsection}{1em}{}

% List settings
\setlist[itemize]{leftmargin=2em}

% Code settings
\lstset{
  basicstyle=\ttfamily\small,
  backgroundcolor=\color{codebg},
  breaklines=true,
  captionpos=b,
  frame=single,
  tabsize=2
}

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
        title = sanitize_for_latex(lines[0][2:].strip())
        lines = lines[1:]  # Remove title line
    
    # Process title for LaTeX
    latex_title = ""
    if title:
        latex_title = f"\\title{{{title}}}\n\\author{{}}\n\\date{{\\today}}\n\\maketitle\n\\tableofcontents\n\\newpage\n"
    
    # Join remaining lines back together
    md_content = '\n'.join(lines)
    
    # Pre-process code blocks to protect them from other transformations
    # Replace code blocks with placeholder markers
    code_blocks = []
    
    def replace_code_block(match):
        language = match.group(1).strip() if match.group(1) else ""
        code_content = match.group(2)
        # Save the code block
        marker = f"CODE_BLOCK_{len(code_blocks)}"
        code_blocks.append((language, code_content))
        return marker
    
    # Find all code blocks and replace them with markers
    md_content = re.sub(r'```(.*?)\n(.*?)```', replace_code_block, md_content, flags=re.DOTALL)
    
    # Process headers
    def header_replace(match):
        header_content = sanitize_for_latex(match.group(1))
        return f'\\section{{{header_content}}}'
    
    md_content = re.sub(r'^# (.+)$', header_replace, md_content, flags=re.MULTILINE)
    
    def subheader_replace(match):
        header_content = sanitize_for_latex(match.group(1))
        return f'\\subsection{{{header_content}}}'
    
    md_content = re.sub(r'^## (.+)$', subheader_replace, md_content, flags=re.MULTILINE)
    
    def subsubheader_replace(match):
        header_content = sanitize_for_latex(match.group(1))
        return f'\\subsubsection{{{header_content}}}'
    
    md_content = re.sub(r'^### (.+)$', subsubheader_replace, md_content, flags=re.MULTILINE)
    
    def paragraph_replace(match):
        header_content = sanitize_for_latex(match.group(1))
        return f'\\paragraph{{{header_content}}}'
    
    md_content = re.sub(r'^#### (.+)$', paragraph_replace, md_content, flags=re.MULTILINE)
    
    # Process inline code
    def inline_code_replace(match):
        code = escape_latex(match.group(1))
        return f'\\texttt{{{code}}}'
    
    md_content = re.sub(r'`([^`]+)`', inline_code_replace, md_content)
    
    # Process bold and italic
    def bold_replace(match):
        text = escape_latex(match.group(1))
        return f'\\textbf{{{text}}}'
    
    md_content = re.sub(r'\*\*(.+?)\*\*', bold_replace, md_content)
    
    def italic_replace(match):
        text = escape_latex(match.group(1))
        return f'\\textit{{{text}}}'
    
    md_content = re.sub(r'\*(.+?)\*', italic_replace, md_content)
    
    # Process lists
    lines = md_content.split('\n')
    in_list = False
    result_lines = []
    list_depth = 0
    
    for line in lines:
        # Check if this is a list item
        stripped = line.lstrip()
        indent = len(line) - len(stripped)
        
        if stripped.startswith('* ') or stripped.startswith('- '):
            list_text = escape_latex(stripped[2:])  # Remove the list marker and escape
            
            # Determine list depth based on indentation
            current_depth = indent // 2
            
            # Start a list if we're not in one or need a deeper list
            if not in_list:
                result_lines.append("\\begin{itemize}")
                in_list = True
                list_depth = current_depth
            elif current_depth > list_depth:
                result_lines.append("\\begin{itemize}")
                list_depth = current_depth
            elif current_depth < list_depth:
                # Close deeper lists
                for _ in range(list_depth - current_depth):
                    result_lines.append("\\end{itemize}")
                list_depth = current_depth
            
            # Add the item
            result_lines.append(f"\\item {list_text}")
        else:
            # Close any open lists
            if in_list:
                for _ in range(list_depth + 1):
                    result_lines.append("\\end{itemize}")
                in_list = False
                list_depth = 0
            
            # Add the non-list line
            result_lines.append(line)
    
    # Close any open lists at the end
    if in_list:
        for _ in range(list_depth + 1):
            result_lines.append("\\end{itemize}")
    
    # Rejoin the lines
    md_content = '\n'.join(result_lines)
    
    # Process horizontal rules
    md_content = re.sub(r'^---+$', r'\\rule{\\linewidth}{0.5pt}', md_content, flags=re.MULTILINE)
    
    # Process links
    def link_replace(match):
        text = escape_latex(match.group(1))
        url = match.group(2)
        # Use a safer approach for URLs
        return f'\\href{{{url}}}{{{text}}}'
    
    md_content = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', link_replace, md_content)
    
    # Restore code blocks
    for i, (language, code) in enumerate(code_blocks):
        marker = f"CODE_BLOCK_{i}"
        language_opt = language if language else "text"
        escaped_code = code.replace('\\', '\\\\')  # Extra escape for backslashes in code
        
        # Use a safer verbatim approach for code blocks
        if marker in md_content:
            listing_block = f"""
\\begin{{lstlisting}}[language={language_opt}]
{code}
\\end{{lstlisting}}
"""
            md_content = md_content.replace(marker, listing_block)
    
    # Combine everything
    latex_content = latex_preamble + latex_title + md_content + latex_end
    
    return latex_content

def process_file(md_file_path, use_advanced=True):
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
        
        # Convert to LaTeX
        print(f"Converting Markdown to LaTeX...")
        latex_content = md_to_latex_advanced(md_content)
        
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
        if process_file(file_path, use_advanced=True):
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
            if process_file(md_file, use_advanced=True):
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