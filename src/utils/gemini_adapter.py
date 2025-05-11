"""Adapter for GeminiDirect to make it LangChain-compatible for CrewAI."""
from typing import Any, List, Optional, Dict, Union
from langchain.schema.language_model import LanguageModelInput
from langchain.schema.output import Generation, LLMResult
from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.llms.base import LLM

from src.utils.gemini_direct import GeminiDirect
from src.config.env import config

class GeminiAdapter(LLM):
    """Adapter for GeminiDirect to LangChain's LLM interface for CrewAI compatibility."""
    
    model_name: str = config.MODEL_NAME
    temperature: float = config.TEMPERATURE
    max_tokens: int = config.MAX_TOKENS
    
    @property
    def _llm_type(self) -> str:
        return "gemini-adapter"
    
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """Call GeminiDirect generate_text and return the output."""
        try:
            history = kwargs.get("history", None)
            return GeminiDirect.generate_text(prompt, history=history)
        except Exception as e:
            print(f"[ERROR] GeminiAdapter: Error in _call: {e}")
            import traceback
            print(traceback.format_exc())
            raise
    
    def _generate(
        self,
        prompts: List[str],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> LLMResult:
        """Generate text for multiple prompts."""
        generations = []
        for prompt in prompts:
            text = self._call(prompt, stop=stop, run_manager=run_manager, **kwargs)
            generations.append([Generation(text=text)])
        return LLMResult(generations=generations)
    
    def get_num_tokens(self, text: str) -> int:
        """Get the number of tokens in a text string."""
        # A very rough estimation for Gemini models
        # This is a placeholder - actual token counting is more complex
        return len(text.split())

def get_langchain_compatible_llm():
    """Get a LangChain-compatible LLM for CrewAI using our direct implementation."""
    return GeminiAdapter()