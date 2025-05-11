"""Direct Gemini utility module using Vertex AI SDK without LangChain."""
from google.cloud import aiplatform
from vertexai.generative_models import GenerativeModel, GenerationConfig
from src.config.env import config

class GeminiDirect:
    """Direct Vertex AI Gemini implementation without LangChain."""
    
    @staticmethod
    def initialize():
        """Initialize the Vertex AI platform."""
        print(f"\n[DEBUG] GeminiDirect: Initializing Vertex AI platform")
        print(f"[DEBUG] GeminiDirect: Project ID = {config.GOOGLE_PROJECT_ID}")
        print(f"[DEBUG] GeminiDirect: Region = {config.GOOGLE_REGION}")
        try:
            aiplatform.init(
                project=config.GOOGLE_PROJECT_ID,
                location=config.GOOGLE_REGION,
            )
            print(f"[DEBUG] GeminiDirect: Successfully initialized Vertex AI platform")
            return True
        except Exception as e:
            print(f"[ERROR] GeminiDirect: Failed to initialize Vertex AI platform: {e}")
            import traceback
            print(f"[ERROR] GeminiDirect: {traceback.format_exc()}")
            return False
    
    @staticmethod
    def get_model():
        """Get a GenerativeModel instance for Gemini."""
        GeminiDirect.initialize()
        
        print(f"[DEBUG] GeminiDirect: Creating GenerativeModel with model={config.MODEL_NAME}")
        try:
            model = GenerativeModel(config.MODEL_NAME)
            print(f"[DEBUG] GeminiDirect: Successfully created GenerativeModel")
            return model
        except Exception as e:
            print(f"[ERROR] GeminiDirect: Failed to create GenerativeModel: {e}")
            import traceback
            print(f"[ERROR] GeminiDirect: {traceback.format_exc()}")
            raise
    
    @staticmethod
    def get_generation_config():
        """Get a GenerationConfig instance based on environment config."""
        return GenerationConfig(
            temperature=config.TEMPERATURE,
            max_output_tokens=config.MAX_TOKENS,
            top_p=0.95,
            top_k=40,
        )
    
    @staticmethod
    def generate_text(prompt, history=None):
        """Generate text response for a prompt.
        
        Args:
            prompt: The text prompt to generate a response for
            history: Optional conversation history
            
        Returns:
            The generated text response
        """
        model = GeminiDirect.get_model()
        generation_config = GeminiDirect.get_generation_config()
        
        print(f"[DEBUG] GeminiDirect: Generating content for prompt: {prompt[:50]}...")
        try:
            if history:
                response = model.generate_content(
                    history + [prompt],
                    generation_config=generation_config,
                )
            else:
                response = model.generate_content(
                    prompt,
                    generation_config=generation_config,
                )
            
            print(f"[DEBUG] GeminiDirect: Successfully generated content")
            return response.text
        except Exception as e:
            print(f"[ERROR] GeminiDirect: Failed to generate content: {e}")
            import traceback
            print(f"[ERROR] GeminiDirect: {traceback.format_exc()}")
            raise