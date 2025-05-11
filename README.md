# Multi-Agent Application for Research Proposal Generation

A multi-agent application using Crew AI to generate research proposals in the domain of Generative AI in healthcare.

## Project Overview

This project uses a crew of specialized AI agents to collaboratively generate a research proposal. Each agent plays a specific role in the process:

1. **Research Scientist** - Conducts literature reviews and identifies research gaps
2. **Healthcare Domain Expert** - Validates research directions from a clinical perspective, grounding insights in academic literature through RAG
3. **Research Proposal Writer** - Drafts and refines the research proposal
4. **Research Proposal Critic** - Critiques the proposal and identifies areas for improvement

The system incorporates Retrieval-Augmented Generation (RAG) to ground the domain expert's knowledge in actual academic literature, allowing for evidence-based validation with proper citations.

## Setup

### Prerequisites

- Python 3.8+
- Google API key for Gemini access

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/multi-agent-app.git
   cd multi-agent-app
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   - Create a `.env` file based on the provided template
   - Add your Google API key and adjust other parameters as needed

## Usage

Run the main application:

```
python run.py
```

By default, the system will:
1. Use a file-based Chroma vector database stored in `data/chroma_db`
2. Look for papers in the `data/papers` directory
3. If the papers directory is empty, download predefined academic papers on generative AI in healthcare

### Command-line options

You can customize the behavior with these options:

```
python run.py --papers-dir /path/to/papers/directory
```
Uses all PDF and text files in the specified directory for RAG.

```
python run.py --papers https://arxiv.org/pdf/paper1.pdf /path/to/local/paper.pdf
```
Adds specific papers from URLs or local file paths.

```
python run.py --papers-dir /path/to/papers/directory --papers https://arxiv.org/pdf/additional.pdf
```
Uses all papers in the directory plus the additional specified papers.

```
python run.py --skip-ingestion
```
Skips the paper ingestion process and uses the existing Chroma DB. This is useful after you've already ingested papers and don't want to repeat the process.

### Workflow

The workflow will:
1. Ingest academic papers into the persistent vector database
2. Start the literature review process
3. Validate research directions using RAG for grounding in literature
4. Draft a research proposal
5. Critique the proposal
6. Refine the final proposal

The final research proposal and intermediate outputs will be saved in the `outputs` directory.

## Step-by-Step Instructions

### Step 1: Initialize Chroma and Set Up the Environment

1. Ensure you have Python 3.8+ installed
2. Clone the repository and navigate to it
3. Install dependencies using uv (faster, more reliable package manager):
   ```
   # Install uv if you don't have it
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Create virtual environment and install dependencies
   uv venv
   uv pip install -r requirements.txt

   # Activate the virtual environment
   source .venv/bin/activate  # On Unix/MacOS
   # OR
   # .venv\Scripts\activate  # On Windows
   ```

   Alternatively, you can use pip:
   ```
   pip install -r requirements.txt
   ```
4. Set up Google Cloud and Vertex AI:
   - Create or use an existing Google Cloud project
   - Make sure Vertex AI API is enabled for your project
   - Set up authentication by creating a service account key or using gcloud auth
5. Update the `.env` file with your Google Cloud details:
   ```
   GOOGLE_PROJECT_ID=your-google-project-id
   GOOGLE_REGION=us-central1
   MODEL_NAME=gemini-2.5-pro-preview-05-06
   EMBEDDING_MODEL=text-embedding-004
   TEMPERATURE=0.7
   MAX_TOKENS=2048
   ```
6. Authenticate with Google Cloud:
   ```
   gcloud auth application-default login
   ```
   or set `GOOGLE_APPLICATION_CREDENTIALS` environment variable pointing to a service account key file.

### Step 2: Prepare Research Papers

Option A: Use default papers
- Simply run the application and it will automatically download default papers on AI in healthcare

Option B: Add your own papers
- Place PDF or text files in the `data/papers` directory
- Alternatively, specify a different directory of papers with the `--papers-dir` option

### Step 3: Run the Application

Basic execution:
```
python run.py
```

With custom paper directory:
```
python run.py --papers-dir /path/to/your/papers
```

With additional specific papers:
```
python run.py --papers https://arxiv.org/pdf/your-paper.pdf
```

### Step 4: Monitoring the Process

The application will run through these stages:
1. Initialize the Chroma vector database in `data/chroma_db`
2. Process and index all papers in the papers directory
3. Run the literature review with the researcher agent
4. Validate research directions with the domain expert (using RAG)
5. Draft a research proposal with the writer agent
6. Critique the proposal with the critic agent
7. Refine the final proposal with the writer agent

### Step 5: Review the Results

All outputs are saved in the `outputs` directory:
- `literature_review.md` - Initial literature review
- `domain_validation.md` - Domain expert validation with citations
- `proposal_draft.md` - First draft of the proposal
- `proposal_critique.md` - Critique of the draft
- `final_proposal.md` - The refined research proposal

### Note on Persistent Chroma DB

The Chroma database persists between runs. This means:
- You only need to process papers once
- Subsequent runs will be faster as the database already exists
- To reindex papers, delete the `data/chroma_db` directory

## Configuration

The agents and tasks are defined in YAML configuration files:

- `src/config/agents.yaml` - Defines the role, goal, and backstory for each agent
- `src/config/tasks.yaml` - Defines the tasks, their descriptions, and which agent handles each task

You can modify these files to customize the behavior of the agents and tasks without changing the code.

## Project Structure

```
multi-agent-app/
├── .env                   # Environment variables
├── README.md              # Project documentation
├── requirements.txt       # Project dependencies
├── outputs/               # Generated output files
├── src/                   # Source code
│   ├── __init__.py
│   ├── agents/            # Agent definitions
│   │   ├── __init__.py
│   │   ├── agent_factory.py # Agent factory from YAML
│   │   └── task_factory.py  # Task factory from YAML
│   ├── config/            # Configuration
│   │   ├── __init__.py
│   │   ├── agents.yaml    # Agent definitions
│   │   ├── tasks.yaml     # Task definitions
│   │   └── env.py         # Environment config
│   ├── data/              # Data handling
│   │   └── __init__.py
│   ├── main.py            # Main application
│   ├── services/          # Services
│   │   └── __init__.py
│   └── utils/             # Utilities
│       ├── __init__.py
│       ├── gemini_llm.py  # LLM integration
│       └── yaml_loader.py # YAML configuration loader
└── tests/                 # Test directory
```