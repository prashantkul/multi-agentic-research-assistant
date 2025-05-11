"""Adapter for EmbeddingsDirect to make it LangChain-compatible."""
from typing import List, Optional, Dict, Any, Union
import numpy as np
from langchain.embeddings.base import Embeddings

from src.utils.embeddings_direct import EmbeddingsDirect
from src.config.env import config

class EmbeddingsAdapter(Embeddings):
    """Adapter for EmbeddingsDirect to LangChain's Embeddings interface."""
    
    model_name: str = config.EMBEDDING_MODEL
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed search documents.
        
        Args:
            texts: The list of texts to embed
            
        Returns:
            List of embeddings, one for each text
        """
        try:
            return EmbeddingsDirect.get_embeddings(texts)
        except Exception as e:
            print(f"[ERROR] EmbeddingsAdapter: Error in embed_documents: {e}")
            import traceback
            print(traceback.format_exc())
            raise
    
    def embed_query(self, text: str) -> List[float]:
        """Embed query text.
        
        Args:
            text: The text to embed
            
        Returns:
            Embeddings for the text
        """
        try:
            embeddings = EmbeddingsDirect.get_embeddings([text])
            return embeddings[0]
        except Exception as e:
            print(f"[ERROR] EmbeddingsAdapter: Error in embed_query: {e}")
            import traceback
            print(traceback.format_exc())
            raise

def get_langchain_compatible_embeddings():
    """Get a LangChain-compatible embeddings model."""
    return EmbeddingsAdapter()