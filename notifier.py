import requests

DISCORD_LIMIT = 2000

def split_message(text: str, limit: int = DISCORD_LIMIT) -> list[str]:
    """Split text into chunks that fit in one discord message, breaking between lines."""
    chunks = []
    current = ""
    for line in text.splitlines(keepends=True):
        # A single line longer than the limit gets cut into pieces.
        while len(line) > limit:
            if current:
                chunks.append(current)
                current = ""
            chunks.append(line[:limit])
            line = line[limit:]
        if len(current) + len(line) > limit:
            chunks.append(current)
            current = ""
        current += line
    if current.strip():
        chunks.append(current)
    
    return chunks

def send_to_discord(webhook_url: str, text: str) -> None:
    """Send a message to a discord webhook."""
    for chunk in split_message(text):
        response = requests.post(
            webhook_url, 
            json={
                "content": chunk,
                "username": "Crypto Briefing Bot",
                "allowed_mentions": {"parse": []},
            },
            timeout=15,
        )
        response.raise_for_status()