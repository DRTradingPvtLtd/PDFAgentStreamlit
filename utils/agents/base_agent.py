from phi.llm.openai.chat import OpenAIChat
import os
from typing import List, Dict, Any
from phi.agent.agent import Agent

class BaseAgent(Agent):
    """Base class for all agents in the system using phidata framework."""
    
    def __init__(self, name: str):
        llm = OpenAIChat(
            model=os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4"),
            api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
            api_base=os.environ.get("AZURE_OPENAI_ENDPOINT"),
            api_type="azure",
            api_version="2023-05-15"
        )
        
        super().__init__(
            name=name,
            llm=llm,
            add_chat_history_to_messages=True,
            debug_mode=False
        )
        self._conversation_history: List[Dict[str, Any]] = []
    
    def log_action(self, action: str, details: str = None):
        """Log agent actions for monitoring."""
        message = f"[{self.name}] {action}" + (f": {details}" if details else "")
        print(message)
        self._conversation_history.append({"role": "system", "content": message})
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get the conversation history."""
        return self._conversation_history

    def add_to_history(self, role: str, content: str):
        """Add a message to the conversation history."""
        self._conversation_history.append({"role": role, "content": content})
