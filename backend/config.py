import os
import re
from pathlib import Path
from typing import List, Optional

# Load .env file if present (so users don't have to export vars manually)
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parent / ".env"
    load_dotenv(dotenv_path=env_path)
except ImportError:
    pass  # python-dotenv not installed; fall back to os.environ only


def get_env(name: str, default: str = "") -> str:
    value = os.getenv(name)
    return value if value is not None else default


def get_env_optional(name: str) -> Optional[str]:
    return os.getenv(name) or None


# Database
DATABASE_URL: str = get_env("DATABASE_URL", "sqlite:///./tn_politics.db")


# Collection settings
COLLECTION_ENABLED: bool = get_env("COLLECTION_ENABLED", "true").lower() == "true"
COLLECTION_INTERVAL_SECONDS: int = int(get_env("COLLECTION_INTERVAL_SECONDS", "60"))  # 1 minute default

# How far back to look for new RSS articles (hours)
RSS_LOOKBACK_HOURS: int = int(get_env("RSS_LOOKBACK_HOURS", "48"))


# --------- News / RSS (no auth required) ----------
NEWS_RSS_FEEDS: List[str] = [
    # VERIFIED WORKING feeds with actual entries
    "https://www.thehindu.com/news/national/tamil-nadu/feeder/default.rss",
    "https://indianexpress.com/section/cities/chennai/feed/",
    "https://www.thehindu.com/news/cities/chennai/feeder/default.rss",
    "https://www.hindustantimes.com/feeds/rss/cities/chennai/rssfeed.xml",
    "https://economictimes.indiatimes.com/rssfeeds/4920533.cms",
]

# Source name lookup for display
RSS_FEED_NAMES: dict = {
    "thehindu.com": "The Hindu",
    "indianexpress.com": "Indian Express",
    "hindustantimes.com": "Hindustan Times",
    "economictimes": "Economic Times",
    "ndtv.com": "NDTV",
    "news18.com": "News18",
    "timesofindia": "Times of India",
}


# --------- X (Twitter) ----------
X_BEARER_TOKEN: Optional[str] = get_env_optional("X_BEARER_TOKEN")
X_SEARCH_QUERIES: List[str] = [
    "Tamil Nadu election",
    "TN elections",
    "DMK OR AIADMK OR BJP OR Congress",
]


# --------- YouTube ----------
YOUTUBE_API_KEY: Optional[str] = get_env_optional("YOUTUBE_API_KEY")
YOUTUBE_SEARCH_QUERIES: List[str] = [
    "Tamil Nadu politics",
    "TN election rally",
]


# --------- Reddit ----------
REDDIT_CLIENT_ID: Optional[str] = get_env_optional("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET: Optional[str] = get_env_optional("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT: str = get_env("REDDIT_USER_AGENT", "tn-politics-monitor/1.0")
REDDIT_SUBREDDITS: List[str] = [
    "TamilNadu",
    "india",
    "Chennai",
]
# Only keep Reddit posts matching at least one of these keywords (case-insensitive)
REDDIT_TN_KEYWORDS: List[str] = [
    "tamil nadu", "tamilnadu", "chennai", "dmk", "aiadmk", "bjp", "congress",
    "election", "politics", "stalin", "annamalai", "edappadi",
    "neet", "cauvery", "kaveri", "dravidian",
    "coimbatore", "madurai", "trichy", "salem",
]


# --------- GNews API (free: 100 req/day) ----------
GNEWS_API_KEY: Optional[str] = get_env_optional("GNEWS_API_KEY")
GNEWS_SEARCH_QUERY: str = "Tamil Nadu politics OR election"
GNEWS_COUNTRY: str = "in"
GNEWS_LANGUAGE: str = "en"


# --------- Facebook / Instagram (placeholders for Graph API) ----------
FACEBOOK_APP_ID: Optional[str] = get_env_optional("FACEBOOK_APP_ID")
FACEBOOK_APP_SECRET: Optional[str] = get_env_optional("FACEBOOK_APP_SECRET")
FACEBOOK_ACCESS_TOKEN: Optional[str] = get_env_optional("FACEBOOK_ACCESS_TOKEN")


# --------- Telegram / WhatsApp (placeholders) ----------
TELEGRAM_BOT_TOKEN: Optional[str] = get_env_optional("TELEGRAM_BOT_TOKEN")
WHATSAPP_ACCESS_TOKEN: Optional[str] = get_env_optional("WHATSAPP_ACCESS_TOKEN")
WHATSAPP_BUSINESS_ID: Optional[str] = get_env_optional("WHATSAPP_BUSINESS_ID")


# Simple keyword-based analysis fallback if external AI is not wired yet
ENABLE_KEYWORD_ANALYSIS: bool = get_env("ENABLE_KEYWORD_ANALYSIS", "true").lower() == "true"
