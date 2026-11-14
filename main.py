import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model

from notifier import send_to_discord
from tools import get_crypto_news, get_top_coins

load_dotenv()

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
- Don't claim one story caused another unless the article says so.
- End with: "Not financial advice."
"""


def today_text() -> str:
    """Today's date in your time zone (servers like GitHub's run on UTC)."""
    tz_name = os.getenv("TIMEZONE")
    now = datetime.now(ZoneInfo(tz_name)) if tz_name else datetime.now()
    return now.strftime("%A, %d %B %Y")


def write_briefing(show_steps: bool = False) -> str:
    """Run the agent and return the finished briefing as plain text."""
    model = init_chat_model(
        # "or" also covers an empty value (GitHub passes "" for a missing variable)
        f"google_genai:{os.getenv('GEMINI_MODEL') or 'gemini-3.5-flash-lite'}",
        temperature=0,
        timeout=90,
        max_retries=2,
    )
    agent = create_agent(
        model=model,
        tools=[get_top_coins, get_crypto_news],
        system_prompt=SYSTEM_PROMPT,
    )
    result = agent.invoke(
        {"messages": [{"role": "user", "content": f"Write tonight's crypto briefing for {today_text()}."}]}
    )
    if show_steps:
        for message in result["messages"]:
            message.pretty_print()
    return result["messages"][-1].text


def main() -> None:
    dry_run = "--dry-run" in sys.argv      # write the briefing but don't send it
    show_steps = "--steps" in sys.argv     # print every step the agent took

    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not dry_run and not webhook_url:
        sys.exit("DISCORD_WEBHOOK_URL is missing. Add it to .env (or use --dry-run).")

    try:
        briefing = write_briefing(show_steps)
    except Exception as error:
        # Tell yourself on Discord that tonight's run failed, then stop with an error.
        if not dry_run:
            send_to_discord(webhook_url, f"⚠️ Tonight's crypto briefing failed: {error}")
        raise

    message = f"📈 **Crypto Briefing: {today_text()}**\n\n{briefing}"
    print(message)

    if dry_run:
        print("\n(dry run: not sent to Discord)")
        return

    send_to_discord(webhook_url, message)
    print("\nSent to Discord ✅")


if __name__ == "__main__":
    main()