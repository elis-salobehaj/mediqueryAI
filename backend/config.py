from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    # App Config
    log_level: str = "DEBUG"
    chat_history_retention_hours: int = 24
    
    # Auth
    jwt_secret_key: str = "supersecretkey"  # Use proper secret in prod
    
    # Provider Selection (Priority: Bedrock > Gemini > Anthropic > Local)
    use_bedrock: bool = False
    use_gemini: bool = False
    use_anthropic: bool = False
    use_local_model: bool = False
    
    # Credentials
    gemini_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    
    # AWS Bedrock
    aws_bedrock_region: str = "us-west-2"
    aws_bearer_token_bedrock: Optional[str] = None
    bedrock_base_model: str = "global.anthropic.claude-haiku-4-5-20251001-v1:0"
    bedrock_sql_writer_model: str = "global.anthropic.claude-haiku-4-5-20251001-v1:0"
    bedrock_navigator_model: str = "global.anthropic.claude-haiku-4-5-20251001-v1:0"
    bedrock_critic_model: str = "global.anthropic.claude-haiku-4-5-20251001-v1:0"
    
    # Gemini Models
    gemini_base_model: str = "gemini-1.5-flash"
    gemini_sql_writer_model: str = "gemini-1.5-pro"
    gemini_navigator_model: str = "gemini-1.5-flash"
    gemini_critic_model: str = "gemini-1.5-flash"
    
    # Anthropic Models (Direct API)
    anthropic_base_model: str = "claude-3-5-sonnet-20241022"
    anthropic_sql_writer_model: str = "claude-3-5-sonnet-20241022"
    anthropic_navigator_model: str = "claude-3-5-haiku-20241022"
    anthropic_critic_model: str = "claude-3-5-haiku-20241022"
    
    # Local Models (Ollama)
    local_base_model: str = "qwen3:latest"
    local_sql_writer_model: str = "sqlcoder:7b"
    local_navigator_model: str = "qwen2.5-coder:7b"
    local_critic_model: str = "llama3.1"
    local_model_name: str = "qwen3:latest"  # Legacy compatibility
    ollama_host: str = "http://localhost:11434"
    
    # Default UI Toggle Settings
    default_multi_agent: bool = True
    default_fast_mode: bool = False  # False = thinking mode enabled

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    # Computed Properties - Single Source of Truth
    @property
    def active_provider(self) -> str:
        """Returns active provider based on priority: Bedrock > Gemini > Anthropic > Local"""
        if self.use_bedrock:
            return "bedrock"
        if self.use_gemini:
            return "gemini"
        if self.use_anthropic:
            return "anthropic"
        if self.use_local_model:
            return "local"
        return "gemini"  # Default fallback
    
    @property
    def base_model(self) -> str:
        """Returns base model for active provider"""
        provider = self.active_provider
        return getattr(self, f"{provider}_base_model")
    
    @property
    def sql_writer_model(self) -> str:
        """Returns SQL writer model for active provider"""
        provider = self.active_provider
        return getattr(self, f"{provider}_sql_writer_model")
    
    @property
    def navigator_model(self) -> str:
        """Returns navigator model for active provider"""
        provider = self.active_provider
        return getattr(self, f"{provider}_navigator_model")
    
    @property
    def critic_model(self) -> str:
        """Returns critic model for active provider"""
        provider = self.active_provider
        return getattr(self, f"{provider}_critic_model")

@lru_cache
def get_settings():
    return Settings()

settings = get_settings()
