import hashlib
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Iterable, List

import feedparser
import httpx
from sqlalchemy.orm import Session

from config import (
    NEWS_RSS_FEEDS,
    RSS_FEED_NAMES,
    RSS_LOOKBACK_HOURS,
    ENABLE_KEYWORD_ANALYSIS,
    X_BEARER_TOKEN,
    X_SEARCH_QUERIES,
    YOUTUBE_API_KEY,
    YOUTUBE_SEARCH_QUERIES,
    REDDIT_CLIENT_ID,
    REDDIT_CLIENT_SECRET,
    REDDIT_USER_AGENT,
    REDDIT_SUBREDDITS,
    REDDIT_TN_KEYWORDS,
    GNEWS_API_KEY,
    GNEWS_SEARCH_QUERY,
    GNEWS_COUNTRY,
    GNEWS_LANGUAGE,
)
from database import SessionLocal
from models import Post, AnalyzedPost, Alert, Keyword

logger = logging.getLogger("tn_collector")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    ))
    logger.addHandler(handler)


# ---------------------------------------------------------------------------
#  Helpers
# ---------------------------------------------------------------------------

def _now_utc() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _make_post_id(prefix: str, unique_str: str) -> str:
    digest = hashlib.sha256(unique_str.encode("utf-8")).hexdigest()[:32]
    return f"{prefix}_{digest}"


def _get_rss_source_name(feed_url: str) -> str:
    """Extract a human-readable source name from a feed URL."""
    for key, name in RSS_FEED_NAMES.items():
        if key in feed_url.lower():
            return name
    return "News"


# ---------------------------------------------------------------------------
#  IMPROVED keyword analysis — much less aggressive than before
# ---------------------------------------------------------------------------

# Words that indicate REAL political threats (whole-word match only)
_THREAT_PATTERNS = [
    # English
    r"\bkill\s+(him|her|them|the|this|that|all)\b",
    r"\bbomb\s+(the|this|that|a)\b",
    r"\b(murder|assassinat|lynching|stone\s*pelt)\b",
    r"\b(death\s+threat|threaten\s+to\s+kill)\b",
    r"\b(riot|rioting|arson|burn\s+down)\b",
    r"\b(attack\s+on|violent\s+protest)\b",
    # Tamil
    r"கொலை\s*(செய்|பண்ண|விடு)",
    r"அடிச்சி\s*(விரட்டு|கொல்)",
    r"வெடிகுண்டு",
    r"கலவரம்",
]
_THREAT_RE = [re.compile(p, re.IGNORECASE) for p in _THREAT_PATTERNS]

# Words that indicate hate speech
_HATE_PATTERNS = [
    r"\b(terroris[tm]|extremis[tm])\b",
    r"\b(anti[\s-]?national)\b",
    r"\bcommunal\s+(violence|tension|clash)\b",
    r"\b(hate\s+speech|incite|inciting)\b",
]
_HATE_RE = [re.compile(p, re.IGNORECASE) for p in _HATE_PATTERNS]

# Negative campaigning and polarizing content patterns
_NEGATIVE_CAMPAIGN_PATTERNS = [
    r"\b(corrupt|corruption|scam|fraud|scandal|irregularit)\b",
    r"\b(accus|allegat|charge[sd]|booked|arrested|detained|FIR|complaint)\b",
    r"\b(protest|agitation|strike|bandh|blockade|boycott|dharna)\b",
    r"\b(clash|tension|unrest|violence|conflict)\b",
    r"\b(condemn|slam|blast|criticis|lash|attack)\b",
    r"\b(demand|resign|step\s+down|sack|dismiss)\b",
    r"\b(MCC|model\s+code|code\s+of\s+conduct|violation)\b",
    r"\b(communal|polariz|divisive|provocat)\b",
    r"\b(defect|cross\s*over|horse.?trading|poach)\b",
    r"\b(sedition|treason|separatis)\b",
    # Tamil political terms
    r"ஊழல்|புகார்|கைது|போராட்டம்|கண்டனம்",
    r"ராஜினாமா|நீக்கம்|மோதல்|பதற்றம்",
]
_NEGATIVE_CAMPAIGN_RE = [re.compile(p, re.IGNORECASE) for p in _NEGATIVE_CAMPAIGN_PATTERNS]

# Political context markers — at least one must be present for CRITICAL/HIGH
_POLITICAL_CONTEXT = [
    "election", "vote", "party", "minister", "mla", "mp", "parliament",
    "dmk", "aiadmk", "bjp", "congress", "pmk", "neet", "cauvery",
    "campaign", "rally", "manifesto", "constituency", "candidate",
    "government", "opposition", "alliance", "seat", "polling",
    "tamil nadu", "tamilnadu", "chennai", "chief minister",
    "governor", "assembly", "lok sabha", "rajya sabha",
    "stalin", "annamalai", "edappadi", "kamal", "seeman",
    "political", "politics", "leader", "legislat",
    # Tamil  
    "தேர்தல்", "வாக்கு", "கட்சி", "அமைச்சர்",
    "திமுக", "அதிமுக", "பாஜக", "காங்கிரஸ்",
    "முதலமைச்சர்", "ஆளுநர்",
    # Also match news about TN politics broadly
    "police", "court", "high court", "supreme court", "tribunal",
    "commissioner", "collector", "ias", "ips",
]

# Sensitive issue keywords
_SENSITIVE_ISSUES = [
    "neet", "cauvery", "kaveri", "reservation", "corruption",
    "communal", "caste", "farmer", "protest", "strike",
    "sc/st", "obc", "dalit", "minority", "conversion",
    "sri lankan tamils", "fishermen", "katchatheevu",
    "liquor", "prohibition", "drug", "methanol",
    "காவிரி", "இட ஒதுக்கீடு", "ஊழல்",
]


def _has_political_context(text_lower: str) -> bool:
    """Check if the text has any political context markers."""
    return any(kw in text_lower for kw in _POLITICAL_CONTEXT)


def _basic_keyword_analysis(db: Session, text: str) -> dict:
    """
    Improved keyword-based analysis:
    - Uses regex WORD BOUNDARIES to avoid false positives (e.g. "Hero Killer")
    - Requires POLITICAL CONTEXT before escalating to CRITICAL/HIGH
    - Multiple signals needed for high severity
    """
    if not ENABLE_KEYWORD_ANALYSIS or not text:
        return {
            "sentiment": "neutral",
            "severity": "LOW",
            "issues": [],
            "topics": ["General"],
            "confidence": 0.5,
            "explanation": "No analysis configured.",
        }

    lower = text.lower()
    issues: list[str] = []
    severity = "LOW"
    has_politics = _has_political_context(lower)

    # --- Check for threat patterns (regex, not simple substring) ---
    threat_matches = sum(1 for regex in _THREAT_RE if regex.search(text))
    if threat_matches > 0:
        issues.append("VIOLENCE_OR_THREAT")
        if has_politics:
            severity = "CRITICAL" if threat_matches >= 2 else "HIGH"
        else:
            severity = "MEDIUM"

    # --- Check for hate speech patterns ---
    hate_matches = sum(1 for regex in _HATE_RE if regex.search(text))
    if hate_matches > 0:
        issues.append("HATE_SPEECH")
        if severity == "LOW":
            severity = "HIGH" if has_politics else "MEDIUM"

    # --- Check for negative campaigning / polarizing content ---
    neg_campaign = sum(1 for regex in _NEGATIVE_CAMPAIGN_RE if regex.search(text))
    if neg_campaign > 0 and has_politics:
        if neg_campaign >= 3:
            issues.append("NEGATIVE_CAMPAIGNING")
            if severity == "LOW":
                severity = "HIGH"
        elif neg_campaign >= 1:
            issues.append("POLITICAL_INCIDENT")
            if severity == "LOW":
                severity = "MEDIUM"

    # --- Check for sensitive political issues ---
    sensitive_found = [kw for kw in _SENSITIVE_ISSUES if kw in lower]
    if sensitive_found and has_politics:
        issues.append("SENSITIVE_ISSUE")
        if severity == "LOW":
            severity = "MEDIUM"

    # --- Political context with ANY negative sentiment = at least MEDIUM ---
    # This ensures political news about conflicts, accusations, etc. always surfaces
    if has_politics and severity == "LOW":
        # Check if there's any notable content worth surfacing
        if neg_campaign > 0 or sensitive_found:
            severity = "MEDIUM"

    # --- Determine sentiment ---
    sentiment = "neutral"
    negative_indicators = [
        r"\b(attack|corrupt|fraud|scam|scandal|cheat|betray|fail|crisis)\b",
        r"\b(worst|terrible|shame|disgusting|awful|pathetic)\b",
        r"ஊழல்|மோசம்|அவமானம்",
    ]
    positive_indicators = [
        r"\b(good|great|excellent|best|success|progress|develop|improve|win)\b",
        r"\b(welcome|support|appreciate|congratulat)\b",
        r"நல்லா|சிறந்த|வெற்றி",
    ]
    neg_count = sum(1 for p in negative_indicators if re.search(p, text, re.IGNORECASE))
    pos_count = sum(1 for p in positive_indicators if re.search(p, text, re.IGNORECASE))
    if neg_count > pos_count:
        sentiment = "negative"
    elif pos_count > neg_count:
        sentiment = "positive"

    # --- Determine topics ---
    topics = []
    if any(kw in lower for kw in ["election", "vote", "campaign", "rally", "candidate", "polling", "தேர்தல்"]):
        topics.append("Elections")
    if any(kw in lower for kw in ["policy", "reform", "law", "bill", "scheme", "budget"]):
        topics.append("Policy")
    if any(kw in lower for kw in ["neet", "education", "school", "college", "university"]):
        topics.append("Education")
    if any(kw in lower for kw in ["farmer", "agriculture", "crop", "cauvery", "kaveri", "water"]):
        topics.append("Agriculture")
    if any(kw in lower for kw in ["protest", "strike", "march", "agitation", "bandh"]):
        topics.append("Protests")
    if any(kw in lower for kw in ["corruption", "scam", "fraud", "arrest", "case", "court"]):
        topics.append("Law & Order")
    if not topics:
        topics.append("General")

    # --- Confidence ---
    if issues:
        confidence = 0.80 if has_politics else 0.55
    else:
        confidence = 0.70 if has_politics else 0.50

    # --- Build explanation ---
    if not issues:
        explanation = "No violations detected."
    elif has_politics:
        explanation = f"Detected: {', '.join(issues)} in political context."
    else:
        explanation = f"Detected: {', '.join(issues)} (no clear political context; may be false positive)."

    return {
        "sentiment": sentiment,
        "severity": severity,
        "issues": issues,
        "topics": topics,
        "confidence": confidence,
        "explanation": explanation,
    }


# ---------------------------------------------------------------------------
#  RSS / News collector
# ---------------------------------------------------------------------------

def collect_news_rss(db: Session) -> int:
    """
    Collect latest political/news articles from configured RSS feeds.
    Uses RSS_LOOKBACK_HOURS from config (default 48h).
    """
    created = 0
    cutoff = _now_utc() - timedelta(hours=RSS_LOOKBACK_HOURS)

    for feed_url in NEWS_RSS_FEEDS:
        source_name = _get_rss_source_name(feed_url)
        try:
            parsed = feedparser.parse(feed_url)
        except Exception as exc:
            logger.warning("RSS parse error for %s: %s", source_name, exc)
            continue

        if not parsed.entries:
            logger.debug("  RSS [%s]: 0 entries returned", source_name)
            continue

        feed_created = 0
        for entry in parsed.entries:
            # Try to get a publication date; fall back to now
            published = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published = datetime(*entry.published_parsed[:6])
            elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                published = datetime(*entry.updated_parsed[:6])
            else:
                published = _now_utc()

            if published < cutoff:
                continue

            title = getattr(entry, "title", "") or ""
            summary = getattr(entry, "summary", "") or ""
            link = getattr(entry, "link", "") or ""
            content = f"{title}\n\n{summary}".strip()

            if not content or not link:
                continue

            post_id = _make_post_id("news", link)

            existing = (
                db.query(Post)
                .filter(Post.platform == "news", Post.post_id == post_id)
                .first()
            )
            if existing:
                continue

            analysis = _basic_keyword_analysis(db, content)

            post = Post(
                platform="news",
                post_id=post_id,
                author_id=None,
                author_name=source_name,
                content=content,
                language="en",
                translated_content=None,
                url=link,
                timestamp=published,
                likes=0,
                shares=0,
                comments_count=0,
                location=None,
                district=None,
            )
            db.add(post)
            db.flush()

            analyzed = AnalyzedPost(
                post_id=post.id,
                sentiment=analysis["sentiment"],
                sentiment_score=analysis["confidence"],
                topics=analysis["topics"],
                entities={},
                severity=analysis["severity"],
                severity_score=analysis["confidence"],
                detected_issues=analysis["issues"],
                confidence_score=analysis["confidence"],
                explanation=analysis["explanation"],
                key_phrases=analysis["issues"],
            )
            db.add(analyzed)
            db.flush()

            if analysis["severity"] in {"CRITICAL", "HIGH", "MEDIUM"}:
                alert = Alert(
                    post_id=post.id,
                    analyzed_post_id=analyzed.id,
                    severity=analysis["severity"],
                    alert_type="NEWS_ARTICLE",
                    description=analysis["explanation"],
                    evidence={"source": "RSS", "feed_url": feed_url, "source_name": source_name},
                    status="NEW",
                    notes=[],
                )
                db.add(alert)

            feed_created += 1
            created += 1

        if feed_created:
            logger.info("  RSS [%s]: +%d new articles", source_name, feed_created)

    db.commit()
    return created


# ---------------------------------------------------------------------------
#  Shared post-creation helpers
# ---------------------------------------------------------------------------

def _upsert_post_if_new(
    db: Session,
    platform: str,
    post_id: str,
    author_id: str | None,
    author_name: str | None,
    content: str,
    url: str,
    timestamp: datetime,
) -> Post | None:
    existing = (
        db.query(Post)
        .filter(Post.platform == platform, Post.post_id == post_id)
        .first()
    )
    if existing:
        return None

    post = Post(
        platform=platform,
        post_id=post_id,
        author_id=author_id,
        author_name=author_name,
        content=content,
        language="en",
        translated_content=None,
        url=url,
        timestamp=timestamp,
        likes=0,
        shares=0,
        comments_count=0,
        location=None,
        district=None,
    )
    db.add(post)
    db.flush()
    return post


def _create_analysis_and_alert_if_needed(
    db: Session,
    post: Post,
    analysis: dict,
    alert_type: str,
    evidence_extra: dict | None = None,
) -> None:
    analyzed = AnalyzedPost(
        post_id=post.id,
        sentiment=analysis["sentiment"],
        sentiment_score=analysis["confidence"],
        topics=analysis["topics"],
        entities={},
        severity=analysis["severity"],
        severity_score=analysis["confidence"],
        detected_issues=analysis["issues"],
        confidence_score=analysis["confidence"],
        explanation=analysis["explanation"],
        key_phrases=analysis["issues"],
    )
    db.add(analyzed)
    db.flush()

    if analysis["severity"] in {"CRITICAL", "HIGH", "MEDIUM"}:
        evidence = {"detected_issues": analysis["issues"]}
        if evidence_extra:
            evidence.update(evidence_extra)
        alert = Alert(
            post_id=post.id,
            analyzed_post_id=analyzed.id,
            severity=analysis["severity"],
            alert_type=alert_type,
            description=analysis["explanation"],
            evidence=evidence,
            status="NEW",
            notes=[],
        )
        db.add(alert)


# ---------------------------------------------------------------------------
#  X (Twitter) collector
# ---------------------------------------------------------------------------

def collect_x_recent(db: Session) -> int:
    if not X_BEARER_TOKEN or not X_SEARCH_QUERIES:
        return 0

    created = 0
    headers = {"Authorization": f"Bearer {X_BEARER_TOKEN}"}
    base_url = "https://api.x.com/2/tweets/search/recent"

    with httpx.Client(timeout=10.0) as client:
        for query in X_SEARCH_QUERIES:
            params = {
                "query": query,
                "max_results": 50,
                "tweet.fields": "created_at,author_id,lang",
            }
            try:
                resp = client.get(base_url, params=params, headers=headers)
                resp.raise_for_status()
            except Exception as exc:
                logger.warning("  X API error for query '%s': %s", query, exc)
                continue

            data = resp.json()
            for t in data.get("data", []):
                text = t.get("text", "")
                if not text:
                    continue
                tweet_id = t["id"]
                author_id = t.get("author_id")
                created_at_str = t.get("created_at")
                ts = (
                    datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                    if created_at_str
                    else _now_utc()
                )
                url = f"https://x.com/i/web/status/{tweet_id}"

                post = _upsert_post_if_new(db, "x", tweet_id, author_id, None, text, url, ts)
                if not post:
                    continue

                analysis = _basic_keyword_analysis(db, text)
                _create_analysis_and_alert_if_needed(
                    db, post, analysis, "SOCIAL_POST",
                    evidence_extra={"platform": "x", "query": query},
                )
                created += 1

    if created:
        logger.info("  X (Twitter): +%d new tweets", created)
    db.commit()
    return created


# ---------------------------------------------------------------------------
#  YouTube collector
# ---------------------------------------------------------------------------

def collect_youtube(db: Session) -> int:
    if not YOUTUBE_API_KEY or not YOUTUBE_SEARCH_QUERIES:
        return 0

    created = 0
    base_url = "https://www.googleapis.com/youtube/v3/search"

    with httpx.Client(timeout=10.0) as client:
        for query in YOUTUBE_SEARCH_QUERIES:
            params = {
                "key": YOUTUBE_API_KEY,
                "part": "snippet",
                "q": query,
                "type": "video",
                "maxResults": 25,
                "regionCode": "IN",
                "order": "date",
            }
            try:
                resp = client.get(base_url, params=params)
                resp.raise_for_status()
            except Exception as exc:
                logger.warning("  YouTube API error for query '%s': %s", query, exc)
                continue

            data = resp.json()
            for item in data.get("items", []):
                vid_id = item["id"].get("videoId")
                if not vid_id:
                    continue
                snippet = item.get("snippet", {})
                title = snippet.get("title", "")
                description = snippet.get("description", "")
                channel_title = snippet.get("channelTitle", "")
                published_at = snippet.get("publishedAt")
                ts = (
                    datetime.fromisoformat(published_at.replace("Z", "+00:00"))
                    if published_at
                    else _now_utc()
                )
                content = f"{title}\n\n{description}".strip()
                if not content:
                    continue
                url = f"https://www.youtube.com/watch?v={vid_id}"

                post = _upsert_post_if_new(db, "youtube", vid_id, None, channel_title, content, url, ts)
                if not post:
                    continue

                analysis = _basic_keyword_analysis(db, content)
                _create_analysis_and_alert_if_needed(
                    db, post, analysis, "YOUTUBE_VIDEO",
                    evidence_extra={"platform": "youtube", "query": query},
                )
                created += 1

    if created:
        logger.info("  YouTube: +%d new videos", created)
    db.commit()
    return created


# ---------------------------------------------------------------------------
#  Reddit collector
# ---------------------------------------------------------------------------

def _is_tn_relevant(text: str) -> bool:
    lower = text.lower()
    return any(kw in lower for kw in REDDIT_TN_KEYWORDS)


def collect_reddit(db: Session) -> int:
    if not REDDIT_SUBREDDITS:
        return 0

    created = 0
    base_url = "https://www.reddit.com/r/{sub}/new.json"
    headers = {"User-Agent": REDDIT_USER_AGENT}

    with httpx.Client(timeout=10.0, headers=headers) as client:
        for sub in REDDIT_SUBREDDITS:
            url = base_url.format(sub=sub)
            try:
                resp = client.get(url, params={"limit": 50})
                resp.raise_for_status()
            except Exception as exc:
                logger.warning("  Reddit error for r/%s: %s", sub, exc)
                continue

            data = resp.json()
            sub_created = 0
            for child in data.get("data", {}).get("children", []):
                post_data = child.get("data", {})
                post_id = post_data.get("id")
                if not post_id:
                    continue
                title = post_data.get("title", "")
                selftext = post_data.get("selftext", "")
                content = f"{title}\n\n{selftext}".strip()
                if not content:
                    continue

                if not _is_tn_relevant(content):
                    continue

                created_utc = post_data.get("created_utc")
                ts = (
                    datetime.fromtimestamp(created_utc, tz=timezone.utc).replace(tzinfo=None)
                    if created_utc
                    else _now_utc()
                )
                author = post_data.get("author")
                permalink = post_data.get("permalink", "")
                full_url = f"https://www.reddit.com{permalink}" if permalink else ""

                post = _upsert_post_if_new(db, "reddit", post_id, author, author, content, full_url, ts)
                if not post:
                    continue

                analysis = _basic_keyword_analysis(db, content)
                _create_analysis_and_alert_if_needed(
                    db, post, analysis, "SOCIAL_POST",
                    evidence_extra={"platform": "reddit", "subreddit": sub},
                )
                sub_created += 1
                created += 1

            if sub_created:
                logger.info("  Reddit r/%s: +%d new posts", sub, sub_created)

    db.commit()
    return created


# ---------------------------------------------------------------------------
#  GNews API collector
# ---------------------------------------------------------------------------

def collect_gnews(db: Session) -> int:
    if not GNEWS_API_KEY:
        return 0

    created = 0
    base_url = "https://gnews.io/api/v4/search"
    params = {
        "q": GNEWS_SEARCH_QUERY,
        "lang": GNEWS_LANGUAGE,
        "country": GNEWS_COUNTRY,
        "max": 10,
        "apikey": GNEWS_API_KEY,
    }

    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(base_url, params=params)
            resp.raise_for_status()
            data = resp.json()

            for article in data.get("articles", []):
                title = article.get("title", "")
                description = article.get("description", "")
                content_text = f"{title}\n\n{description}".strip()
                url = article.get("url", "")
                source_name = article.get("source", {}).get("name", "GNews")
                published = article.get("publishedAt")

                if not content_text or not url:
                    continue

                ts = _now_utc()
                if published:
                    try:
                        ts = datetime.fromisoformat(published.replace("Z", "+00:00")).replace(tzinfo=None)
                    except Exception:
                        pass

                post_id = _make_post_id("gnews", url)
                post = _upsert_post_if_new(db, "news", post_id, None, source_name, content_text, url, ts)
                if not post:
                    continue

                analysis = _basic_keyword_analysis(db, content_text)
                _create_analysis_and_alert_if_needed(
                    db, post, analysis, "NEWS_ARTICLE",
                    evidence_extra={"source": "GNews API", "source_name": source_name},
                )
                created += 1

        if created:
            logger.info("  GNews API: +%d new articles", created)
    except Exception as exc:
        logger.warning("  GNews API error: %s", exc)

    db.commit()
    return created


# ---------------------------------------------------------------------------
#  Main collection cycle
# ---------------------------------------------------------------------------

def run_collection_cycle() -> int:
    logger.info("=== Collection cycle starting ===")
    db: Session = SessionLocal()
    try:
        total = 0
        total += collect_news_rss(db)
        total += collect_gnews(db)
        total += collect_x_recent(db)
        total += collect_youtube(db)
        total += collect_reddit(db)
        logger.info("=== Collection cycle complete: %d new items ===", total)
        return total
    except Exception as exc:
        logger.error("Collection cycle error: %s", exc)
        return 0
    finally:
        db.close()
