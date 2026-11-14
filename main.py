import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

load_dotenv()

model_name = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

model = init_chat_model(
    f"google_genai:{model_name}",
    temperature=0,
    # Gemini 3.8 Flash reasons before it answers. Its default thinking level
    # is "medium", which often runs past a short deadline and comes back as
    # 504 DEADLINE_EXCEEDED. "low" is the fastest level this model accepts.
    timeout=120,
    max_retries=2,
)

messages = [
	("system", "You are a concise crypto market analyst. Answer in 2 sentences max."),
	("user", "What is Bitcoin, and why does its price move so much?"),
]
print(f"Calling {model_name}...", flush=True)
response = model.invoke(messages)
print(response.text)
