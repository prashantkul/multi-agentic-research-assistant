#!/bin/bash
# Script to run the Streamlit UI for the multi-agent app

# Create temp uploads directory if it doesn't exist
mkdir -p temp_uploads

echo "Starting Streamlit UI..."
streamlit run streamlit_app_updated.py