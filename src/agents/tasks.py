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

            Structure your literature review as follows:

            1. Title: "Generative AI in Healthcare: A Comprehensive Literature Review"
            2. Abstract: A brief summary of the review (100-150 words)
            3. Introduction: Overview of generative AI and its relevance to healthcare
            4. Methods: Approach to literature selection and review
            5. Results/Findings: Organized by the five focus areas mentioned above
            6. Discussion: Synthesis of findings, identifying patterns and research gaps
            7. Conclusion: Summary of key insights and promising research directions
            8. References: Key papers cited in the review

            IMPORTANT NOTES:
            - Write in clear academic Markdown format
            - Include citations to specific papers when discussing research
            - Be thorough and comprehensive in your analysis
            - Clearly highlight research gaps and opportunities
            - Ensure all sections are complete before submitting
            - Your review should be a standalone document that provides a solid foundation for further research
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
        # Ensure context is not None
        safe_context = context if context else "No context provided from previous stages."

        return Task(
            description=f"""Draft a comprehensive research proposal for a novel application of
            Generative AI in healthcare based on the identified gaps and validated
            research directions.

            The proposal should be structured as a 2-3 page academic research proposal with the following sections:

            1. Title (Concise and descriptive of the research focus)
            2. Abstract (150-250 words summarizing the proposal)
               - Create the abstract after completing the rest of the proposal
               - Summarize the key points of your proposal in clear, concise language
               - Include brief mentions of the problem, approach, and expected impact
               - Avoid using references or citations in the abstract
            3. Background & Literature Review (Concise summary of key related work)
            4. Problem Statement & Research Gap (Clear articulation of the gap being addressed)
            5. Proposed Gen AI Approach (Methodology and technical details)
            6. Expected Impact in Healthcare (Potential benefits and applications)
            7. Limitations or Ethical Considerations (Potential challenges and ethical issues)
            8. References (Key citations in academic format)

            Context from previous tasks:
            {safe_context}

            IMPORTANT NOTES:
            - Write in Markdown format for readability
            - Generate all sections completely from scratch without relying on external sources
            - Create self-contained content that doesn't reference unavailable information
            - If you encounter any issues with creating a section, provide a placeholder with an explanation
            - Ensure the proposal is academically sound, novel, and addresses a significant healthcare challenge
            """,
            agent=writer,
            expected_output="A complete draft research proposal in the required format",
        )
    
    @staticmethod
    def proposal_critique(critic, context=""):
        """Create a proposal critique task."""
        # Ensure context is not None
        safe_context = context if context else "No context provided from previous stages."

        return Task(
            description=f"""Thoroughly critique the draft research proposal, focusing on:
            1. Scientific merit and novelty
            2. Methodological soundness
            3. Feasibility and practical implementation
            4. Potential impact and significance
            5. Adherence to the required format and structure
            6. Completeness of all required sections
            7. Clarity and quality of writing
            8. Limitations and potential challenges

            Ensure the proposal follows the required structure:
            - Title
            - Abstract (150-250 words)
            - Background & Literature Review
            - Problem Statement & Research Gap
            - Proposed Gen AI Approach
            - Expected Impact in Healthcare
            - Limitations or Ethical Considerations
            - References

            Context from previous tasks:
            {safe_context}

            IMPORTANT NOTES:
            - If any section is missing or incomplete, note this specifically
            - Provide constructive feedback that can be used to improve the proposal
            - Format your critique in a clear, organized manner with section-by-section feedback
            - If you encounter any issues with the proposal, describe them clearly and suggest solutions
            - Focus on both content and formatting issues
            """,
            agent=critic,
            expected_output="A detailed critique with specific improvement suggestions regarding both content and format",
        )
    
    @staticmethod
    def proposal_refinement(writer, context=""):
        """Create a proposal refinement task."""
        # Ensure context is not None
        safe_context = context if context else "No context provided from previous stages."

        return Task(
            description=f"""Refine the research proposal based on the critique and feedback received.
            Address all the points raised in the critique and strengthen the proposal accordingly.

            The final proposal must maintain the required structure:
            1. Title
            2. Abstract (150-250 words)
            3. Background & Literature Review
            4. Problem Statement & Research Gap
            5. Proposed Gen AI Approach
            6. Expected Impact in Healthcare
            7. Limitations or Ethical Considerations
            8. References

            Additionally, include a short section (max 1/2 page) titled "Multi-Agent Reflection"
            at the end of the proposal reflecting on how the different agents (researcher,
            domain expert, critic, and writer) helped shape the thinking and proposal.

            Context from previous tasks:
            {safe_context}

            IMPORTANT NOTES:
            - Address all feedback points from the critique
            - Ensure all sections are complete and well-developed
            - Maintain academic writing standards and Markdown formatting
            - Pay special attention to the abstract, ensuring it is 150-250 words and summarizes the full proposal
            - If you encounter any issues with specific sections, explain your approach in the Multi-Agent Reflection
            - Check that citations are properly formatted in the References section

            Produce a final, polished research proposal in Markdown format that is ready for submission.
            """,
            agent=writer,
            expected_output="A refined, final research proposal with the required structure and reflection section",
        )