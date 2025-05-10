"""Main application file for the research proposal crew."""
import os
import argparse
from typing import List, Optional
from crewai import Crew
from src.config.env import config
from src.agents.agent_factory import AgentFactory
from src.agents.task_factory import TaskFactory
from src.utils.vector_store import VectorStore
from src.utils.document_ingestion import DocumentIngestion

def save_output(output: str, filename: str):
    """Save output to a file.
    
    Args:
        output: The output to save
        filename: The filename to save to
    """
    output_dir = "outputs"
    os.makedirs(output_dir, exist_ok=True)
    
    with open(os.path.join(output_dir, filename), "w") as f:
        f.write(output)
    
    print(f"Output saved to outputs/{filename}")

def ingest_papers(paper_sources: Optional[List[str]] = None, papers_dir: str = "data/papers"):
    """Ingest papers into the vector store.
    
    Args:
        paper_sources: Optional list of paper URLs, file paths, or directories
        papers_dir: Directory where papers are stored
    
    Returns:
        Initialized vector store
    """
    # Create document ingestion
    ingestion = DocumentIngestion(papers_directory=papers_dir)
    
    # Create vector store with persistent storage
    vector_store = VectorStore(persist_directory="data/chroma_db")
    
    # Download default papers if directory is empty and no sources provided
    if len(os.listdir(papers_dir)) == 0 and not paper_sources:
        print("📚 Downloading default papers...")
        default_papers = [
            "https://arxiv.org/pdf/2303.04365.pdf",  # GenAI in Healthcare
            "https://arxiv.org/pdf/2310.19974.pdf",  # LLMs in Healthcare
            "https://arxiv.org/pdf/2312.05209.pdf"   # Survey of GenAI in Medicine
        ]
        ingestion.batch_import_papers(default_papers)
    
    # Import additional papers if provided
    if paper_sources:
        print(f"🔍 Importing {len(paper_sources)} additional sources...")
        ingestion.batch_import_papers(paper_sources)
    
    # Add all papers from the papers directory to the vector store
    print(f"🔍 Indexing papers from {papers_dir}...")
    vector_store.add_documents_from_directory(papers_dir)
    
    print("✅ Paper ingestion complete")
    
    return vector_store

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Generate research proposals using CrewAI')
    parser.add_argument('--papers', nargs='+', help='Paper URLs or file paths to ingest')
    parser.add_argument('--papers-dir', default='data/papers', help='Directory containing research papers')
    return parser.parse_args()

def main():
    """Run the research proposal generation crew."""
    # Parse arguments
    args = parse_args()
    
    # Validate environment configuration
    config.validate()
    
    # Ingest papers
    papers_dir = args.papers_dir if hasattr(args, 'papers_dir') else 'data/papers'
    paper_sources = args.papers if hasattr(args, 'papers') else None
    vector_store = ingest_papers(paper_sources, papers_dir)
    
    # Initialize factories with the vector store
    agent_factory = AgentFactory(vector_store)
    task_factory = TaskFactory(agent_factory)
    
    print("🤖 Initializing research crew...")
    
    # Create initial task (literature review)
    literature_review_task = task_factory.create_task("literature_review")
    
    # Execute first task and get result
    print("\n🔬 Starting literature review...")
    crew = Crew(
        agents=[agent_factory.create_agent("researcher")],
        tasks=[literature_review_task],
        verbose=2
    )
    lit_review_result = crew.kickoff()
    save_output(lit_review_result, "literature_review.md")
    
    # Domain validation with context from literature review
    domain_validation_task = task_factory.create_task(
        "domain_validation", 
        context=lit_review_result
    )
    
    print("\n🏥 Validating research directions with domain expert...")
    crew = Crew(
        agents=[agent_factory.create_agent("domain_expert")],
        tasks=[domain_validation_task],
        verbose=2
    )
    validation_result = crew.kickoff()
    save_output(validation_result, "domain_validation.md")
    
    # Combined context for proposal drafting
    combined_context = f"Literature Review:\n{lit_review_result}\n\nDomain Validation:\n{validation_result}"
    
    # Draft proposal
    proposal_drafting_task = task_factory.create_task(
        "proposal_drafting",
        context=combined_context
    )
    
    print("\n📝 Drafting research proposal...")
    crew = Crew(
        agents=[agent_factory.create_agent("proposal_writer")],
        tasks=[proposal_drafting_task],
        verbose=2
    )
    proposal_draft = crew.kickoff()
    save_output(proposal_draft, "proposal_draft.md")
    
    # Updated context for critique
    updated_context = f"{combined_context}\n\nProposal Draft:\n{proposal_draft}"
    
    # Critique proposal
    critique_task = task_factory.create_task(
        "proposal_critique",
        context=updated_context
    )
    
    print("\n🔍 Critiquing research proposal...")
    crew = Crew(
        agents=[agent_factory.create_agent("critic")],
        tasks=[critique_task],
        verbose=2
    )
    critique_result = crew.kickoff()
    save_output(critique_result, "proposal_critique.md")
    
    # Final context for refinement
    final_context = f"{updated_context}\n\nCritique:\n{critique_result}"
    
    # Refine proposal
    refinement_task = task_factory.create_task(
        "proposal_refinement",
        context=final_context
    )
    
    print("\n✨ Refining final research proposal...")
    crew = Crew(
        agents=[agent_factory.create_agent("proposal_writer")],
        tasks=[refinement_task],
        verbose=2
    )
    final_proposal = crew.kickoff()
    save_output(final_proposal, "final_proposal.md")
    
    print("\n✅ Research proposal generation complete!")
    print("Final proposal saved to outputs/final_proposal.md")

if __name__ == "__main__":
    main()