import re
from typing import Tuple, Optional

TOKEN_PATTERN_ANCHORED = re.compile(r"^\d+:[A-Za-z0-9_-]{35,}$")
TOKEN_PATTERN_UNANCHORED = re.compile(r"\d+:[A-Za-z0-9_-]{35,}")

def validate_bot_token(token: str) -> bool:
    if not token or not isinstance(token, str):
        return False
    return bool(TOKEN_PATTERN_ANCHORED.match(token.strip()))

def mask_token(token: str) -> str:
    if not token or not isinstance(token, str):
        return "***"
    parts = token.strip().split(":", 1)
    if len(parts) == 2:
        bot_id, secret = parts
        masked_secret = secret[:4] + "..." + secret[-4:] if len(secret) > 8 else "..."
        return f"{bot_id}:{masked_secret}"
    return token[:4] + "..." + token[-4:] if len(token) > 8 else "..."

def sanitize_text(text: str) -> str:
    """Removes any potential bot token patterns from text output or error messages."""
    if not text or not isinstance(text, str):
        return ""
    return TOKEN_PATTERN_UNANCHORED.sub("[REDACTED_TOKEN]", text)
