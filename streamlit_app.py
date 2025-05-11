#!/usr/bin/env python3
"""
Streamlit UI for the Multi-Agent Research Proposal Generation System.
This UI provides a visual interface to monitor and control the research proposal generation process.
"""
import os
import sys
import time
import subprocess
import threading
import queue
import streamlit as st
import pandas as pd
from pathlib import Path
import base64

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import project modules
from src.config.env import config
from src.main import parse_args, ingest_papers

# Set page configuration
st.set_page_config(
    page_title="Research Proposal Gen AI System",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Define agent avatars
AGENT_AVATARS = {
    "system": "⚙️",
    "researcher": "👨‍🔬",
    "domain_expert": "👩‍⚕️",
    "writer_draft": "✍️",
    "critic": "🔍",
    "writer_refine": "✨"
}

# Custom CSS for a polished, modern UI
st.markdown("""
<style>
    /* Main styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    /* Typography */
    h1, h2, h3, h4, h5 {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }

    /* Terminal styling */
    .terminal {
        background-color: #0f111a;
        color: #d8dee9;
        font-family: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace;
        padding: 16px;
        border-radius: 8px;
        border: 1px solid #313547;
        height: 450px;
        overflow-y: auto;
        white-space: pre-wrap;
        font-size: 14px;
        line-height: 1.4;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    .terminal::-webkit-scrollbar {
        width: 8px;
    }

    .terminal::-webkit-scrollbar-track {
        background: #1e1e2e;
        border-radius: 8px;
    }

    .terminal::-webkit-scrollbar-thumb {
        background: #555;
        border-radius: 8px;
    }

    /* Workflow card styling */
    .workflow-container {
        display: flex;
        flex-direction: column;
        gap: 12px;
        max-width: 100%;
        position: relative;
    }

    .workflow-connector {
        position: absolute;
        left: 32px;
        top: 75px;
        bottom: 20px;
        width: 3px;
        background: linear-gradient(to bottom,
            rgba(100, 100, 100, 0.7),
            rgba(100, 100, 100, 0.7) 60%,
            rgba(100, 100, 100, 0) 100%);
        z-index: 0;
    }

    .workflow-step {
        display: flex;
        align-items: stretch;
        background-color: #1a1f36;
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
        z-index: 1;
        transition: all 0.3s ease;
        position: relative;
    }

    .workflow-step:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.2);
    }

    .step-icon {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 64px;
        font-size: 28px;
        flex-shrink: 0;
        position: relative;
    }

    .step-icon-inner {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 50px;
        height: 50px;
        border-radius: 50%;
        background-color: rgba(255, 255, 255, 0.1);
        z-index: 2;
    }

    .step-content {
        flex-grow: 1;
        padding: 14px 16px;
        display: flex;
        flex-direction: column;
    }

    .step-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 6px;
    }

    .step-title {
        font-weight: 600;
        font-size: 16px;
        margin: 0;
        color: #e1e1e6;
        display: flex;
        align-items: center;
    }

    .step-agent {
        font-size: 14px;
        color: #a0a0a8;
    }

    .step-description {
        font-size: 14px;
        color: #cbcbd6;
        margin-top: 4px;
    }

    .step-status {
        font-size: 12px;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        letter-spacing: 0.3px;
        text-transform: uppercase;
    }

    /* Status colors */
    .status-waiting {
        background-color: #2e3752;
        color: #8e96b3;
    }

    .workflow-step.is-waiting {
        border-left: 3px solid #8e96b3;
    }

    .status-running {
        background-color: #00469f;
        color: #77baff;
    }

    .workflow-step.is-running {
        border-left: 3px solid #3498db;
        animation: pulse-border 2s infinite alternate;
    }

    @keyframes pulse-border {
        from { border-left-color: #3498db; }
        to { border-left-color: #77baff; }
    }

    .status-complete {
        background-color: #00603a;
        color: #5cffb1;
    }

    .workflow-step.is-complete {
        border-left: 3px solid #2ecc71;
    }

    .status-skipped {
        background-color: #4a4a60;
        color: #c0c0c6;
    }

    .workflow-step.is-skipped {
        border-left: 3px solid #95a5a6;
        opacity: 0.85;
    }

    .status-error {
        background-color: #7d1321;
        color: #ff8e9a;
    }

    .workflow-step.is-error {
        border-left: 3px solid #e74c3c;
    }

    /* Agent avatar styling */
    .avatar-container {
        position: relative;
        display: inline-block;
    }

    .avatar {
        width: 50px;
        height: 50px;
        border-radius: 50%;
        overflow: hidden;
        background-color: #2c3e50;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
    }

    .status-indicator {
        position: absolute;
        bottom: 0;
        right: 0;
        width: 14px;
        height: 14px;
        border-radius: 50%;
        border: 2px solid #1a1f36;
    }

    .status-indicator.waiting {
        background-color: #7f8c8d;
    }

    .status-indicator.running {
        background-color: #3498db;
        box-shadow: 0 0 0 rgba(52, 152, 219, 0.4);
        animation: pulse 1.5s infinite;
    }

    .status-indicator.complete {
        background-color: #2ecc71;
    }

    .status-indicator.skipped {
        background-color: #95a5a6;
    }

    .status-indicator.error {
        background-color: #e74c3c;
    }

    @keyframes pulse {
        0% {
            box-shadow: 0 0 0 0 rgba(52, 152, 219, 0.4);
        }
        70% {
            box-shadow: 0 0 0 10px rgba(52, 152, 219, 0);
        }
        100% {
            box-shadow: 0 0 0 0 rgba(52, 152, 219, 0);
        }
    }

    /* Progress indicator */
    .progress-indicator {
        position: absolute;
        left: 32px;
        top: 0;
        bottom: 0;
        width: 3px;
        background-color: #3498db;
        z-index: 0;
    }

    /* Animation for running state */
    .running-animation {
        display: inline-block;
        margin-left: 8px;
    }

    .dot {
        display: inline-block;
        width: 4px;
        height: 4px;
        border-radius: 50%;
        margin-right: 3px;
        background-color: currentColor;
        animation: dot-flashing 1s infinite alternate;
    }

    .dot:nth-child(2) {
        animation-delay: 0.2s;
    }

    .dot:nth-child(3) {
        animation-delay: 0.4s;
    }

    @keyframes dot-flashing {
        0% {
            opacity: 0.2;
        }
        100% {
            opacity: 1;
        }
    }

    /* Output file styling */
    .file-container {
        border: 1px solid #2c3e50;
        border-radius: 8px;
        margin-bottom: 16px;
        overflow: hidden;
    }

    .file-header {
        background-color: #1a1f36;
        padding: 10px 16px;
        font-weight: 600;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }

    .file-header svg {
        margin-right: 8px;
    }

    .file-content {
        padding: 12px;
        background-color: #f8f9fa;
        max-height: 400px;
        overflow-y: auto;
    }

    /* Button styling */
    .custom-button {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 8px 16px;
        background-color: #2c3e50;
        color: white;
        border: none;
        border-radius: 4px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s ease;
    }

    .custom-button:hover {
        background-color: #34495e;
        transform: translateY(-1px);
    }

    .custom-button svg {
        margin-right: 8px;
    }

    /* Animated spinner for loading states */
    @keyframes spinner {
        to {transform: rotate(360deg);}
    }

    .spinner-border {
        display: inline-block;
        width: 16px;
        height: 16px;
        vertical-align: text-bottom;
        border: 2px solid currentColor;
        border-right-color: transparent;
        border-radius: 50%;
        animation: spinner 0.75s linear infinite;
        margin-right: 8px;
    }

    /* Toast/notification styling */
    .toast {
        position: fixed;
        bottom: 20px;
        right: 20px;
        padding: 12px 20px;
        background-color: #2ecc71;
        color: white;
        border-radius: 4px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        z-index: 1000;
        animation: slideIn 0.3s ease-out forwards;
    }

    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    /* Footer styling */
    .footer {
        margin-top: 30px;
        padding-top: 10px;
        border-top: 1px solid #ddd;
        text-align: center;
        color: #888;
    }
</style>
""", unsafe_allow_html=True)

# Define the workflow steps and their corresponding agents
WORKFLOW_STEPS = [
    {
        "id": "ingestion",
        "name": "Paper Ingestion",
        "agent": "System",
        "description": "Ingest and index research papers into the vector database",
        "icon": "📚",
        "flag": "skip_ingestion"
    },
    {
        "id": "researcher",
        "name": "Literature Review",
        "agent": "Research Scientist",
        "description": "Conduct a comprehensive literature review on Generative AI in healthcare",
        "icon": "🔬",
        "flag": "skip_researcher"
    },
    {
        "id": "domain_expert",
        "name": "Domain Validation",
        "agent": "Healthcare Domain Expert",
        "description": "Validate research directions from a healthcare perspective",
        "icon": "🏥",
        "flag": "skip_domain_expert"
    },
    {
        "id": "writer_draft",
        "name": "Proposal Drafting",
        "agent": "Proposal Writer",
        "description": "Draft a comprehensive research proposal",
        "icon": "📝",
        "flag": "skip_writer_draft"
    },
    {
        "id": "critic",
        "name": "Proposal Critique",
        "agent": "Research Proposal Critic",
        "description": "Critique the draft proposal and provide feedback",
        "icon": "🔍",
        "flag": "skip_critic"
    },
    {
        "id": "writer_refine",
        "name": "Proposal Refinement",
        "agent": "Proposal Writer",
        "description": "Refine the proposal based on critique",
        "icon": "✨",
        "flag": "skip_writer_refine"
    }
]

# Initialize session state for workflow tracking
if 'current_step' not in st.session_state:
    st.session_state.current_step = None
if 'step_status' not in st.session_state:
    st.session_state.step_status = {step['id']: 'waiting' for step in WORKFLOW_STEPS}
if 'terminal_output' not in st.session_state:
    st.session_state.terminal_output = ""
if 'process_running' not in st.session_state:
    st.session_state.process_running = False
if 'output_queue' not in st.session_state:
    st.session_state.output_queue = queue.Queue()
if 'paper_files' not in st.session_state:
    st.session_state.paper_files = []
if 'cmd_args' not in st.session_state:
    st.session_state.cmd_args = []
if 'error_occurred' not in st.session_state:
    st.session_state.error_occurred = False

def update_terminal(new_text):
    """Update the terminal output in the session state"""
    st.session_state.terminal_output += new_text
    # Keep only the last 5000 characters to prevent too much text
    if len(st.session_state.terminal_output) > 5000:
        st.session_state.terminal_output = "...\n" + st.session_state.terminal_output[-4500:]

def run_process(cmd, step_tracking=None):
    """Run a subprocess and capture its output"""
    st.session_state.process_running = True
    st.session_state.error_occurred = False
    
    if step_tracking:
        update_step_status(step_tracking, 'running')
    
    # Clear terminal for new run
    st.session_state.terminal_output = ""
    
    def process_target():
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Read and process output line by line
            for line in iter(process.stdout.readline, ''):
                st.session_state.output_queue.put(line)
                time.sleep(0.01)  # Small delay to avoid hogging the CPU
            
            # Process exited
            process.stdout.close()
            return_code = process.wait()
            
            if return_code != 0:
                st.session_state.output_queue.put(f"\n❌ Process exited with code {return_code}\n")
                if step_tracking:
                    update_step_status(step_tracking, 'error')
                st.session_state.error_occurred = True
            else:
                if step_tracking:
                    update_step_status(step_tracking, 'complete')
        
        except Exception as e:
            st.session_state.output_queue.put(f"\n❌ Error: {str(e)}\n")
            if step_tracking:
                update_step_status(step_tracking, 'error')
            st.session_state.error_occurred = True
        
        finally:
            st.session_state.process_running = False
    
    # Start process in a separate thread
    thread = threading.Thread(target=process_target)
    thread.daemon = True
    thread.start()

def update_step_status(step_id, status):
    """Update the status of a workflow step"""
    st.session_state.step_status[step_id] = status
    if status == 'running':
        st.session_state.current_step = step_id

def get_flags_for_skipped_steps():
    """Generate command-line flags for skipped steps"""
    flags = []
    for step in WORKFLOW_STEPS:
        if st.session_state.step_status.get(step['id']) == 'skipped':
            flags.append(f"--{step['flag']}")
    return flags

def build_command():
    """Build the command to run the process with appropriate flags"""
    cmd = ["python", "run.py"]
    
    # Add skipped steps flags
    for flag in get_flags_for_skipped_steps():
        cmd.append(flag)
    
    # Add custom paper directory if specified
    if 'papers_dir' in st.session_state and st.session_state.papers_dir:
        cmd.extend(["--papers-dir", st.session_state.papers_dir])
    
    # Add paper files if uploaded
    if st.session_state.paper_files:
        cmd.append("--papers")
        cmd.extend(st.session_state.paper_files)
    
    # Add any custom arguments
    if st.session_state.cmd_args:
        cmd.extend(st.session_state.cmd_args)
    
    return cmd

def check_agent_log_pattern(line, agent_id):
    """Check if a log line indicates an agent's activity"""
    agent_start_patterns = {
        "ingestion": ["Ingest", "paper", "vector"],
        "researcher": ["literature review", "Starting literature", "research sci"],
        "domain_expert": ["domain valid", "Domain Expert", "healthcare domain"],
        "writer_draft": ["Drafting", "proposal draft", "writer"],
        "critic": ["Critiquing", "critique", "critic"],
        "writer_refine": ["Refining", "refinement", "writer"]
    }
    
    patterns = agent_start_patterns.get(agent_id, [])
    return any(pattern.lower() in line.lower() for pattern in patterns)

def process_output_for_agent_detection():
    """Process the output queue to detect active agents and update the UI"""
    while not st.session_state.output_queue.empty():
        line = st.session_state.output_queue.get()
        update_terminal(line)
        
        # Check for agent activity in the output
        for step in WORKFLOW_STEPS:
            if st.session_state.step_status[step['id']] in ['waiting', 'running'] and check_agent_log_pattern(line, step['id']):
                update_step_status(step['id'], 'running')

def load_output_files():
    """Load the output files for display"""
    outputs = {}
    output_dir = Path("outputs")
    
    if output_dir.exists() and output_dir.is_dir():
        for file in output_dir.glob("*.md"):
            try:
                with open(file, 'r') as f:
                    outputs[file.name] = f.read()
            except Exception as e:
                outputs[file.name] = f"Error reading file: {str(e)}"
    
    return outputs

# Create the sidebar for workflow control
with st.sidebar:
    st.title("🧠 Research Proposal Generator")
    st.write("Generate AI-powered research proposals using a multi-agent system.")
    
    # Configuration section
    st.subheader("📋 Configuration")
    
    # Paper ingestion configuration
    st.write("##### Papers Source")
    papers_option = st.radio(
        "Select papers source",
        ["Use default papers", "Upload papers", "Specify papers directory", "Skip paper ingestion"]
    )
    
    if papers_option == "Upload papers":
        uploaded_files = st.file_uploader("Upload research papers", accept_multiple_files=True, type=["pdf", "txt"])
        if uploaded_files:
            # Save uploaded files to a temporary directory
            temp_dir = Path("temp_uploads")
            temp_dir.mkdir(exist_ok=True)
            
            st.session_state.paper_files = []
            for uploaded_file in uploaded_files:
                file_path = str(temp_dir / uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.session_state.paper_files.append(file_path)
            
            st.success(f"✅ {len(uploaded_files)} files uploaded")
    
    elif papers_option == "Specify papers directory":
        st.session_state.papers_dir = st.text_input("Enter path to papers directory", "data/papers")
    
    elif papers_option == "Skip paper ingestion":
        update_step_status('ingestion', 'skipped')
    
    # Allow users to select which steps to skip
    st.write("##### Workflow Steps")
    st.write("Select steps to skip (for debugging or using saved outputs):")
    
    for step in WORKFLOW_STEPS[1:]:  # Skip the ingestion step as it's handled above
        if st.checkbox(f"Skip {step['name']}", key=f"skip_{step['id']}"):
            update_step_status(step['id'], 'skipped')
        else:
            # Only reset to waiting if it was skipped before
            if st.session_state.step_status[step['id']] == 'skipped':
                update_step_status(step['id'], 'waiting')
    
    # Additional command-line arguments
    st.write("##### Advanced Options")
    custom_args = st.text_input("Additional command-line arguments", "")
    if custom_args:
        st.session_state.cmd_args = custom_args.split()
    
    # Start button
    start_disabled = st.session_state.process_running
    if st.button("▶️ Start Process", disabled=start_disabled, key="start_button"):
        cmd = build_command()
        st.write(f"Running: `{' '.join(cmd)}`")
        run_process(cmd)
    
    # Stop button (for future implementation)
    if st.session_state.process_running:
        if st.button("⏹️ Stop Process"):
            st.warning("Stop functionality not yet implemented")
            # Would need a more complex subprocess management to implement stopping

# Main content area with two columns
col1, col2 = st.columns([3, 7])

# Left column: Agent status and workflow visualization
with col1:
    st.header("🔄 Workflow Status")

    # Get active and completed steps to calculate progress
    active_step_index = -1
    completed_steps = 0

    for i, step in enumerate(WORKFLOW_STEPS):
        status = st.session_state.step_status.get(step['id'], 'waiting')
        if status == 'running':
            active_step_index = i
        if status == 'complete':
            completed_steps += 1

    # Calculate progress percentage for visual indicator
    total_steps = len(WORKFLOW_STEPS)
    progress_percent = (completed_steps / total_steps) * 100 if total_steps > 0 else 0

    # Start workflow container with connector
    st.markdown('<div class="workflow-container">', unsafe_allow_html=True)
    st.markdown('<div class="workflow-connector"></div>', unsafe_allow_html=True)

    # Display each step with modern styling
    for i, step in enumerate(WORKFLOW_STEPS):
        status = st.session_state.step_status.get(step['id'], 'waiting')

        # Get appropriate avatar
        avatar = AGENT_AVATARS.get(step['id'], step['icon'])

        # Determine if animation dots should be shown
        running_animation = ""
        if status == 'running':
            running_animation = """
            <span class="running-animation">
                <span class="dot"></span>
                <span class="dot"></span>
                <span class="dot"></span>
            </span>
            """

        # Create workflow step HTML
        workflow_step = f"""
        <div class="workflow-step is-{status}">
            <div class="step-icon">
                <div class="step-icon-inner">
                    {avatar}
                    <div class="status-indicator {status}"></div>
                </div>
            </div>
            <div class="step-content">
                <div class="step-header">
                    <h3 class="step-title">
                        {step['name']}
                        {running_animation}
                    </h3>
                    <span class="step-status status-{status}">{status}</span>
                </div>
                <div class="step-agent">{step['agent']}</div>
                <div class="step-description">{step['description']}</div>
            </div>
        </div>
        """
        st.markdown(workflow_step, unsafe_allow_html=True)

    # End workflow container
    st.markdown('</div>', unsafe_allow_html=True)

    # Display a progress summary
    if active_step_index >= 0:
        active_step = WORKFLOW_STEPS[active_step_index]
        st.info(f"🔄 Current activity: **{active_step['name']}** in progress ({completed_steps}/{total_steps} steps completed)")
    elif completed_steps == total_steps:
        st.success("✅ All steps completed successfully!")
    elif any(st.session_state.step_status.get(step['id']) == 'error' for step in WORKFLOW_STEPS):
        st.error("❌ Process encountered errors. Check the logs for details.")
    else:
        not_started = all(st.session_state.step_status.get(step['id']) in ['waiting', 'skipped'] for step in WORKFLOW_STEPS)
        if not_started:
            st.info("ℹ️ Workflow not started. Configure and press the Start button when ready.")
        else:
            st.warning(f"⏸️ Process paused. Progress: {completed_steps}/{total_steps} steps completed.")

    # Display configuration summary in a collapsible section
    with st.expander("🔧 Configuration Details", expanded=False):
        st.subheader("Command Configuration")
        cmd = build_command()
        st.code(" ".join(cmd), language="bash")

        if papers_option == "Upload papers" and st.session_state.paper_files:
            st.write(f"📄 Uploaded papers: {len(st.session_state.paper_files)} files")
            for file in st.session_state.paper_files:
                st.text(f"  • {os.path.basename(file)}")

    # Add refresh button with a more attractive design
    st.markdown("""
    <div style="display: flex; justify-content: center; margin-top: 20px;">
        <button class="custom-button" id="refresh-btn" onclick="window.location.reload()">
            <span class="spinner-border" style="width: 12px; height: 12px;"></span>
            Refresh Status
        </button>
    </div>
    """, unsafe_allow_html=True)

    # Display output summary if available
    outputs = load_output_files()
    if outputs:
        st.markdown(f"<div style='margin-top: 20px;'><h4>📊 Output Summary</h4>", unsafe_allow_html=True)
        for filename in outputs.keys():
            st.markdown(f"✅ **{filename}** - Generated", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# Right column: Terminal output and results
with col2:
    output_container = st.container()

    with output_container:
        # Create header with status indicator
        if st.session_state.process_running:
            st.markdown("""
            <div style="display: flex; align-items: center; margin-bottom: 16px;">
                <h2 style="margin: 0; margin-right: 10px;">💻 Console Output</h2>
                <div style="background-color: #3498db; color: white; padding: 4px 10px; border-radius: 20px; font-size: 14px; display: flex; align-items: center;">
                    <span class="spinner-border"></span>
                    Running
                </div>
            </div>
            """, unsafe_allow_html=True)
        elif st.session_state.error_occurred:
            st.markdown("""
            <div style="display: flex; align-items: center; margin-bottom: 16px;">
                <h2 style="margin: 0; margin-right: 10px;">💻 Console Output</h2>
                <div style="background-color: #e74c3c; color: white; padding: 4px 10px; border-radius: 20px; font-size: 14px;">Error</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="display: flex; align-items: center; margin-bottom: 16px;">
                <h2 style="margin: 0; margin-right: 10px;">💻 Console Output</h2>
                <div style="background-color: #2ecc71; color: white; padding: 4px 10px; border-radius: 20px; font-size: 14px;">Ready</div>
            </div>
            """, unsafe_allow_html=True)

        # Process any new output in the queue
        if st.session_state.process_running or not st.session_state.output_queue.empty():
            process_output_for_agent_detection()

        # Display terminal-like output with syntax highlighting
        terminal_content = st.session_state.terminal_output

        # Add syntax highlighting for key phrases
        highlighted_content = terminal_content
        # Highlight success messages
        highlighted_content = highlighted_content.replace("✅", "<span style='color: #2ecc71;'>✅</span>")
        highlighted_content = highlighted_content.replace("SUCCESS", "<span style='color: #2ecc71;'>SUCCESS</span>")
        # Highlight warnings
        highlighted_content = highlighted_content.replace("⚠️", "<span style='color: #f39c12;'>⚠️</span>")
        highlighted_content = highlighted_content.replace("WARNING", "<span style='color: #f39c12;'>WARNING</span>")
        # Highlight errors
        highlighted_content = highlighted_content.replace("❌", "<span style='color: #e74c3c;'>❌</span>")
        highlighted_content = highlighted_content.replace("ERROR", "<span style='color: #e74c3c;'>ERROR</span>")
        # Highlight agent names
        for step in WORKFLOW_STEPS:
            agent_name = step['agent']
            highlighted_content = highlighted_content.replace(
                agent_name,
                f"<span style='color: #3498db; font-weight: bold;'>{agent_name}</span>"
            )

        st.markdown(f'<div class="terminal">{highlighted_content}</div>', unsafe_allow_html=True)

        # Display a visual loader and status message if the process is running
        if st.session_state.process_running:
            col1, col2 = st.columns([1, 5])
            with col1:
                st.markdown("""
                <div style="display: flex; justify-content: center; align-items: center; height: 60px;">
                    <div class="spinner-border" style="width: 24px; height: 24px; color: #3498db;"></div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.info("Process is running. The output will update automatically...")
        elif st.session_state.error_occurred:
            st.error("❌ An error occurred during execution. Check the output above for details.")

    # Display outputs section if any are available
    outputs = load_output_files()
    if outputs:
        st.markdown("""
        <div style="margin-top: 32px; margin-bottom: 16px;">
            <h2>📑 Generated Documents</h2>
        </div>
        """, unsafe_allow_html=True)

        # Create tabs for each output file with more attractive styling
        output_tabs = st.tabs([f"{filename}" for filename in outputs.keys()])

        for i, (filename, content) in enumerate(outputs.items()):
            with output_tabs[i]:
                # Create a custom file viewer
                st.markdown(f"""
                <div class="file-container">
                    <div class="file-header">
                        <div>
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M14 2H6C4.9 2 4.01 2.9 4.01 4L4 20C4 21.1 4.89 22 5.99 22H18C19.1 22 20 21.1 20 20V8L14 2ZM16 18H8V16H16V18ZM16 14H8V12H16V14ZM13 9V3.5L18.5 9H13Z" fill="#E1E1E6"/>
                            </svg>
                            {filename}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Display content in a stylized text area
                content_with_line_numbers = content
                st.text_area("", content_with_line_numbers, height=350,
                             key=f"output_{i}", label_visibility="collapsed")

                # Add actionable buttons for the file
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"📷 View as PDF", key=f"view_{filename}",
                              use_container_width=True):
                        # Launch the PDF conversion script
                        pdf_cmd = ["./convert_to_pdf.sh", f"outputs/{filename}"]
                        try:
                            subprocess.run(pdf_cmd, check=True)
                            st.success(f"Converting '{filename}' to PDF...")
                            # Get the PDF file path
                            pdf_path = f"outputs/{os.path.splitext(filename)[0]}.pdf"
                            if os.path.exists(pdf_path):
                                # Use HTML to display the PDF
                                pdf_display = f'<iframe src="file://{pdf_path}" width="100%" height="500px"></iframe>'
                                st.markdown(pdf_display, unsafe_allow_html=True)
                            else:
                                st.error("PDF file not created. Check for errors in the conversion process.")
                        except subprocess.CalledProcessError:
                            st.error("❌ Error creating PDF. Make sure you have LaTeX installed.")
                        except FileNotFoundError:
                            st.error("❌ convert_to_pdf.sh script not found or not executable.")

                with col2:
                    if st.button(f"⬇️ Download as PDF", key=f"pdf_{filename}",
                              use_container_width=True):
                        # Launch the PDF conversion script
                        pdf_cmd = ["./convert_to_pdf.sh", f"outputs/{filename}"]
                        try:
                            subprocess.run(pdf_cmd, check=True)
                            # Get the path to the PDF file
                            pdf_path = f"outputs/{os.path.splitext(filename)[0]}.pdf"
                            if os.path.exists(pdf_path):
                                # Provide download link using HTML
                                with open(pdf_path, "rb") as f:
                                    pdf_bytes = f.read()

                                b64_pdf = base64.b64encode(pdf_bytes).decode()
                                href = f'<a href="data:application/pdf;base64,{b64_pdf}" download="{os.path.basename(pdf_path)}">Click to download PDF</a>'
                                st.markdown(href, unsafe_allow_html=True)
                                st.success(f"✅ PDF created: {pdf_path}")
                            else:
                                st.error("PDF file not created. Check for errors in the conversion process.")
                        except subprocess.CalledProcessError:
                            st.error("❌ Error creating PDF. Make sure you have LaTeX installed.")
                        except FileNotFoundError:
                            st.error("❌ convert_to_pdf.sh script not found or not executable.")

# Update the UI periodically
if st.session_state.process_running:
    st.rerun()

if __name__ == "__main__":
    # This prevents execution during module import
    pass