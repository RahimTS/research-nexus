from typing import Union
from langchain_openai import ChatOpenAI
from src.utils.config import settings

def create_llm() -> Union[ChatOpenAI, None]:
    """Create the appropriate LLM based on configuration"""
    
    # OpenRouter configuration
    if settings.openrouter_api_key:
        print(f"🌐 Using OpenRouter with model: {settings.llm_model}")
        return ChatOpenAI(
            api_key=settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
            model=settings.llm_model,
            temperature=settings.temperature,
            default_headers={
                "HTTP-Reference": "https://github.com/RahimTS/research-nexus",
                "X-Title": "Research Nexus AI Agent",
            }
        )
    
    else:
        print("⚠️ No OpenRouter API key found, will use fallback analysis")
        return None