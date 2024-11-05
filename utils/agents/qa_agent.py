from .base_agent import BaseAgent
import os

class QAAgent(BaseAgent):
    """Agent responsible for question answering operations."""
    
    def __init__(self):
        super().__init__("Q&A Agent")
    
    async def process(self, context: str, question: str) -> dict:
        """Process a question and generate an answer."""
        try:
            prompt = self._create_qa_prompt(context, question)
            self.add_message("user", prompt)
            
            messages = self.get_messages()
            response = await self.llm.chat(messages=messages)
            answer = response.content
            
            self.add_message("assistant", answer)
            
            return {
                "success": True,
                "answer": answer,
                "metadata": {
                    "model": os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4"),
                    "question": question
                }
            }
        except Exception as e:
            self.log_action("Error", str(e))
            return {
                "success": False,
                "error": str(e)
            }
    
    def _create_qa_prompt(self, context: str, question: str) -> str:
        """Create prompt for Q&A."""
        return f"""
        Context: {context}
        
        Question: {question}
        
        Please provide a concise and accurate answer based on the context above.
        If the answer cannot be found in the context, please say "I cannot find the answer in the provided text."
        """
