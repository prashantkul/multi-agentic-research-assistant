"""Agent factory module for creating agents from YAML configuration."""
from typing import Dict, List, Optional
from crewai import Agent
from crewai_tools import BaseTool
from src.utils.yaml_loader import YAMLLoader
from src.utils.gemini_adapter import get_langchain_compatible_llm
from src.utils.vector_store import VectorStore
from src.utils.rag_chain import RAGChain

class AgentFactory:
    """Factory class for creating agents from YAML configuration."""

    def __init__(self, vector_store: Optional[VectorStore] = None):
        """Initialize the agent factory.
        
        Args:
            vector_store: Optional vector store for RAG capabilities
        """
        self.agent_configs = YAMLLoader.get_agents_config()
        self.agents_cache: Dict[str, Agent] = {}
        print("[DEBUG] AgentFactory: Getting LangChain-compatible LLM")
        self.llm = get_langchain_compatible_llm()
        self.vector_store = vector_store or VectorStore()
        self.rag_chain = RAGChain(self.vector_store)

    def create_agent(self, agent_id: str) -> Agent:
        """Create an agent by ID from the YAML configuration.
        
        Args:
            agent_id: The ID of the agent to create
            
        Returns:
            The created agent
            
        Raises:
            ValueError: If the agent ID is not found in the configuration
        """
        # Return from cache if available
        if agent_id in self.agents_cache:
            return self.agents_cache[agent_id]
        
        # Find agent config by ID
        agent_config = next(
            (config for config in self.agent_configs if config.get('id') == agent_id),
            None
        )
        
        if not agent_config:
            raise ValueError(f"Agent with ID '{agent_id}' not found in configuration")
        
        # Create base agent from config
        agent_kwargs = {
            "role": agent_config.get('role'),
            "goal": agent_config.get('goal'),
            "backstory": agent_config.get('backstory'),
            "verbose": agent_config.get('verbose', True),
            "allow_delegation": agent_config.get('allow_delegation', True),
            "llm": self.llm
        }
        
        # Add tools for specific agents
        if agent_id == "domain_expert":
            # Add RAG-specific tools for the domain expert
            agent_kwargs["tools"] = self._create_rag_tools()
        
        # Create agent
        agent = Agent(**agent_kwargs)
        
        # Cache agent for future use
        self.agents_cache[agent_id] = agent
        
        return agent
    
    def _create_rag_tools(self) -> List[BaseTool]:
        """Create RAG tools for domain expert agent.

        Returns:
            List of RAG tools for CrewAI compatibility
        """
        from typing import Optional, Type, Any
        from pydantic import Field, BaseModel

        class SearchLiteratureTool(BaseTool):
            """Tool for searching academic literature."""
            name: str = Field("SearchLiterature", description="Name of the tool")
            description: str = Field(
                "Search academic literature for information on a specific topic",
                description="Description of the tool"
            )
            rag_chain: Any = Field(None, description="RAG chain for querying literature", exclude=True)

            def __init__(self, rag_chain):
                """Initialize the tool with the RAG chain."""
                super().__init__(rag_chain=rag_chain)

            def _run(self, query: str) -> str:
                """Run the tool."""
                try:
                    # Get result from RAG chain
                    result = self.rag_chain.query(query)
                    # Return answer or fallback
                    return result.get("answer", "No specific information found in the literature for this query.")
                except Exception as e:
                    print(f"Error in SearchLiteratureTool: {e}")
                    return f"I encountered an error while searching the literature: {str(e)}. Please try another query."

        class GetCitationsTool(BaseTool):
            """Tool for retrieving citations from academic literature."""
            name: str = Field("GetCitations", description="Name of the tool")
            description: str = Field(
                "Get citations from academic literature for a specific topic",
                description="Description of the tool"
            )
            rag_chain: Any = Field(None, description="RAG chain for retrieving citations", exclude=True)

            def __init__(self, rag_chain):
                """Initialize the tool with the RAG chain."""
                super().__init__(rag_chain=rag_chain)

            def _run(self, query: str) -> str:
                """Run the tool."""
                try:
                    citations = self.rag_chain.get_citations(query)
                    if not citations:
                        return "No relevant citations found in the literature for this query."
                    return str(citations)
                except Exception as e:
                    print(f"Error in GetCitationsTool: {e}")
                    return f"I encountered an error while retrieving citations: {str(e)}. Please try another query."

        # Create and return tool instances
        search_tool = SearchLiteratureTool(self.rag_chain)
        citation_tool = GetCitationsTool(self.rag_chain)

        return [search_tool, citation_tool]
    
    def create_all_agents(self) -> List[Agent]:
        """Create all agents defined in the YAML configuration.
        
        Returns:
            List of all created agents
        """
        agents = []
        
        for config in self.agent_configs:
            agent_id = config.get('id')
            if agent_id:
                agents.append(self.create_agent(agent_id))
        
        return agents