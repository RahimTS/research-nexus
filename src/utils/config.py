import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Settings:
    # App Settings
    app_name: str = os.getenv("APP_NAME", "research-nexus")
    debug_mode: bool = os.getenv("DEBUG_MODE", "true").lower() == "true"
    env: str = os.getenv("ENV", "local")
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    
    # API Keys
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "")
    tavily_api_key: str = os.getenv("TAVILY_API_KEY", "")
    
    # Database
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./research_agent.db")
    
    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Research Settings
    max_search_results: int = int(os.getenv("MAX_SEARCH_RESULTS", "5"))
    max_research_steps: int = int(os.getenv("MAX_RESEARCH_STEPS", "3"))
    
    # Model Settings - OpenRouter models
    llm_model: str = os.getenv("LLM_MODEL", "anthropic/claude-3-haiku")  # OpenRouter format
    temperature: float = float(os.getenv("TEMPERATURE", "0.1"))

settings = Settings()