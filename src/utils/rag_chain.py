"""RAG chain utility for the domain expert agent."""
import os
from typing import List, Dict, Any, Optional
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable

from src.utils.vector_store import VectorStore
from src.utils.gemini_llm import GeminiLLM

class RAGChain:
    """RAG chain for domain expert agent."""
    
    def __init__(self, vector_store: Optional[VectorStore] = None):
        """Initialize RAG chain.
        
        Args:
            vector_store: Optional vector store instance
        """
        self.vector_store = vector_store or VectorStore()
        self.llm = GeminiLLM.get_llm()
        self.chain = self._create_rag_chain()
    
    def _create_rag_chain(self) -> Runnable:
        """Create RAG chain.
        
        Returns:
            RAG chain
        """
        # Define prompt template
        prompt = ChatPromptTemplate.from_template("""
        You are a healthcare domain expert with knowledge of generative AI applications.
        Use the following retrieved scientific papers to provide expert insights.
        
        Context from retrieved papers:
        {context}
        
        Question: {input}
        
        Provide your expert insights, and specifically cite the papers you're
        referencing. When possible, mention the authors, publication year, and title
        of the paper you're referring to in your response.
        """)
        
        # Create document chain
        document_chain = create_stuff_documents_chain(self.llm, prompt)
        
        # Create retrieval chain
        retriever = self.vector_store.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 5}
        )
        return create_retrieval_chain(retriever, document_chain)
    
    def query(self, query: str) -> Dict[str, Any]:
        """Query the RAG chain.
        
        Args:
            query: Query string
            
        Returns:
            Response from the RAG chain
        """
        return self.chain.invoke({"input": query})
    
    def get_citations(self, query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """Get citations for a query.
        
        Args:
            query: Query string
            max_results: Maximum number of citations to return
            
        Returns:
            List of citations
        """
        results = self.vector_store.similarity_search(query, k=max_results)
        
        citations = []
        for result in results:
            metadata = result["metadata"]
            citation = {
                "excerpt": result["content"][:150] + "...",
                "source": metadata.get("source", "Unknown"),
                "page": metadata.get("page", "Unknown"),
                "title": metadata.get("title", os.path.basename(metadata.get("source", "Unknown paper"))),
                "authors": metadata.get("authors", "Unknown")
            }
            citations.append(citation)
        
        return citations