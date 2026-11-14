import os

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

from tools import get_crypto_news, get_top_coins

load_dotenv()

model = init_chat_model(
    f"google_genai:{os.getenv('GEMINI_MODEL', 'gemini-3.5-flash-lite')}",
    temperature=0,
    timeout=60,
    max_retries=1,
)

print("Tool name: ", get_top_coins.name)
print("Description: ", get_top_coins.description)
print("Inputs: ", get_top_coins.args)
print("-" * 60)

model_with_tools = model.bind_tools([get_top_coins, get_crypto_news])

response = model_with_tools.invoke("What's the price of the Bitcoin right now?")

print("Text reply: ", repr(response.text))
print("Tool calls: ", response.tool_calls)
