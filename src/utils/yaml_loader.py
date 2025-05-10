"""YAML configuration loader utility."""
import os
import yaml
from typing import Dict, Any, List

class YAMLLoader:
    """Utility class for loading YAML configuration files."""
    
    @staticmethod
    def load_yaml(file_path: str) -> Dict[str, Any]:
        """Load a YAML file and return its contents as a dictionary.
        
        Args:
            file_path: Path to the YAML file
            
        Returns:
            Dictionary containing the YAML file contents
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"YAML file not found: {file_path}")
        
        with open(file_path, 'r') as file:
            try:
                return yaml.safe_load(file)
            except yaml.YAMLError as e:
                raise ValueError(f"Error parsing YAML file {file_path}: {e}")
    
    @staticmethod
    def get_agents_config() -> List[Dict[str, Any]]:
        """Load the agents configuration from YAML.
        
        Returns:
            List of agent configurations
        """
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        agents_path = os.path.join(base_dir, 'config', 'agents.yaml')
        
        config = YAMLLoader.load_yaml(agents_path)
        return config.get('agents', [])
    
    @staticmethod
    def get_tasks_config() -> List[Dict[str, Any]]:
        """Load the tasks configuration from YAML.
        
        Returns:
            List of task configurations
        """
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        tasks_path = os.path.join(base_dir, 'config', 'tasks.yaml')
        
        config = YAMLLoader.load_yaml(tasks_path)
        return config.get('tasks', [])