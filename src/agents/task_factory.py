"""Task factory module for creating tasks from YAML configuration."""
from typing import Dict, List, Optional
from crewai import Task, Agent
from src.utils.yaml_loader import YAMLLoader
from src.agents.agent_factory import AgentFactory

class TaskFactory:
    """Factory class for creating tasks from YAML configuration."""
    
    def __init__(self, agent_factory: AgentFactory):
        """Initialize the task factory.
        
        Args:
            agent_factory: Agent factory for resolving agent references
        """
        self.task_configs = YAMLLoader.get_tasks_config()
        self.agent_factory = agent_factory
        self.tasks_cache: Dict[str, Task] = {}
    
    def create_task(self, task_id: str, context: Optional[str] = None) -> Task:
        """Create a task by ID from the YAML configuration.
        
        Args:
            task_id: The ID of the task to create
            context: Optional context to inject into the task description
            
        Returns:
            The created task
            
        Raises:
            ValueError: If the task ID is not found in the configuration
        """
        # Find task config by ID
        task_config = next(
            (config for config in self.task_configs if config.get('id') == task_id),
            None
        )
        
        if not task_config:
            raise ValueError(f"Task with ID '{task_id}' not found in configuration")
        
        # Get the agent for this task
        agent_id = task_config.get('agent')
        if not agent_id:
            raise ValueError(f"Task '{task_id}' does not have an associated agent")
        
        agent = self.agent_factory.create_agent(agent_id)
        
        # Prepare description with context if required
        description = task_config.get('description', '')
        if context and task_config.get('context_required', False):
            description = f"{description}\n\nContext from previous tasks:\n{context}"
        
        # Create task from config
        task = Task(
            description=description,
            expected_output=task_config.get('expected_output', ''),
            agent=agent
        )
        
        return task
    
    def create_task_sequence(self, context_map: Optional[Dict[str, str]] = None) -> List[Task]:
        """Create all tasks in sequence, passing context between them as needed.
        
        Args:
            context_map: Optional mapping of task IDs to their contexts
            
        Returns:
            List of all created tasks in sequence
        """
        tasks = []
        context_map = context_map or {}
        
        for config in self.task_configs:
            task_id = config.get('id')
            if task_id:
                context = context_map.get(task_id)
                tasks.append(self.create_task(task_id, context))
        
        return tasks