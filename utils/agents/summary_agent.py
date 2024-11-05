from .base_agent import BaseAgent
import os
from openai import AzureOpenAI

class SummaryAgent(BaseAgent):
    """Agent responsible for document summarization operations."""
    
    def __init__(self):
        super().__init__("Summary Agent")
        self._initialize_azure_client()
        
        self.summary_templates = {
            "concise": "Please provide a brief summary of the following text in 2-3 sentences:",
            "detailed": "Please provide a comprehensive summary of the following text, including main points and key details:",
            "bullet_points": "Please summarize the following text in a bullet-point format, highlighting the key points:"
        }
    
    def _initialize_azure_client(self):
        """Initialize Azure OpenAI client."""
        azure_api_key = os.environ.get("AZURE_OPENAI_API_KEY")
        azure_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
        
        if not azure_api_key or not azure_endpoint:
            raise ValueError("Azure OpenAI API key or endpoint is not set")
        
        self.client = AzureOpenAI(
            api_key=azure_api_key,
            api_version="2023-05-15",
            azure_endpoint=azure_endpoint
        )
        self.deployment_name = os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4")
    
    async def process(self, text: str, summary_type: str = "concise") -> dict:
        """Generate summary of the provided text."""
        try:
            if summary_type not in self.summary_templates:
                summary_type = "concise"
            
            prompt = self._create_summary_prompt(text, summary_type)
            summary = await self._get_completion(prompt)
            
            return {
                "success": True,
                "summary": summary,
                "metadata": {
                    "type": summary_type,
                    "model": self.deployment_name
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
        return f"""{self.summary_templates[summary_type]}

        Text: {text}

        Ensure the summary is clear, accurate, and well-structured."""
    
    async def _get_completion(self, prompt: str) -> str:
        """Get completion from Azure OpenAI."""
        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                temperature=0.0,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            self.log_action("Completion error", str(e))
            raise
