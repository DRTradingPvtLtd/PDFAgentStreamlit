from abc import ABC, abstractmethod

class BaseAgent(ABC):
    """Base class for all agents in the system."""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    async def process(self, *args, **kwargs):
        """Main processing method that each agent must implement."""
        pass
    
    def log_action(self, action: str, details: str = None):
        """Log agent actions for monitoring."""
        print(f"[{self.name}] {action}" + (f": {details}" if details else ""))
