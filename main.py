import os
from datetime import datetime

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model

from tools import get_crypto_news, get_top_coins

load_dotenv()

SHOW_STEPS = True

model = init_chat_model(
    f"google_genai:{os.getenv('GEMINI_MODEL', 'gemini-3.5-flash-lite')}",
    temperature=0,
    timeout=60,
    max_retries=1,
)

SYSTEM_PROMPT = """You are a crypto market analyst who writes a short nightly news briefing.

How to work:
1. Call get_top_coins to get a market snapshot.
2. Call get_crypto_news to get the latest headlines.
3. Choose the 10 stories that matter most for the overall crypto market
   (big price moves, regulation, ETFs, major companies, hacks, macro news).
   If several sources cover the same story, include it only once.

How to write the briefing:
- Start with one line: BTC and ETH price with 24h change, plus the biggest mover in the top 10.
- Then a numbered list of 10 stories, each as: **Headline**: one sentence on why it matters. (Source)
- Keep the whole briefing under 1800 characters.
- Only use facts from the tool results. Never invent prices or news.
- End with: "Not financial advice."
"""

agent = create_agent(
    model=model,
    tools=[get_top_coins, get_crypto_news],
    system_prompt=SYSTEM_PROMPT,
)

today = datetime.now().strftime("%A, %d %B %Y")

result = agent.invoke(
    {"messages": [{"role": "user", "content": f"Write tonight's crypto briefing for {today}."}]}
)

if SHOW_STEPS:
    for message in result["messages"]:
        message.pretty_print()

else:
    print(result["messages"][-1].content)

