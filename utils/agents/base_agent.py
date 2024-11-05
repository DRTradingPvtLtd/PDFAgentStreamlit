from phi.llm.openai.chat import OpenAIChat
import os
from phi.agent import Agent

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
            system_prompt="I am an AI assistant helping with document analysis and question answering.",
            add_chat_history_to_messages=True,
            debug_mode=False
        )
    
    def log_action(self, action: str, details: str = None):
        """Log agent actions for monitoring."""
        message = f"[{self.name}] {action}" + (f": {details}" if details else "")
        print(message)
        # Add message to conversation history using phidata's method
        self.add_message("system", message)
