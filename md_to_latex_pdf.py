#!/usr/bin/env python3
"""
Convert Markdown files to LaTeX and then to PDF.
This script handles the conversion of all Markdown files in the outputs directory.
"""
import os
import re
import subprocess
import sys
from pathlib import Path

def clean_temp_files(base_path):
    """Remove LaTeX temporary files"""
    extensions = ['.aux', '.log', '.out', '.toc', '.lof', '.lot', '.fls', '.fdb_latexmk']
    for ext in extensions:
        try:
            os.remove(f"{base_path}{ext}")
        except FileNotFoundError:
            pass

def md_to_latex(md_content):
    """Convert Markdown content to LaTeX format"""
    # Basic LaTeX document structure
    latex_template = r"""
\documentclass[12pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\usepackage{microtype}
\usepackage{graphicx}
\usepackage{hyperref}
\usepackage{booktabs}
\usepackage{listings}
\usepackage{xcolor}
\usepackage{amsmath,amssymb}
\usepackage[margin=1in]{geometry}
\usepackage{titlesec}
\usepackage{enumitem}
\usepackage{fancyhdr}

\definecolor{linkcolor}{RGB}{0,102,204}
\hypersetup{colorlinks=true,linkcolor=linkcolor,citecolor=linkcolor,urlcolor=linkcolor}

\titleformat{\section}{\normalfont\Large\bfseries}{\thesection}{1em}{}
\titleformat{\subsection}{\normalfont\large\bfseries}{\thesubsection}{1em}{}
\titleformat{\subsubsection}{\normalfont\normalsize\bfseries}{\thesubsubsection}{1em}{}

\lstset{
    basicstyle=\ttfamily\footnotesize,
    breaklines=true,
    backgroundcolor=\color{gray!10},
    frame=single,
    frameround=tttt,
    framesep=5pt,
    commentstyle=\color{green!50!black},
    keywordstyle=\color{blue},
    stringstyle=\color{red},
}

\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\leftmark}
\fancyhead[R]{\thepage}
\renewcommand{\headrulewidth}{0.4pt}

\begin{document}
"""

    latex_end = r"""
\end{document}
"""

    # Process the title/header
    first_line = md_content.strip().split('\n', 1)[0]
    if first_line.startswith('# '):
        title = first_line[2:].strip()
        md_content = md_content.replace(first_line, '', 1)  # Remove the title from content
        latex_title = r"\title{" + title + r"}\date{\today}\author{}\maketitle"
        latex_template += latex_title
    
    # Process markdown content
    content = md_content.strip()
    
    # Convert headers
    content = re.sub(r'^# (.+)$', r'\\section{\1}', content, flags=re.MULTILINE)
    content = re.sub(r'^## (.+)$', r'\\subsection{\1}', content, flags=re.MULTILINE)
    content = re.sub(r'^### (.+)$', r'\\subsubsection{\1}', content, flags=re.MULTILINE)
    content = re.sub(r'^#### (.+)$', r'\\paragraph{\1}', content, flags=re.MULTILINE)
    
    # Convert bullet points
    content = re.sub(r'^[ \t]*\* (.+)$', r'\\begin{itemize}\n\\item \1', content, flags=re.MULTILINE)
    content = content + '\n\\end{itemize}\n'  # Close any open itemize environments
    
    # Clean up excess itemize environments
    content = content.replace('\\begin{itemize}\n\\begin{itemize}', '\\begin{itemize}')
    content = content.replace('\\end{itemize}\n\\end{itemize}', '\\end{itemize}')
    
    # Convert bold and italic
    content = re.sub(r'\*\*(.+?)\*\*', r'\\textbf{\1}', content)
    content = re.sub(r'\*(.+?)\*', r'\\textit{\1}', content)
    
    # Convert code blocks
    content = re.sub(r'```(.+?)```', r'\\begin{lstlisting}\n\1\n\\end{lstlisting}', content, flags=re.DOTALL)
    
    # Combine everything
    latex_content = latex_template + content + latex_end
    
    return latex_content

def process_file(md_file_path):
    """Process a single Markdown file to LaTeX and PDF"""
    print(f"Processing {md_file_path}...")
    
    # Read the markdown content
    with open(md_file_path, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Convert to LaTeX
    latex_content = md_to_latex(md_content)
    
    # Create a LaTeX file
    base_name = os.path.splitext(md_file_path)[0]
    tex_file_path = f"{base_name}.tex"
    
    with open(tex_file_path, 'w', encoding='utf-8') as f:
        f.write(latex_content)
    
    # Compile to PDF using pdflatex
    print(f"Compiling {tex_file_path} to PDF...")
    try:
        subprocess.run(['pdflatex', tex_file_path], check=True, stdout=subprocess.PIPE)
        # Run twice for cross-references and table of contents
        subprocess.run(['pdflatex', tex_file_path], check=True, stdout=subprocess.PIPE)
        print(f"PDF created: {base_name}.pdf")
    except subprocess.CalledProcessError as e:
        print(f"Error compiling LaTeX file: {e}")
        return False
    except FileNotFoundError:
        print("Error: pdflatex not found. Please install TeX Live or another LaTeX distribution.")
        return False
    
    # Clean up temp files
    clean_temp_files(base_name)
    
    return True

def main():
    """Main function to process all Markdown files in the outputs directory"""
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

if __name__ == "__main__":
    main()