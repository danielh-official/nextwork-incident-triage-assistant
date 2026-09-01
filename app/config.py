from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Required: loaded from ANTHROPIC_API_KEY in .env
    anthropic_api_key: str
    # Claude model to use for triage analysis
    model_name: str = "claude-haiku-4-5"
    # Max tokens for Claude's response
    max_tokens: int = 1024
    # Timeout in seconds for Claude API calls
    claude_timeout: float = 30.0
    # Logging level
    log_level: str = "INFO"

    # Tell pydantic-settings to read from a .env file
    model_config = {"env_file": ".env"}
