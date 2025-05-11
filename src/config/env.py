"""Environment configuration module."""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration class for environment variables."""

    # Google Cloud and Vertex AI configurations
    GOOGLE_PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID")
    GOOGLE_REGION = os.getenv("GOOGLE_REGION", "us-central1")
    MODEL_NAME = os.getenv("MODEL_NAME", "gemini-2.5-pro-preview-05-06")
    # For Vertex AI embeddings, use the model name without the "models/" prefix
    raw_embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-004")
    EMBEDDING_MODEL = raw_embedding_model.replace("models/", "") if raw_embedding_model.startswith("models/") else raw_embedding_model
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", "8192"))

    @classmethod
    def validate(cls):
        """Validate required environment variables."""
        print("\n[DEBUG] Config: Validating environment variables")

        if not cls.GOOGLE_PROJECT_ID:
            print("[ERROR] Config: GOOGLE_PROJECT_ID environment variable is missing")
            raise ValueError("GOOGLE_PROJECT_ID environment variable is required")
        else:
            print(f"[DEBUG] Config: GOOGLE_PROJECT_ID = {cls.GOOGLE_PROJECT_ID}")

        print(f"[DEBUG] Config: GOOGLE_REGION = {cls.GOOGLE_REGION}")
        print(f"[DEBUG] Config: MODEL_NAME = {cls.MODEL_NAME}")
        print(f"[DEBUG] Config: EMBEDDING_MODEL = {cls.EMBEDDING_MODEL}")

        # Check authentication methods
        if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            print(f"[DEBUG] Config: Found GOOGLE_APPLICATION_CREDENTIALS: {creds_path}")
            if not os.path.exists(creds_path):
                print(f"[ERROR] Config: Service account key file not found: {creds_path}")
            else:
                print(f"[DEBUG] Config: Service account key file exists")
        else:
            print("[DEBUG] Config: GOOGLE_APPLICATION_CREDENTIALS not set")

        gcloud_path = os.path.expanduser("~/.config/gcloud")
        adc_path = os.path.expanduser("~/.config/gcloud/application_default_credentials.json")

        if os.path.exists(gcloud_path):
            print(f"[DEBUG] Config: Found gcloud credentials directory at {gcloud_path}")
            if os.path.exists(adc_path):
                print(f"[DEBUG] Config: Found application default credentials at {adc_path}")
            else:
                print(f"[WARNING] Config: No application default credentials found at {adc_path}")
        else:
            print(f"[DEBUG] Config: No gcloud credentials directory found at {gcloud_path}")

        # Show warning if no authentication method is available
        if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS") and not os.path.exists(adc_path):
            print("[WARNING] Config: Neither GOOGLE_APPLICATION_CREDENTIALS nor gcloud application default credentials detected.")
            print("[WARNING] Config: Please ensure you've authenticated with Google Cloud using:")
            print("[WARNING] Config:   gcloud auth application-default login")
            print("[WARNING] Config: or by setting GOOGLE_APPLICATION_CREDENTIALS to point to a service account key file.")

# Singleton instance
config = Config()