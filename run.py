#!/usr/bin/env python3
"""
Wrapper script to run the multi-agent application.

Usage:
    python run.py [options]

Options:
    # Paper ingestion options
    --papers          List of paper URLs or file paths to ingest
    --papers-dir      Directory containing research papers (default: data/papers)
    --skip-ingestion  Skip paper ingestion and use existing Chroma DB

    # Agent execution options - for troubleshooting individual stages
    --skip-researcher        Skip the Research Scientist stage
    --skip-domain-expert     Skip the Domain Expert stage
    --skip-writer-draft      Skip the Proposal Writer draft stage
    --skip-critic            Skip the Critic stage
    --skip-writer-refine     Skip the Proposal Writer refinement stage

    # Input file options - for using existing outputs when skipping stages
    --lit-review-file          Path to existing literature review file
    --domain-validation-file   Path to existing domain validation file
    --proposal-draft-file      Path to existing proposal draft file
    --proposal-critique-file   Path to existing proposal critique file
"""
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Run the main application
from src.main import main

import warnings

# Suppress all DeprecationWarnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

# Suppress specific Pydantic deprecation warnings as UserWarning
warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    message=r".*PydanticDeprecatedSince20.*"
)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nApplication terminated by user")
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)