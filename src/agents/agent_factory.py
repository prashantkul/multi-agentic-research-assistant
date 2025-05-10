"""Agent factory module for creating agents from YAML configuration."""
from typing import Dict, List, Optional
from crewai import Agent
from langchain.tools import Tool
from src.utils.yaml_loader import YAMLLoader
from src.utils.gemini_llm import GeminiLLM
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
        self.llm = GeminiLLM.get_llm()
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

    def _create_rag_tools(self) -> List[Tool]:
        """Create RAG tools for domain expert agent.

        Returns:
            List of RAG tools
        """
        search_tool = Tool(
            name="SearchLiterature",
            description="Search academic literature for information on a specific topic",
            func=lambda query: self.rag_chain.query(query)["answer"],
        )

        citation_tool = Tool(
            name="GetCitations",
            description="Get citations from academic literature for a specific topic",
            func=lambda query: str(self.rag_chain.get_citations(query)),
        )

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