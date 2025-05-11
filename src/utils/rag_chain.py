"""RAG chain utility for the domain expert agent using Vertex AI."""
import os
from typing import List, Dict, Any, Optional
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.prompts.chat import ChatPromptTemplate
from langchain.schema.runnable import Runnable

from src.utils.vector_store import VectorStore
from src.utils.gemini_adapter import get_langchain_compatible_llm

class RAGChain:
    """RAG chain for domain expert agent using Vertex AI."""
    
    def __init__(self, vector_store: Optional[VectorStore] = None):
        """Initialize RAG chain.

        Args:
            vector_store: Optional vector store instance
        """
        print(f"\n[DEBUG] RAGChain: Initializing RAG Chain")
        try:
            print(f"[DEBUG] RAGChain: Creating/loading vector store")
            self.vector_store = vector_store or VectorStore()
            print(f"[DEBUG] RAGChain: Successfully created/loaded vector store")
        except Exception as e:
            print(f"[ERROR] RAGChain: Failed to create/load vector store: {e}")
            print(f"[ERROR] RAGChain: Error type: {type(e).__name__}")
            import traceback
            print(f"[ERROR] RAGChain: {traceback.format_exc()}")
            raise

        try:
            print(f"[DEBUG] RAGChain: Getting LangChain-compatible LLM")
            self.llm = get_langchain_compatible_llm()
            print(f"[DEBUG] RAGChain: Successfully got LLM instance")
        except Exception as e:
            print(f"[ERROR] RAGChain: Failed to get LLM instance: {e}")
            print(f"[ERROR] RAGChain: Error type: {type(e).__name__}")
            import traceback
            print(f"[ERROR] RAGChain: {traceback.format_exc()}")
            raise

        try:
            print(f"[DEBUG] RAGChain: Creating retrieval chain")
            self.chain = self._create_rag_chain()
            print(f"[DEBUG] RAGChain: Successfully created retrieval chain")
        except Exception as e:
            print(f"[ERROR] RAGChain: Failed to create retrieval chain: {e}")
            print(f"[ERROR] RAGChain: Error type: {type(e).__name__}")
            import traceback
            print(f"[ERROR] RAGChain: {traceback.format_exc()}")
            raise
    
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
        try:
            response = self.chain.invoke({"input": query})
            return response
        except Exception as e:
            print(f"Error querying RAG chain: {e}")
            import traceback
            print(traceback.format_exc())
            # Return a fallback response
            return {
                "answer": f"I was unable to find specific information on that topic in the academic literature. The RAG system encountered an error: {str(e)}. Please try a different query or reformulate your question.",
                "input": query
            }
    
    def get_citations(self, query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """Get citations for a query.

        Args:
            query: Query string
            max_results: Maximum number of citations to return

        Returns:
            List of citations
        """
        try:
            results = self.vector_store.similarity_search(query, k=max_results)

            citations = []
            if not results:
                print(f"No results found for query: {query}")
                return citations

            for result in results:
                if not result or "metadata" not in result:
                    continue

                metadata = result["metadata"]
                content = result.get("content", "")
                excerpt = content[:150] + "..." if content else "No content available"

                citation = {
                    "excerpt": excerpt,
                    "source": metadata.get("source", "Unknown"),
                    "page": metadata.get("page", "Unknown"),
                    "title": metadata.get("title", os.path.basename(metadata.get("source", "Unknown paper"))),
                    "authors": metadata.get("authors", "Unknown")
                }
                citations.append(citation)

            return citations
        except Exception as e:
            print(f"Error getting citations: {e}")
            import traceback
            print(traceback.format_exc())
            return [{"excerpt": "Error retrieving citations", "source": "Error", "title": f"Error: {str(e)}"}]