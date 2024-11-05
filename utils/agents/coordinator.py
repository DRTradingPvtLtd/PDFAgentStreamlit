from .pdf_agent import PDFAgent
from .qa_agent import QAAgent
from .summary_agent import SummaryAgent

class AgentCoordinator:
    """Coordinates the actions of different agents in the system."""
    
    def __init__(self):
        self.pdf_agent = PDFAgent()
        self.qa_agent = QAAgent()
        self.summary_agent = SummaryAgent()
    
    async def process_pdf(self, pdf_file):
        """Process PDF file using PDF agent."""
        return await self.pdf_agent.process(pdf_file)
    
    async def get_answer(self, context: str, question: str):
        """Get answer using QA agent."""
        return await self.qa_agent.process(context, question)
    
    async def generate_summary(self, text: str, summary_type: str = "concise"):
        """Generate summary using Summary agent."""
        return await self.summary_agent.process(text, summary_type)
