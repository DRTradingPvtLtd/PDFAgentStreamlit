from .base_agent import BaseAgent
import os

class SummaryAgent(BaseAgent):
    """Agent responsible for document summarization operations."""
    
    def __init__(self):
        super().__init__(name="Summary Agent")
        
        # Store templates as instance variable, not class attribute
        self._templates = {
            "concise": "Please provide a brief summary of the following text in 2-3 sentences:",
            "detailed": "Please provide a comprehensive summary of the following text, including main points and key details:",
            "bullet_points": "Please summarize the following text in a bullet-point format, highlighting the key points:"
        }
    
    async def process(self, text: str, summary_type: str = "concise") -> dict:
        """Generate summary of the provided text."""
        try:
            if summary_type not in self._templates:
                summary_type = "concise"
            
            prompt = self._create_summary_prompt(text, summary_type)
            self.add_to_history("user", prompt)
            
            response = await self.llm.chat(messages=self._conversation_history)
            summary = response.content
            
            self.add_to_history("assistant", summary)
            
            return {
                "success": True,
                "summary": summary,
                "metadata": {
                    "type": summary_type,
                    "model": os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4")
                }
            }
        except Exception as e:
            self.log_action("Error", str(e))
            return {
                "success": False,
                "error": str(e)
            }
    
    def _create_summary_prompt(self, text: str, summary_type: str) -> str:
        """Create prompt for summary generation."""
        return f'''{self._templates[summary_type]}

        Text: {text}

        Ensure the summary is clear, accurate, and well-structured.'''
