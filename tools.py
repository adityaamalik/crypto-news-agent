import calendar
import html
import re

import feedparser
import requests
from langchain.tools import tool

NEWS_FEEDS = {
    "CoinDesk": "https://www.coindesk.com/arc/outboundfeeds/rss/?outputType=xml",
    "Cointelegraph": "https://cointelegraph.com/rss",
    "Decrypt": "https://decrypt.co/feed",
}

HEADERS = {"User-Agent": "Mozilla/5.0 (crypto-news-agent learning project)"}

def _clean(text: str, max_len: int = 300) -> str:
    """Remove HTML tags and extra spaces, then shorten the text."""
    text = html.unescape(text or "")
    text = re.sub(r"<[^>]+>", " ", text)
    text = " ".join(text.split())
    return text[:max_len] + ("..." if len(text) > max_len else "")

@tool(parse_docstring=True)
def get_crypto_news(max_articles: int = 25) -> str:
    """Fetch the latest crypto news from the top 3 news sources.
    
    Returns recent articles, newest first, each with source, publish time,
    title, a short summary and a link. Use this to find today's crypto news.
    
    Args:
        max_articles: How many articles to return in total (default 25).
    """
    articles = []
    errors = []

    for source, url in NEWS_FEEDS.items():
        try:
            response = requests.get(url, headers=HEADERS, timeout=15)
            response.raise_for_status()
            feed = feedparser.parse(response.content)
            for entry in feed.entries[:max_articles]:
                published_parsed = entry.get("published_parsed") or entry.get("updated_parsed")
                articles.append({
                    "source": source,
                    "title": _clean(entry.get("title", ""), 200),
                    "summary": _clean(entry.get("summary", "")),
                    "link": entry.get("link", ""),
                    "published": entry.get("published", "unknown time"),
                    "timestamp": calendar.timegm(published_parsed) if published_parsed else 0,
                })
        except Exception as error:
            errors.append(f"{source}: {error}")

    if not articles:
        return "Could not fetch any news. Errors: " + "; ".join(errors)

    articles.sort(key=lambda a: a["timestamp"], reverse=True)

    lines = []
    for i, a in enumerate(articles[:max_articles], start=1):
        lines.append(
            f"{i}. {a['source']} - {a['title']}\n"
            f"Published: {a['published']}\n"
            f"Summary: {a['summary']}\n"
            f"Link: {a['link']}"
        )

    if errors:
        lines.append("\nSome sources failed to fetch: " + "; ".join(errors))

    return "\n\n".join(lines)

@tool(parse_docstring=True)
def get_top_coins(limit: int = 10) -> str:
    """Get live prices for the top cryptocurrencies by market cap from CoinGecko.

    Returns each coin's rank, name, symbol, price in USD and 24-hour price change.
    Use this to give a market snapshot alongside the news.

    Args:
        limit: How many top coins to return (default 10, max 50).
    """
    limit = max(1, min(limit, 50))
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": limit,
        "page": 1,
    }

    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=15)
        response.raise_for_status()
        coins = response.json()
        
    except Exception as error:
        return f"Could not fetch prices from CoinGecko: {error}"

    lines = []
    for coin in coins:
        # .get(key, 0) only substitutes the default when the key is missing.
        # CoinGecko sometimes includes the key with a null value.
        change = coin.get("price_change_percentage_24h")
        price = coin.get("current_price")
        price_text = f"${price:,}" if isinstance(price, (int, float)) else "price n/a"
        change_text = f"{change:+.2f}%" if isinstance(change, (int, float)) else "change n/a"
        lines.append(
            f"{coin.get('market_cap_rank')}. {coin['name']} ({coin['symbol'].upper()}): "
            f"{price_text} ({change_text} in 24h)"
        )

    return "\n".join(lines)

if __name__ == "__main__":
    print(get_top_coins.invoke({"limit": 5}))
    print()
    print(get_crypto_news.invoke({"max_articles": 5}))