#!/usr/bin/env python3
"""
Wrapper script to run the multi-agent application.

Usage:
    python run.py [options]

Options:
    --papers        List of paper URLs or file paths to ingest
    --papers-dir    Directory containing research papers (default: data/papers)
"""
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Run the main application
from src.main import main

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nApplication terminated by user")
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)