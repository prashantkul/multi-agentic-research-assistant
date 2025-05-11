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
    "ingestion": "📚",
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
        padding-top: 1rem;
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
    
    /* Process sequence flow */
    .sequence-flow {
        display: flex;
        flex-direction: row;
        align-items: center;
        gap: 10px;
        width: 100%;
        overflow-x: auto;
        padding: 16px 0;
        margin-bottom: 24px;
    }
    
    .sequence-step {
        display: flex;
        flex-direction: column;
        align-items: center;
        min-width: 100px;
        position: relative;
    }
    
    .step-connector {
        height: 2px;
        background-color: #ddd;
        flex-grow: 1;
        margin: 0 -5px;
        position: relative;
        z-index: 1;
    }
    
    .step-connector.complete {
        background-color: #2ecc71;
    }
    
    .step-connector.active {
        background: linear-gradient(90deg, #2ecc71 0%, #3498db 100%);
    }
    
    .step-node {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background-color: #ecf0f1;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 8px;
        position: relative;
        z-index: 2;
        border: 2px solid #ddd;
    }
    
    .step-node.waiting {
        background-color: #ecf0f1;
        border-color: #bdc3c7;
        color: #7f8c8d;
    }
    
    .step-node.running {
        background-color: #3498db;
        border-color: #2980b9;
        color: white;
        animation: pulse-node 1.5s infinite alternate;
    }
    
    .step-node.complete {
        background-color: #2ecc71;
        border-color: #27ae60;
        color: white;
    }
    
    .step-node.skipped {
        background-color: #95a5a6;
        border-color: #7f8c8d;
        color: white;
        opacity: 0.7;
    }
    
    .step-node.error {
        background-color: #e74c3c;
        border-color: #c0392b;
        color: white;
    }
    
    @keyframes pulse-node {
        from { box-shadow: 0 0 5px rgba(52, 152, 219, 0.5); }
        to { box-shadow: 0 0 15px rgba(52, 152, 219, 0.8); }
    }
    
    .step-label {
        font-size: 12px;
        font-weight: 500;
        text-align: center;
        color: #7f8c8d;
        max-width: 120px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    
    .step-label.active {
        color: #2c3e50;
        font-weight: 600;
    }
    
    .checkmark {
        display: inline-block;
        width: 20px;
        height: 20px;
        background-color: transparent;
        border-radius: 50%;
        position: relative;
    }
    
    .checkmark::after {
        content: '';
        display: block;
        width: 6px;
        height: 12px;
        border: solid white;
        border-width: 0 2px 2px 0;
        transform: rotate(45deg);
        position: absolute;
        top: 2px;
        left: 7px;
    }
    
    /* Status badge styling */
    .status-badge {
        display: inline-flex;
        align-items: center;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 14px;
        font-weight: 600;
        margin-left: 12px;
    }
    
    .status-badge.running {
        background-color: rgba(52, 152, 219, 0.15);
        color: #3498db;
        border: 1px solid rgba(52, 152, 219, 0.3);
    }
    
    .status-badge.complete {
        background-color: rgba(46, 204, 113, 0.15);
        color: #2ecc71;
        border: 1px solid rgba(46, 204, 113, 0.3);
    }
    
    .status-badge.error {
        background-color: rgba(231, 76, 60, 0.15);
        color: #e74c3c;
        border: 1px solid rgba(231, 76, 60, 0.3);
    }
    
    .status-badge.waiting {
        background-color: rgba(189, 195, 199, 0.15);
        color: #7f8c8d;
        border: 1px solid rgba(189, 195, 199, 0.3);
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
    
    /* Action panel */
    .action-panel {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 24px;
        border: 1px solid #ddd;
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

def convert_to_pdf(md_file_path):
    """Separate function to handle PDF conversion"""
    try:
        # Call the conversion script with proper parameters
        pdf_cmd = ["./convert_to_pdf.sh", md_file_path]
        result = subprocess.run(pdf_cmd, capture_output=True, text=True, check=True)
        
        # Get the PDF file path from markdown path
        pdf_path = os.path.splitext(md_file_path)[0] + ".pdf"
        
        return True, pdf_path, result.stdout
    except subprocess.CalledProcessError as e:
        return False, None, f"❌ Error: {e.stderr}"
    except FileNotFoundError:
        return False, None, "❌ convert_to_pdf.sh script not found or not executable."
    except Exception as e:
        return False, None, f"❌ Error: {str(e)}"

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

# ----- Main Content Area -----
st.title("Research Proposal Generation System")

# Horizontal Sequence Flow
# Calculate progress and active step
active_step_index = -1
completed_steps = 0
for i, step in enumerate(WORKFLOW_STEPS):
    status = st.session_state.step_status.get(step['id'], 'waiting')
    if status == 'running':
        active_step_index = i
    if status == 'complete':
        completed_steps += 1

# Build the sequence flow HTML
sequence_html = '<div class="sequence-flow">'

for i, step in enumerate(WORKFLOW_STEPS):
    status = st.session_state.step_status.get(step['id'], 'waiting')
    
    # Add connector between steps (except before the first step)
    if i > 0:
        connector_class = ""
        if completed_steps > i-1:
            connector_class = " complete"
        elif active_step_index == i:
            connector_class = " active"
        sequence_html += f'<div class="step-connector{connector_class}"></div>'
    
    # Get appropriate step icon/content based on status
    step_content = step['icon']
    if status == 'complete':
        step_content = '<span class="checkmark"></span>'
    
    # Determine if step label should be active
    label_class = ""
    if status == 'running':
        label_class = " active"
    
    # Add the step node
    sequence_html += f'''
    <div class="sequence-step">
        <div class="step-node {status}">{step_content}</div>
        <div class="step-label{label_class}">{step['name']}</div>
    </div>
    '''

sequence_html += '</div>'

# Display the sequence flow
st.markdown(sequence_html, unsafe_allow_html=True)

# Display active process information if relevant
if active_step_index >= 0:
    active_step = WORKFLOW_STEPS[active_step_index]
    st.markdown(f"""
    <div style="margin-bottom: 20px; text-align: center;">
        <span style="font-size: 16px; color: #2c3e50;">
            <b>{active_step['agent']}</b> is currently working on <b>{active_step['name']}</b>
            <span class="status-badge running">
                <span class="spinner-border" style="width: 10px; height: 10px;"></span>
                Running
            </span>
        </span>
    </div>
    """, unsafe_allow_html=True)
elif completed_steps == len(WORKFLOW_STEPS):
    st.markdown(f"""
    <div style="margin-bottom: 20px; text-align: center; color: #27ae60;">
        <span style="font-size: 16px;">
            <b>✅ All steps completed successfully!</b>
        </span>
    </div>
    """, unsafe_allow_html=True)
elif any(st.session_state.step_status.get(step['id']) == 'error' for step in WORKFLOW_STEPS):
    error_step = next((step for step in WORKFLOW_STEPS if st.session_state.step_status.get(step['id']) == 'error'), None)
    if error_step:
        st.markdown(f"""
        <div style="margin-bottom: 20px; text-align: center; color: #e74c3c;">
            <span style="font-size: 16px;">
                <b>❌ Error in {error_step['name']}</b> - Check the logs for details
            </span>
        </div>
        """, unsafe_allow_html=True)

# Action panel
with st.expander("📋 Configuration Details", expanded=False):
    st.subheader("Command Configuration")
    cmd = build_command()
    st.code(" ".join(cmd), language="bash")
    
    if papers_option == "Upload papers" and st.session_state.paper_files:
        st.write(f"📄 Uploaded papers: {len(st.session_state.paper_files)} files")
        for file in st.session_state.paper_files:
            st.text(f"  • {os.path.basename(file)}")
    
    # Display skipped steps if any
    skipped_steps = [step for step in WORKFLOW_STEPS if st.session_state.step_status.get(step['id']) == 'skipped']
    if skipped_steps:
        st.write("⏭️ Skipped Steps:")
        for step in skipped_steps:
            st.text(f"  • {step['name']}")

# Terminal output section
st.subheader("💻 Console Output")

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
    st.info("⏳ Process is running. The output will update automatically...")
elif st.session_state.error_occurred:
    st.error("❌ An error occurred during execution. Check the output above for details.")

# Generated outputs section
outputs = load_output_files()
if outputs:
    st.subheader("📑 Generated Documents")
    
    # Create tabs for each output file with more attractive styling
    output_tabs = st.tabs([f"{filename}" for filename in outputs.keys()])
    
    for i, (filename, content) in enumerate(outputs.items()):
        with output_tabs[i]:
            # Display content in a stylized text area
            st.text_area("", content, height=350, 
                         key=f"output_{i}", label_visibility="collapsed")
            
            # Add actionable buttons for the file
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"📷 View as PDF", key=f"view_{filename}", 
                          use_container_width=True):
                    # Use the separate conversion function
                    md_file_path = f"outputs/{filename}"
                    success, pdf_path, message = convert_to_pdf(md_file_path)
                    
                    if success and pdf_path and os.path.exists(pdf_path):
                        st.success(f"✅ PDF created successfully")
                        # Use HTML to display the PDF
                        pdf_display = f'<iframe src="file://{pdf_path}" width="100%" height="500px"></iframe>'
                        st.markdown(pdf_display, unsafe_allow_html=True)
                    else:
                        st.error(f"Failed to create PDF: {message}")
            
            with col2:
                if st.button(f"⬇️ Download as PDF", key=f"pdf_{filename}", 
                          use_container_width=True):
                    # Use the separate conversion function
                    md_file_path = f"outputs/{filename}"
                    success, pdf_path, message = convert_to_pdf(md_file_path)
                    
                    if success and pdf_path and os.path.exists(pdf_path):
                        # Provide download link using HTML
                        with open(pdf_path, "rb") as f:
                            pdf_bytes = f.read()
                        
                        b64_pdf = base64.b64encode(pdf_bytes).decode()
                        href = f'<a href="data:application/pdf;base64,{b64_pdf}" download="{os.path.basename(pdf_path)}">Click to download PDF</a>'
                        st.markdown(href, unsafe_allow_html=True)
                        st.success(f"✅ PDF created: {pdf_path}")
                    else:
                        st.error(f"Failed to create PDF: {message}")

# Add a footer
st.markdown("""
<div class="footer">
    <p>Multi-Agent Research Proposal Generator | Powered by CrewAI and Streamlit</p>
</div>
""", unsafe_allow_html=True)

# Update the UI periodically
if st.session_state.process_running:
    st.rerun()

if __name__ == "__main__":
    # This prevents execution during module import
    pass