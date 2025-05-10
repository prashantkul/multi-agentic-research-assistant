"""Task definitions for the research proposal crew."""
from crewai import Task

class ResearchTasks:
    """Factory class for creating research proposal tasks."""
    
    @staticmethod
    def literature_review(researcher):
        """Create a literature review task."""
        return Task(
            description="""Conduct a comprehensive literature review on Generative AI applications in 
            healthcare. Identify key research trends, notable successes, limitations, 
            and gaps in the current literature. Focus on:
            1. Recent advances in generative AI models for healthcare
            2. Current applications in clinical settings
            3. Ethical considerations and challenges
            4. Data privacy and security concerns
            5. Gaps and opportunities for novel research
            
            Your output should be a structured summary with references to key papers.
            """,
            agent=researcher,
            expected_output="A comprehensive literature review document with identified research gaps",
        )
    
    @staticmethod
    def domain_validation(domain_expert, context=""):
        """Create a domain validation task."""
        return Task(
            description=f"""Review the identified research gaps and opportunities in the healthcare domain.
            Provide your expert opinion on:
            1. Clinical relevance and potential impact
            2. Practical implementation challenges
            3. Regulatory and ethical considerations
            4. Data availability and quality issues
            5. Integration with existing healthcare systems
            
            Context from previous tasks:
            {context}
            
            Your output should be a validation report highlighting the most promising
            research directions from a healthcare perspective.
            """,
            agent=domain_expert,
            expected_output="A validation report on proposed research directions",
        )
    
    @staticmethod
    def proposal_drafting(writer, context=""):
        """Create a proposal drafting task."""
        return Task(
            description=f"""Draft a comprehensive research proposal for a novel application of 
            Generative AI in healthcare based on the identified gaps and validated
            research directions.
            
            The proposal should include:
            1. Project title
            2. Executive summary
            3. Background and significance
            4. Research objectives and hypotheses
            5. Methodology
            6. Expected outcomes and impact
            7. Ethical considerations
            8. Timeline and milestones
            
            Context from previous tasks:
            {context}
            
            Ensure the proposal is academically sound, novel, and addresses a significant
            healthcare challenge.
            """,
            agent=writer,
            expected_output="A complete draft research proposal",
        )
    
    @staticmethod
    def proposal_critique(critic, context=""):
        """Create a proposal critique task."""
        return Task(
            description=f"""Thoroughly critique the draft research proposal, focusing on:
            1. Scientific merit and novelty
            2. Methodological soundness
            3. Feasibility and practical implementation
            4. Potential impact and significance
            5. Clarity and structure
            6. Limitations and potential challenges
            
            Context from previous tasks:
            {context}
            
            Provide specific, constructive feedback for improving the proposal.
            """,
            agent=critic,
            expected_output="A detailed critique with specific improvement suggestions",
        )
    
    @staticmethod
    def proposal_refinement(writer, context=""):
        """Create a proposal refinement task."""
        return Task(
            description=f"""Refine the research proposal based on the critique and feedback received.
            Address all the points raised in the critique and strengthen the proposal accordingly.
            
            Context from previous tasks:
            {context}
            
            Produce a final, polished research proposal that is ready for submission.
            """,
            agent=writer,
            expected_output="A refined, final research proposal",
        )