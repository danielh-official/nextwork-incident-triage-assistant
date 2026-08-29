from anthropic import Anthropic
from app.config import Settings

# Load settings from .env
settings = Settings()
# Create an Anthropic client with your API key
client = Anthropic(api_key=settings.anthropic_api_key)
# Send a simple test message to Claude
message = client.messages.create(
    model=settings.model_name,
    max_tokens=256,
    messages=[{"role": "user", "content": "Say hello!"}],
)
# Print Claude's response
print(message.content[0].text)