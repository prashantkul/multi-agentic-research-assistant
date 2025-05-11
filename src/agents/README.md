# Multi-Agent Workflow for Research Proposal Generation

This directory contains the agent and task definitions for the multi-agent system that generates research proposals in the domain of Generative AI in healthcare.

## Agent Roles

1. **Research Scientist**
   - Conducts comprehensive literature reviews
   - Identifies research gaps and emerging trends
   - Uses base LLM knowledge without RAG capabilities
   - Outputs structured summaries with identified opportunities

2. **Healthcare Domain Expert**
   - Validates research directions from a clinical perspective
   - **Uses RAG capabilities** to ground insights in academic literature
   - Provides citations and evidence-based validation
   - Assesses clinical relevance and practical implementation challenges

3. **Research Proposal Writer**
   - Drafts and refines research proposals
   - Structures content according to academic standards
   - Creates cohesive narratives from different agent inputs
   - Produces the initial draft and final refined proposal

4. **Research Proposal Critic**
   - Evaluates research proposals for scientific merit
   - Identifies methodological weaknesses
   - Checks for format and structure adherence
   - Provides constructive feedback for improvement

## Workflow Structure

The workflow is implemented as a sequential, staged process:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│                 │    │                 │    │                 │    │                 │    │                 │
│     Stage 1     │    │     Stage 2     │    │     Stage 3     │    │     Stage 4     │    │     Stage 5     │
│                 │    │                 │    │                 │    │                 │    │                 │
│  Research       │    │  Domain Expert  │    │  Proposal       │    │  Critic         │    │  Proposal       │
│  Scientist      │───▶│  (with RAG)     │───▶│  Writer         │───▶│                 │───▶│  Writer         │
│                 │    │                 │    │  (Draft)        │    │                 │    │  (Refinement)   │
│                 │    │                 │    │                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
        │                      │                      │                      │                      │
        ▼                      ▼                      ▼                      ▼                      ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ literature_     │    │ domain_         │    │ proposal_       │    │ proposal_       │    │ final_          │
│ review.md       │    │ validation.md   │    │ draft.md        │    │ critique.md     │    │ proposal.md     │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Information Flow

1. **Research Scientist** performs literature review, output saved to `literature_review.md`
2. **Domain Expert** receives the literature review as context, validates with RAG, output saved to `domain_validation.md`
3. **Proposal Writer** receives both outputs as context, drafts proposal, output saved to `proposal_draft.md`
4. **Critic** receives all previous outputs as context, critiques the proposal, output saved to `proposal_critique.md`
5. **Proposal Writer** receives all previous outputs as context, refines proposal, output saved to `final_proposal.md`

Each stage passes its results to the next stage as context, creating a growing body of information that culminates in the final research proposal.

## Technical Implementation

- Each agent runs in a separate CrewAI `Crew` instance
- Context is explicitly passed between stages using output files
- RAG capabilities are specifically implemented for the Domain Expert
- All agent definitions are loaded from YAML configuration files
- Agents use Vertex AI for generation through adapter classes

## Limitations and Future Improvements

The current implementation has some limitations:

- Agents do not interact directly with each other (pipeline approach)
- No back-and-forth dialogue or real-time collaboration
- Only one agent (Domain Expert) has RAG capabilities

Potential improvements:

- Implement CrewAI RPCs for direct agent-to-agent interaction
- Add RAG capabilities to more agents
- Create parallel workflows for different aspects of the proposal
- Add human-in-the-loop feedback mechanisms between stages