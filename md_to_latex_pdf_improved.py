#!/usr/bin/env python3
"""
Improved converter for Markdown files to LaTeX and PDF.
Handles emphasis, code blocks, list items, tables, and section headers effectively.
"""
import os
import re
import subprocess
import sys
import shutil
import unicodedata
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
    if not text:
        return ""

    # Replace & first as it's a special character in LaTeX (for tables)
    text = text.replace('&', '\\&')

    # Replace other special characters
    replacements = [
        ('%', '\\%'),
        ('$', '\\$'),
        ('#', '\\#'),
        ('_', '\\_'),
        ('{', '\\{'),
        ('}', '\\}'),
        ('~', '\\textasciitilde{}'),
        ('^', '\\textasciicircum{}'),
        ('\\', '\\textbackslash{}'),
    ]

    # Apply replacements in order
    for char, replacement in replacements:
        if char != '\\':  # Skip backslash as we already handled it
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

    # Find any remaining Unicode characters that might cause issues
    result = ""
    for char in text:
        # If it's a non-ASCII character that isn't already handled
        if ord(char) > 127 and char not in unicode_replacements:
            try:
                # Try to find a LaTeX representation for the character
                if unicodedata.category(char).startswith('L'):  # Letter
                    # For letter characters, we can just use them directly in most cases
                    result += char
                elif unicodedata.category(char).startswith('P'):  # Punctuation
                    # For punctuation, try to use LaTeX commands if available
                    name = unicodedata.name(char).lower()
                    if 'dash' in name or 'hyphen' in name:
                        result += '-'
                    elif 'quote' in name:
                        result += "'"
                    else:
                        result += ' '  # Replace with space as fallback
                elif unicodedata.category(char).startswith('S'):  # Symbol
                    # For math symbols, try to use LaTeX math commands
                    name = unicodedata.name(char).lower()
                    if 'product' in name:
                        result += '$\\prod$'
                    elif 'sum' in name:
                        result += '$\\sum$'
                    elif 'integral' in name:
                        result += '$\\int$'
                    elif 'partial' in name:
                        result += '$\\partial$'
                    elif 'infinity' in name:
                        result += '$\\infty$'
                    elif 'arrow' in name:
                        if 'left' in name:
                            result += '$\\leftarrow$'
                        elif 'right' in name:
                            result += '$\\rightarrow$'
                        elif 'up' in name:
                            result += '$\\uparrow$'
                        elif 'down' in name:
                            result += '$\\downarrow$'
                        else:
                            result += '$\\rightarrow$'  # Default arrow
                    else:
                        # For other symbols, replace with a reasonable substitute or just a space
                        result += ' '
                else:
                    # For other Unicode categories, replace with a space
                    result += ' '
            except (ValueError, KeyError):
                # If we can't determine, just replace with a space
                result += ' '
        else:
            # Keep ASCII characters and already-handled Unicode characters
            result += char

    return result

def fix_md_structure(md_content):
    """Fix structural issues in Markdown before conversion"""
    # Fix references - academic references often have specific formatting
    lines = md_content.split('\n')
    fixed_lines = []
    in_references = False
    reference_section_index = -1
    in_multi_agent = False
    multi_agent_section_index = -1

    # Renumbering sections - modify these mappings for section renumbering
    section_map = {
        '# **GroundedMed-LLM': '# **1. GroundedMed-LLM',
        '## **Abstract**': '## **1.1. Abstract**',
        '**1. Background & Literature Review**': '**2. Background & Literature Review**',
        '**2. Problem Statement & Research Gap**': '**3. Problem Statement & Research Gap**',
        '**3. Proposed Gen AI Approach (Methodology)**': '**4. Proposed Gen AI Approach (Methodology)**',
        '**4. Expected Impact in Healthcare**': '**5. Expected Impact in Healthcare**',
        '**5. Limitations or Ethical Considerations**': '**6. Limitations or Ethical Considerations**',
        '**6. References**': '**7. References**'
    }

    # First pass: find the References section and Multi-Agent Reflection section and rename sections
    for i, line in enumerate(lines):
        # Update section numbering for the main sections
        for old_section, new_section in section_map.items():
            if line.startswith(old_section):
                lines[i] = line.replace(old_section, new_section)
                break

        # Update references section pointer
        if line.startswith('**7. References**') or line.startswith('**6. References**'):
            in_references = True
            reference_section_index = i
        elif line.strip() == "**Multi-Agent Reflection**":
            in_multi_agent = True
            multi_agent_section_index = i

    # Second pass: process the content
    i = 0
    while i < len(lines):
        line = lines[i]

        # Start of references section
        if i == reference_section_index:
            fixed_lines.append(line)  # Add the section header
            fixed_lines.append('')    # Add empty line after header
            i += 1
            continue

        # Start of Multi-Agent Reflection section
        if i == multi_agent_section_index:
            fixed_lines.append(line)  # Add the section header
            fixed_lines.append('')    # Add empty line after header
            i += 1
            continue

        # We're in the references section
        if in_references and i > reference_section_index and (multi_agent_section_index == -1 or i < multi_agent_section_index):
            # Check if this is a reference item (starts with *)
            if line.strip().startswith('*'):
                # Keep reference items as is, since they're properly formatted
                fixed_lines.append(line)
            # Handle blank line inside references - skip empty lines between reference items
            elif line.strip() == "" and i+1 < len(lines) and lines[i+1].strip().startswith("*"):
                pass  # Skip blank line between reference items
            else:
                fixed_lines.append(line)
        # We're in the Multi-Agent Reflection section - format numbered lists better
        elif in_multi_agent and i > multi_agent_section_index:
            # Check if this is a numbered list item (e.g., "1.  **Researcher Agent:**")
            if re.match(r'^\d+\.\s+\*\*[^*]+\*\*:', line):
                # Format this as a proper list item
                fixed_lines.append(line)
            else:
                fixed_lines.append(line)
        else:
            # Normal processing for non-reference section
            fixed_lines.append(line)

        i += 1

    return '\n'.join(fixed_lines)

def md_to_latex_improved(md_content):
    """Convert Markdown content to LaTeX with improved handling of formatting"""
    # First fix structural issues in the markdown
    md_content = fix_md_structure(md_content)

    # Basic LaTeX document structure
    latex_preamble = r"""
\documentclass[12pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\usepackage{textcomp}
\usepackage{graphicx}
\usepackage{hyperref}
\usepackage{xcolor}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage[margin=1in]{geometry}
\usepackage{titlesec}
\usepackage{tocloft}

% Define basic colors
\definecolor{linkcolor}{RGB}{0,102,204}
\definecolor{codebg}{RGB}{240,240,240}

% Setup hyperlinks
\hypersetup{colorlinks=true,linkcolor=linkcolor,citecolor=linkcolor,urlcolor=linkcolor}

% Let LaTeX handle section page breaks naturally
% (removed forced page breaks between sections)

% Customize section numbering and appearance
\renewcommand{\thesection}{\arabic{section}}
\renewcommand{\thesubsection}{\thesection.\arabic{subsection}}

% Format section titles
\titleformat{\section}
  {\normalfont\Large\bfseries}{\thesection.}{0.5em}{}
\titleformat{\subsection}
  {\normalfont\large\bfseries}{\thesubsection}{0.5em}{}

% Table of contents customization
\renewcommand{\cfttoctitlefont}{\large\bfseries}
\renewcommand{\cftbeforetoctitleskip}{0pt}
\renewcommand{\cftaftertoctitleskip}{1em}

% Explicitly declare Unicode characters
\DeclareUnicodeCharacter{220F}{$\prod$}  % PRODUCT SYMBOL (∏)
\DeclareUnicodeCharacter{2211}{$\sum$}   % SUMMATION (∑)
\DeclareUnicodeCharacter{0394}{$\Delta$} % DELTA (Δ)
\DeclareUnicodeCharacter{2264}{$\leq$}   % LESS THAN OR EQUAL (≤)
\DeclareUnicodeCharacter{2265}{$\geq$}   % GREATER THAN OR EQUAL (≥)
\DeclareUnicodeCharacter{2260}{$\neq$}   % NOT EQUAL (≠)
\DeclareUnicodeCharacter{2248}{$\approx$} % APPROXIMATELY EQUAL (≈)
\DeclareUnicodeCharacter{2192}{$\rightarrow$} % RIGHT ARROW (→)
\DeclareUnicodeCharacter{2190}{$\leftarrow$}  % LEFT ARROW (←)
\DeclareUnicodeCharacter{2191}{$\uparrow$}    % UP ARROW (↑)
\DeclareUnicodeCharacter{2193}{$\downarrow$}  % DOWN ARROW (↓)

\begin{document}
"""

    latex_end = r"""
\end{document}
"""

    # Extract title and abstract if they exist
    lines = md_content.strip().split('\n')
    title = ""
    abstract = ""
    abstract_start = -1
    abstract_end = -1

    # Check for title (# Title)
    if lines and lines[0].startswith('# '):
        title = lines[0][2:].strip()
        # Remove Markdown formatting from title
        title = title.replace('**', '')
        # Escape special characters in title
        title = escape_latex(title)

        # Look for abstract (## Abstract)
        for i, line in enumerate(lines[1:]):
            if line.startswith('## **1.1. Abstract**') or line.startswith('## **Abstract**'):
                abstract_start = i + 1  # +1 because we're starting from lines[1]
            elif abstract_start > -1 and line.strip() == '---':
                abstract_end = i + 1  # +1 for the same reason
                break

        # Extract abstract if found
        if abstract_start > -1 and abstract_end > -1:
            abstract_lines = lines[abstract_start+1:abstract_end]
            abstract = ' '.join([line.strip() for line in abstract_lines if line.strip()])
            abstract = escape_latex(abstract)

        lines = lines[1:]  # Remove title line

    # Process title and abstract for LaTeX
    latex_title = ""
    if title:
        latex_title = f"\\title{{{title}}}\n\\author{{}}\n\\date{{\\today}}\n\\maketitle\n"
        if abstract:
            latex_title += f"\\begin{{abstract}}\n{abstract}\n\\end{{abstract}}\n"
        latex_title += "\\tableofcontents\n\\vspace{1em}\n"
    
    # Pre-process to extract and preserve code blocks
    code_blocks = []
    
    def replace_code_block(match):
        code = match.group(2)
        marker = f"CODE_BLOCK_{len(code_blocks)}"
        code_blocks.append(code)
        return marker
    
    # Replace code blocks with markers
    md_content = '\n'.join(lines)
    md_content = re.sub(r'```(.*?)\n(.*?)```', replace_code_block, md_content, flags=re.DOTALL)
    
    # Process Markdown line by line
    result = []
    in_list = False
    in_references = False
    in_multi_agent = False
    in_enum_list = False
    list_stack = []  # Track the current list environments open

    lines = md_content.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]

        # Check if we're in the references section
        if line.startswith("**7. References**") or line.startswith("**6. References**"):
            # Close any open item list before starting a new section
            if in_list:
                result.append("\\end{itemize}")
                in_list = False

            # Close any open enumerated list
            if in_enum_list:
                result.append("\\end{enumerate}")
                in_enum_list = False

            in_references = True
            # Format as a proper section header
            result.append("\\section{References}")
            i += 1
            continue

        # Special handling for horizontal rules
        if line.strip() == '---':
            result.append('\\hrulefill')
            result.append('')  # Add empty line
            i += 1
            continue
            
        # Check for Multi-Agent Reflection section
        if line.strip() == "**Multi-Agent Reflection**":
            # Close any open item list before starting a new section
            if in_list:
                result.append("\\end{itemize}")
                in_list = False

            # Add vertical space before the reflection section
            result.append("\\vspace{1em}")
            # Format as a section with special formatting
            result.append("\\section*{Multi-Agent Reflection}")
            # Add some space after the section title
            result.append("\\vspace{0.5cm}")
            # Add some formatting for the reflection content
            result.append("\\begin{quote}")
            result.append("\\itshape")
            in_multi_agent = True
            i += 1
            continue

        # Special handling for numbered lists in the Multi-Agent Reflection section
        if in_multi_agent and re.match(r'^\d+\.\s+\*\*([^*]+)\*\*:', line):
            # If we're not in a list yet, start an enumerated list
            if not in_enum_list:
                result.append("\\begin{enumerate}")
                in_enum_list = True

            # Format agent role as bold
            match = re.match(r'^\d+\.\s+\*\*([^*]+)\*\*:(.*)', line)
            if match:
                agent_name = match.group(1)
                rest_of_text = match.group(2)
                # Format the list item with proper LaTeX formatting
                result.append(f"\\item \\textbf{{{agent_name}}}: {rest_of_text}")
            else:
                # Just in case regex matching fails
                result.append(f"\\item {line}")

            i += 1
            continue

        # Process headers - first escape any ampersands in the header
        if line.startswith('# '):
            # First replace '&' with '\&' to avoid LaTeX table interpretation
            line = line.replace('&', '\\&')
            # Remove Markdown bold/italic syntax
            text = line[2:].strip().replace('**', '').replace('*', '')
            # Escape other special characters
            text = escape_latex(text)
            # Replace back '\\&' with '\&' (avoid double escaping)
            text = text.replace('\\\\&', '\\&')
            result.append(f"\\section{{{text}}}")
        elif line.startswith('## '):
            line = line.replace('&', '\\&')
            text = line[3:].strip().replace('**', '').replace('*', '')
            text = escape_latex(text)
            text = text.replace('\\\\&', '\\&')
            result.append(f"\\subsection{{{text}}}")
        elif line.startswith('### '):
            line = line.replace('&', '\\&')
            text = line[4:].strip().replace('**', '').replace('*', '')
            text = escape_latex(text)
            text = text.replace('\\\\&', '\\&')
            result.append(f"\\subsubsection{{{text}}}")
        elif line.startswith('#### '):
            line = line.replace('&', '\\&')
            text = line[5:].strip().replace('**', '').replace('*', '')
            text = escape_latex(text)
            text = text.replace('\\\\&', '\\&')
            result.append(f"\\paragraph{{{text}}}")
        # Process numbered sections that are using the **N. Title** format
        elif line.startswith('**') and re.match(r'^\*\*\d+\.', line):
            # First replace '&' with '\&' to avoid LaTeX table interpretation
            line = line.replace('&', '\\&')
            # Extract the number and title from the Markdown section
            match = re.match(r'^\*\*(\d+)\.\s+([^*]+)\*\*', line)
            if match:
                section_num = match.group(1)
                section_title = match.group(2).strip()
                # Escape other special characters
                section_title = escape_latex(section_title)
                # Replace back '\\&' with '\&' (avoid double escaping)
                section_title = section_title.replace('\\\\&', '\\&')
                result.append(f"\\section{{{section_title}}}")
            else:
                # Fallback if the regex doesn't match
                text = line.strip().replace('**', '')
                text = escape_latex(text)
                text = text.replace('\\\\&', '\\&')
                result.append(f"\\section{{{text}}}")
        # Handle list items
        elif line.strip().startswith('* ') or line.strip().startswith('- '):
            # Start list if not already in one
            if not in_list:
                result.append('\\begin{itemize}')
                in_list = True
            
            # Get list item text
            item_text = line.strip()[2:]

            # Pre-escape ampersands before handling formatting
            item_text = item_text.replace('&', '\\&')

            # Replace Markdown formatting with LaTeX commands directly
            # Bold: **text** -> \textbf{text}
            item_text = re.sub(r'\*\*([^*]+)\*\*', r'\\textbf{\1}', item_text)

            # Italic: *text* -> \textit{text}
            item_text = re.sub(r'\*([^*]+)\*', r'\\textit{\1}', item_text)

            # Inline code: `text` -> \texttt{text}
            item_text = re.sub(r'`([^`]+)`', r'\\texttt{\1}', item_text)

            # Special handling for URLs in references
            item_text = re.sub(r'(https?://[^\s]+)', r'\\url{\1}', item_text)

            # Add item to result
            result.append(f"\\item {item_text}")
        else:
            # If we were in a list and now encounter a line that isn't part of a list, close the list
            if in_list:
                # Check if the current line is not empty and is not a start of a new list
                if line.strip() and not line.strip().startswith('* ') and not line.strip().startswith('- '):
                    result.append('\\end{itemize}')
                    in_list = False
            
            # Skip code block markers - will be replaced later
            if line.strip().startswith("CODE_BLOCK_"):
                result.append(line)
                i += 1
                continue
                
            # Skip empty lines in references section that could create empty bullets
            if in_references and line.strip() == "":
                i += 1
                continue
                
            # Process regular text
            # First handle ampersands
            processed_line = line.replace('&', '\\&')
            
            # Handle Markdown formatting directly
            # Bold: **text** -> \textbf{text}
            processed_line = re.sub(r'\*\*([^*]+)\*\*', r'\\textbf{\1}', processed_line)
            
            # Italic: *text* -> \textit{text}
            processed_line = re.sub(r'\*([^*]+)\*', r'\\textit{\1}', processed_line)
            
            # Inline code: `text` -> \texttt{text}
            processed_line = re.sub(r'`([^`]+)`', r'\\texttt{\1}', processed_line)
            
            # Special handling for URLs in references
            if in_references:
                processed_line = re.sub(r'(https?://[^\s]+)', r'\\url{\1}', processed_line)
            else:
                # Links: [text](url) -> \textit{text}
                processed_line = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\\textit{\1}', processed_line)
            
            # Fix any double-escaped ampersands
            processed_line = processed_line.replace('\\\\&', '\\&')
            
            result.append(processed_line)
        
        i += 1
    
    # Close any open list at the end - make sure to close in the correct order
    # First close any open itemize lists
    if in_list:
        result.append('\\end{itemize}')
        in_list = False

    # Next close any open enumerated lists
    if in_enum_list:
        result.append('\\end{enumerate}')
        in_enum_list = False

    # Finally close the quote environment if in multi-agent section
    if in_multi_agent:
        result.append('\\end{quote}')
        in_multi_agent = False

    # Build combined content
    latex_content = '\n'.join(result)

    # Restore code blocks
    for i, code in enumerate(code_blocks):
        marker = f"CODE_BLOCK_{i}"
        verbatim_block = f"\\begin{{verbatim}}\n{code}\n\\end{{verbatim}}"
        latex_content = latex_content.replace(marker, verbatim_block)

    # Fix any remaining double-escaped ampersands
    latex_content = latex_content.replace('\\\\&', '\\&')

    # Combine everything
    full_latex = latex_preamble + latex_title + latex_content + latex_end
    
    return full_latex

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
        
        # Convert to LaTeX
        print(f"Converting Markdown to LaTeX...")
        latex_content = md_to_latex_improved(md_content)
        
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