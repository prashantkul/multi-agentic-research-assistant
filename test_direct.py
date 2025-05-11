#!/usr/bin/env python3
"""Test script for direct Vertex AI integration."""
import os
import sys
from src.config.env import config
from src.utils.gemini_direct import GeminiDirect
from src.utils.embeddings_direct import EmbeddingsDirect

def test_vertex_direct():
    """Test direct Vertex AI implementation."""
    print("\n========== TESTING DIRECT VERTEX AI IMPLEMENTATION ==========")
    config.validate()
    
    # Test text generation
    try:
        print("\n---------- Testing Direct Text Generation ----------")
        response = GeminiDirect.generate_text("Hello, can you explain what Vertex AI is in one paragraph?")
        print(f"Response: {response}")
        print("✅ Direct text generation successful!")
    except Exception as e:
        print(f"❌ Error with direct text generation: {e}")
        import traceback
        print(traceback.format_exc())
    
    # Test text embeddings
    try:
        print("\n---------- Testing Direct Text Embeddings ----------")
        texts = ["This is a test sentence.", "Another test sentence for embeddings."]
        embeddings = EmbeddingsDirect.get_embeddings(texts)
        print(f"Generated {len(embeddings)} embeddings")
        print(f"First embedding dimensions: {len(embeddings[0])}")
        print("✅ Direct text embeddings successful!")
    except Exception as e:
        print(f"❌ Error with direct text embeddings: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    test_vertex_direct()