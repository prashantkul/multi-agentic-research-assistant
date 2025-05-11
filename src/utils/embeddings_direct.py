"""Direct embeddings utility using Vertex AI SDK without LangChain."""
from google.cloud import aiplatform
from vertexai.language_models import TextEmbeddingModel
from src.config.env import config

class EmbeddingsDirect:
    """Direct implementation of text embeddings using Vertex AI."""
    
    _instance = None
    
    @classmethod
    def initialize(cls):
        """Initialize the Vertex AI platform."""
        print(f"\n[DEBUG] EmbeddingsDirect: Initializing Vertex AI platform")
        print(f"[DEBUG] EmbeddingsDirect: Project ID = {config.GOOGLE_PROJECT_ID}")
        print(f"[DEBUG] EmbeddingsDirect: Region = {config.GOOGLE_REGION}")
        try:
            aiplatform.init(
                project=config.GOOGLE_PROJECT_ID,
                location=config.GOOGLE_REGION,
            )
            print(f"[DEBUG] EmbeddingsDirect: Successfully initialized Vertex AI platform")
            return True
        except Exception as e:
            print(f"[ERROR] EmbeddingsDirect: Failed to initialize Vertex AI platform: {e}")
            import traceback
            print(f"[ERROR] EmbeddingsDirect: {traceback.format_exc()}")
            return False
    
    @classmethod
    def get_model(cls):
        """Get or create a TextEmbeddingModel instance."""
        if cls._instance is None:
            cls.initialize()
            print(f"[DEBUG] EmbeddingsDirect: Creating TextEmbeddingModel with model={config.EMBEDDING_MODEL}")
            try:
                cls._instance = TextEmbeddingModel.from_pretrained(config.EMBEDDING_MODEL)
                print(f"[DEBUG] EmbeddingsDirect: Successfully created TextEmbeddingModel")
            except Exception as e:
                print(f"[ERROR] EmbeddingsDirect: Failed to create TextEmbeddingModel: {e}")
                import traceback
                print(f"[ERROR] EmbeddingsDirect: {traceback.format_exc()}")
                raise
        return cls._instance
    
    @classmethod
    def get_embeddings(cls, texts):
        """Get embeddings for a list of texts.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors
        """
        model = cls.get_model()
        print(f"[DEBUG] EmbeddingsDirect: Getting embeddings for {len(texts)} texts")
        try:
            embeddings = []
            # Process in batches of 5 to avoid rate limits
            batch_size = 5
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i+batch_size]
                batch_embeddings = model.get_embeddings(batch)
                for emb in batch_embeddings:
                    embeddings.append(emb.values)
                print(f"[DEBUG] EmbeddingsDirect: Processed batch {i//batch_size+1}/{(len(texts)-1)//batch_size+1}")
            
            print(f"[DEBUG] EmbeddingsDirect: Successfully got embeddings")
            return embeddings
        except Exception as e:
            print(f"[ERROR] EmbeddingsDirect: Failed to get embeddings: {e}")
            import traceback
            print(f"[ERROR] EmbeddingsDirect: {traceback.format_exc()}")
            raise