"""Main application file for the research proposal crew."""
import os
import argparse
from typing import List, Optional
from crewai import Crew, Task
from src.config.env import config
from src.agents.agent_factory import AgentFactory
from src.agents.task_factory import TaskFactory
from src.utils.vector_store import VectorStore
from src.utils.document_ingestion import DocumentIngestion

def save_output(output, filename: str):
    """Save output to a file.

    Args:
        output: The output to save (string or CrewOutput object)
        filename: The filename to save to
    """
    output_dir = "outputs"
    os.makedirs(output_dir, exist_ok=True)

    # Handle None values
    if output is None:
        output_text = "No output was generated. The agent may have encountered an error."
        print(f"Warning: Received None output when saving to {filename}")
    # Convert output to string if it's not already
    elif hasattr(output, 'raw'):  # CrewOutput has a 'raw' attribute with the text
        output_text = output.raw if output.raw is not None else "Empty output received (raw attribute is None)"
    elif hasattr(output, '__str__'):  # Fallback to string representation
        try:
            output_text = str(output)
            if output_text == 'None':
                output_text = "Empty output received (string representation is 'None')"
        except Exception as e:
            output_text = f"Error converting output to string: {str(e)}"
    else:
        output_text = f"Unable to convert output of type {type(output)} to string"

    with open(os.path.join(output_dir, filename), "w") as f:
        f.write(output_text)

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

def read_file_or_exit(file_path, file_description):
    """Read file content or exit with error if file doesn't exist.
    
    Args:
        file_path: Path to the file to read
        file_description: Description of the file for error message
        
    Returns:
        Content of the file
    """
    try:
        with open(file_path, 'r') as f:
            return f.read()
    except Exception as e:
        print(f"[ERROR] Failed to read {file_description} from {file_path}: {e}")
        print("Please provide a valid file path or run the stage instead of skipping it.")
        import sys
        sys.exit(1)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Generate research proposals using CrewAI')
    
    # Paper ingestion options
    parser.add_argument('--papers', nargs='+', help='Paper URLs or file paths to ingest')
    parser.add_argument('--papers-dir', default='data/papers', help='Directory containing research papers')
    parser.add_argument('--skip-ingestion', action='store_true', help='Skip paper ingestion and use existing Chroma DB')
    
    # Agent execution options
    parser.add_argument('--skip-researcher', action='store_true', help='Skip the Research Scientist stage')
    parser.add_argument('--skip-domain-expert', action='store_true', help='Skip the Domain Expert stage')
    parser.add_argument('--skip-writer-draft', action='store_true', help='Skip the Proposal Writer draft stage')
    parser.add_argument('--skip-critic', action='store_true', help='Skip the Critic stage')
    parser.add_argument('--skip-writer-refine', action='store_true', help='Skip the Proposal Writer refinement stage')
    
    # Input file options (for skipping stages)
    parser.add_argument('--lit-review-file', help='Path to existing literature review file (when skipping researcher)')
    parser.add_argument('--domain-validation-file', help='Path to existing domain validation file (when skipping domain expert)')
    parser.add_argument('--proposal-draft-file', help='Path to existing proposal draft file (when skipping writer draft)')
    parser.add_argument('--proposal-critique-file', help='Path to existing proposal critique file (when skipping critic)')
    
    return parser.parse_args()

def main():
    """Run the research proposal generation crew."""
    # Parse arguments
    args = parse_args()
    
    # Validate environment configuration
    config.validate()
    
    # Initialize vector store
    if hasattr(args, 'skip_ingestion') and args.skip_ingestion:
        print("\n🔍 Skipping paper ingestion, using existing Chroma DB...")
        vector_store = VectorStore(persist_directory="data/chroma_db")
    else:
        # Ingest papers
        papers_dir = args.papers_dir if hasattr(args, 'papers_dir') else 'data/papers'
        paper_sources = args.papers if hasattr(args, 'papers') else None
        vector_store = ingest_papers(paper_sources, papers_dir)
    
    # Initialize factories with the vector store
    print("\n[DEBUG] Main: Initializing agent factory with vector store")
    try:
        agent_factory = AgentFactory(vector_store)
        print("[DEBUG] Main: Successfully initialized agent factory")
    except Exception as e:
        print(f"[ERROR] Main: Failed to initialize agent factory: {e}")
        print(f"[ERROR] Main: Error type: {type(e).__name__}")
        import traceback
        print(f"[ERROR] Main: {traceback.format_exc()}")
        raise
        
    print("[DEBUG] Main: Initializing task factory")
    try:
        task_factory = TaskFactory(agent_factory)
        print("[DEBUG] Main: Successfully initialized task factory")
    except Exception as e:
        print(f"[ERROR] Main: Failed to initialize task factory: {e}")
        print(f"[ERROR] Main: Error type: {type(e).__name__}")
        import traceback
        print(f"[ERROR] Main: {traceback.format_exc()}")
        raise
    
    print("🤖 Initializing research crew...")
    
    # Step 1: Literature Review (Research Scientist)
    skip_researcher = hasattr(args, 'skip_researcher') and args.skip_researcher
    if skip_researcher:
        print("\n🔬 Skipping literature review (Research Scientist stage)...")
        if hasattr(args, 'lit_review_file') and args.lit_review_file:
            lit_review_result = read_file_or_exit(args.lit_review_file, "literature review")
            print(f"📄 Loaded literature review from {args.lit_review_file}")
        else:
            lit_review_result = read_file_or_exit("outputs/literature_review.md", "literature review")
            print("📄 Loaded literature review from outputs/literature_review.md")
    else:
        # Create and execute literature review task
        literature_review_task = task_factory.create_task("literature_review")
        print("\n🔬 Starting literature review...")

        # Break the literature review into stages to avoid token limitations

        # Stage 1: Research and Planning
        planning_task = Task(
            description="""Plan a comprehensive literature review on Generative AI in healthcare.
            Create a detailed outline covering:
            1. Introduction to Generative AI in healthcare
            2. Recent advances in generative AI models
            3. Current clinical applications
            4. Ethical considerations and challenges
            5. Data privacy and security concerns
            6. Research gaps and opportunities

            Provide a structured outline with brief descriptions of each section.
            """,
            agent=agent_factory.create_agent("researcher"),
            expected_output="A detailed outline for the literature review"
        )

        # Stage 2: Execution of the review based on the outline
        print("Planning the literature review structure...")
        planning_crew = Crew(
            agents=[agent_factory.create_agent("researcher")],
            tasks=[planning_task],
            verbose=True
        )
        review_plan = planning_crew.kickoff()

        # Now use the plan to create the actual review
        execution_task = Task(
            description=f"""Based on the following outline, write a complete literature review on Generative AI applications in healthcare.

            OUTLINE:
            {review_plan}

            Follow these guidelines:
            1. Use clear academic Markdown format
            2. Include all sections from the outline
            3. Be comprehensive but concise
            4. Include references to key papers
            5. Highlight research gaps clearly
            6. Write a complete conclusion that summarizes the key findings

            IMPORTANT: Make sure to complete ALL sections of the review. If you reach a token limit,
            focus on completing the content with slightly less detail rather than leaving sections unfinished.
            """,
            agent=agent_factory.create_agent("researcher"),
            expected_output="A complete literature review following the outline"
        )

        print("\n🔬 Writing the full literature review based on the outline...")
        execution_crew = Crew(
            agents=[agent_factory.create_agent("researcher")],
            tasks=[execution_task],
            verbose=True
        )
        lit_review_result = execution_crew.kickoff()

        # Save the result
        save_output(lit_review_result, "literature_review.md")
    
    # Step 2: Domain Validation (Domain Expert)
    skip_domain_expert = hasattr(args, 'skip_domain_expert') and args.skip_domain_expert
    if skip_domain_expert:
        print("\n🏥 Skipping domain validation (Domain Expert stage)...")
        if hasattr(args, 'domain_validation_file') and args.domain_validation_file:
            validation_result = read_file_or_exit(args.domain_validation_file, "domain validation")
            print(f"📄 Loaded domain validation from {args.domain_validation_file}")
        else:
            validation_result = read_file_or_exit("outputs/domain_validation.md", "domain validation")
            print("📄 Loaded domain validation from outputs/domain_validation.md")
    else:
        # Create and execute domain validation task
        domain_validation_task = task_factory.create_task(
            "domain_validation", 
            context=lit_review_result
        )
        print("\n🏥 Validating research directions with domain expert...")
        crew = Crew(
            agents=[agent_factory.create_agent("domain_expert")],
            tasks=[domain_validation_task],
            verbose=True
        )
        validation_result = crew.kickoff()
        save_output(validation_result, "domain_validation.md")
    
    # Combined context for proposal drafting (safely handle None values)
    lit_review_text = "No literature review available" if lit_review_result is None else lit_review_result
    validation_text = "No domain validation available" if validation_result is None else validation_result
    combined_context = f"Literature Review:\n{lit_review_text}\n\nDomain Validation:\n{validation_text}"
    
    # Step 3: Proposal Drafting (Proposal Writer)
    skip_writer_draft = hasattr(args, 'skip_writer_draft') and args.skip_writer_draft
    if skip_writer_draft:
        print("\n📝 Skipping proposal drafting (Writer draft stage)...")
        if hasattr(args, 'proposal_draft_file') and args.proposal_draft_file:
            proposal_draft = read_file_or_exit(args.proposal_draft_file, "proposal draft")
            print(f"📄 Loaded proposal draft from {args.proposal_draft_file}")
        else:
            proposal_draft = read_file_or_exit("outputs/proposal_draft.md", "proposal draft")
            print("📄 Loaded proposal draft from outputs/proposal_draft.md")
    else:
        # Create and execute proposal drafting task - break into stages
        print("\n📝 Drafting research proposal...")

        # Stage 1: Planning the proposal
        planning_task = Task(
            description=f"""Based on the following context about generative AI in healthcare,
            plan a research proposal by deciding on a specific research focus and creating an outline.

            Context from previous tasks:
            {combined_context}

            Your plan should include:
            1. 2-3 potential research titles focused on a specific application of generative AI in healthcare
            2. Brief descriptions of the key problems each potential research direction addresses
            3. A recommended title and focus area with justification
            4. A detailed section-by-section outline for the proposal, following this structure:
               - Title
               - Abstract
               - Background & Literature Review
               - Problem Statement & Research Gap
               - Proposed Gen AI Approach
               - Expected Impact in Healthcare
               - Limitations or Ethical Considerations
               - References

            Provide a clear, structured outline that will guide writing the full proposal.
            """,
            agent=agent_factory.create_agent("proposal_writer"),
            expected_output="A detailed plan and outline for the research proposal"
        )

        print("Planning the research proposal structure...")
        planning_crew = Crew(
            agents=[agent_factory.create_agent("proposal_writer")],
            tasks=[planning_task],
            verbose=True
        )
        proposal_plan = planning_crew.kickoff()

        # Stage 2: Writing the content based on the plan (except abstract)
        content_task = Task(
            description=f"""Based on the following plan and context, write a complete research proposal
            for generative AI in healthcare, EXCEPT for the abstract which will be written last.

            PROPOSAL PLAN:
            {proposal_plan}

            CONTEXT FROM PREVIOUS TASKS:
            {combined_context}

            Write all sections of the proposal EXCEPT the abstract:
            1. Title
            2. [Abstract will be added later]
            3. Background & Literature Review
            4. Problem Statement & Research Gap
            5. Proposed Gen AI Approach
            6. Expected Impact in Healthcare
            7. Limitations or Ethical Considerations
            8. References

            For each section, be thorough, specific, and academically sound.
            Format the proposal in Markdown for readability.
            Ensure that all sections are complete before submitting.
            """,
            agent=agent_factory.create_agent("proposal_writer"),
            expected_output="A complete research proposal without the abstract"
        )

        print("\n📝 Writing the proposal content (excluding abstract)...")
        content_crew = Crew(
            agents=[agent_factory.create_agent("proposal_writer")],
            tasks=[content_task],
            verbose=True
        )
        proposal_content = content_crew.kickoff()

        # Stage 3: Writing just the abstract based on the completed content
        abstract_task = Task(
            description=f"""Write ONLY an abstract (150-250 words) for the following research proposal.
            The abstract should summarize the entire proposal concisely, highlighting the problem,
            approach, methodology, and expected impact.

            COMPLETED PROPOSAL:
            {proposal_content}

            Your task is to:
            1. Read and understand the full proposal
            2. Write ONLY the abstract section (150-250 words)
            3. Ensure the abstract covers all key aspects of the proposal
            4. Count the words to ensure it's between 150-250 words
            5. Format it for insertion in the proposal

            Return only the abstract text, formatted in Markdown.
            """,
            agent=agent_factory.create_agent("proposal_writer"),
            expected_output="An abstract for the research proposal (150-250 words)"
        )

        print("\n📝 Writing the abstract based on the full proposal...")
        abstract_crew = Crew(
            agents=[agent_factory.create_agent("proposal_writer")],
            tasks=[abstract_task],
            verbose=True
        )
        proposal_abstract = abstract_crew.kickoff()

        # Stage 4: Combining the abstract with the proposal content
        print("\n📝 Combining the abstract with the full proposal...")

        # Extract the abstract text
        abstract_text = proposal_abstract
        if hasattr(proposal_abstract, 'raw'):
            abstract_text = proposal_abstract.raw
        elif hasattr(proposal_abstract, '__str__'):
            abstract_text = str(proposal_abstract)
        else:
            abstract_text = "Abstract generation failed. Please review the proposal and write an abstract manually."

        # Extract the proposal content
        content_text = proposal_content
        if hasattr(proposal_content, 'raw'):
            content_text = proposal_content.raw
        elif hasattr(proposal_content, '__str__'):
            content_text = str(proposal_content)
        else:
            content_text = "Proposal content generation failed. Please review the previous stages."

        # Insert the abstract in the appropriate place
        import re
        if "## Abstract" in content_text or "## 2. Abstract" in content_text:
            # If there's a placeholder for the abstract, replace it
            proposal_draft = re.sub(
                r'(## Abstract|## 2\. Abstract)(\s*\n)(?:[^\n]*\n)*?(?=\n*##|$)',
                r'\1\2' + abstract_text + '\n\n',
                content_text
            )
        else:
            # If no placeholder, add the abstract after the title
            title_match = re.search(r'(# .+?\n|## Title.*?\n|## 1\. Title.*?\n)([^\n]*\n)', content_text)
            if title_match:
                title_end = title_match.end()
                proposal_draft = content_text[:title_end] + "\n## Abstract\n\n" + abstract_text + "\n\n" + content_text[title_end:]
            else:
                # If no title found, just prepend the abstract
                proposal_draft = "## Abstract\n\n" + abstract_text + "\n\n" + content_text

        save_output(proposal_draft, "proposal_draft.md")
    
    # Updated context for critique (safely handle None values)
    proposal_text = "No proposal draft available" if proposal_draft is None else proposal_draft
    updated_context = f"{combined_context}\n\nProposal Draft:\n{proposal_text}"
    
    # Step 4: Proposal Critique (Critic)
    skip_critic = hasattr(args, 'skip_critic') and args.skip_critic
    if skip_critic:
        print("\n🔍 Skipping proposal critique (Critic stage)...")
        if hasattr(args, 'proposal_critique_file') and args.proposal_critique_file:
            critique_result = read_file_or_exit(args.proposal_critique_file, "proposal critique")
            print(f"📄 Loaded proposal critique from {args.proposal_critique_file}")
        else:
            critique_result = read_file_or_exit("outputs/proposal_critique.md", "proposal critique")
            print("📄 Loaded proposal critique from outputs/proposal_critique.md")
    else:
        # Create and execute critique task
        critique_task = task_factory.create_task(
            "proposal_critique",
            context=updated_context
        )
        print("\n🔍 Critiquing research proposal...")
        crew = Crew(
            agents=[agent_factory.create_agent("critic")],
            tasks=[critique_task],
            verbose=True
        )
        critique_result = crew.kickoff()
        save_output(critique_result, "proposal_critique.md")
    
    # Final context for refinement (safely handle None values)
    critique_text = "No critique available" if critique_result is None else critique_result
    final_context = f"{updated_context}\n\nCritique:\n{critique_text}"
    
    # Step 5: Proposal Refinement (Proposal Writer)
    skip_writer_refine = hasattr(args, 'skip_writer_refine') and args.skip_writer_refine
    if skip_writer_refine:
        print("\n✨ Skipping proposal refinement (Writer refinement stage)...")
        print("⚠️ No final proposal will be generated.")
    else:
        # Create and execute refinement task
        refinement_task = task_factory.create_task(
            "proposal_refinement",
            context=final_context
        )
        print("\n✨ Refining final research proposal...")
        crew = Crew(
            agents=[agent_factory.create_agent("proposal_writer")],
            tasks=[refinement_task],
            verbose=True
        )
        final_proposal = crew.kickoff()
        save_output(final_proposal, "final_proposal.md")
        print("\n✅ Research proposal generation complete!")
        print("Final proposal saved to outputs/final_proposal.md")

if __name__ == "__main__":
    main()