"""
Seed data for TN Politics Monitor.
Creates users and keywords needed for the system to run.

Usage:
    python seed_data.py            # Seed users + keywords only (production)
    python seed_data.py --demo     # Also add sample posts/alerts for offline demo
"""
import sys
import random
from datetime import datetime, timedelta
from database import engine, SessionLocal, Base
from models import User, Post, AnalyzedPost, Alert, Keyword, AuditLog
from auth import hash_password

# Tamil Nadu districts
DISTRICTS = [
    "Chennai", "Coimbatore", "Madurai", "Tiruchirappalli", "Salem",
    "Tirunelveli", "Tiruppur", "Erode", "Vellore", "Thoothukudi",
    "Dindigul", "Thanjavur", "Ranipet", "Sivagangai", "Karur",
    "Kanyakumari", "Theni", "Namakkal", "Nagapattinam", "Cuddalore",
    "Krishnagiri", "Dharmapuri", "Ramanathapuram", "Virudhunagar",
    "Villupuram", "Perambalur", "Ariyalur", "Nilgiris", "Tiruvannamalai",
    "Tirupathur", "Chengalpattu", "Kanchipuram", "Kallakurichi",
    "Tiruvarur", "Mayiladuthurai", "Pudukkottai", "Tenkasi", "Tiruvallur"
]


def seed_users(db):
    """Create default system users (one per role)."""
    users = [
        User(username="rajesh_officer", email="rajesh@ec.tn.gov.in",
             password_hash=hash_password("TnPolitics@2026"), full_name="Rajesh Kumar",
             role="duty_officer", phone="+91-9876543210", is_active=True),
        User(username="priya_analyst", email="priya@ec.tn.gov.in",
             password_hash=hash_password("TnPolitics@2026"), full_name="Priya Sharma",
             role="analyst", phone="+91-9876543211", is_active=True),
        User(username="senior_official", email="senior@ec.tn.gov.in",
             password_hash=hash_password("TnPolitics@2026"), full_name="D. Murugan",
             role="senior_official", phone="+91-9876543212", is_active=True),
        User(username="admin123", email="admin@ec.tn.gov.in",
             password_hash=hash_password("TnPolitics@2026"), full_name="Admin",
             role="admin", phone="+91-9876543213", is_active=True),
        User(username="auditor_ravi", email="ravi@ec.tn.gov.in",
             password_hash=hash_password("TnPolitics@2026"), full_name="Ravi Chandran",
             role="auditor", phone="+91-9876543214", is_active=True),
    ]
    db.add_all(users)
    db.flush()
    return users


def seed_keywords(db):
    """Create keyword entries used by the analysis pipeline."""
    keyword_data = {
        "political_parties": ["DMK", "AIADMK", "BJP", "Congress", "PMK", "DMDK", "MNM", "NTK",
                               "திமுக", "அதிமுக", "பாஜக", "காங்கிரஸ்"],
        "politicians": ["Stalin", "M.K. Stalin", "EPS", "Edappadi", "Annamalai", "Seeman",
                         "Kamal Haasan", "ஸ்டாலின்", "எடப்பாடி", "அன்புமணி"],
        "issues": ["NEET", "Cauvery", "காவிரி", "reservation", "corruption", "development",
                    "farmer", "healthcare", "education", "unemployment", "inflation"],
        "locations": DISTRICTS,
        "threats": ["kill", "attack", "bomb", "riot", "violence", "destroy", "blood",
                     "கொலை", "அடிக்க", "வெடிகுண்டு", "கலவரம்", "சண்டை"],
    }
    for category, words in keyword_data.items():
        for word in words:
            db.add(Keyword(word=word, category=category,
                           language="ta" if any(ord(c) > 127 for c in word) else "en",
                           is_active=True, created_by=4))
    db.flush()


# --- Demo data (only used with --demo flag) ---

DEMO_POSTS = [
    {
        "content": "BREAKING: Chief Minister announces new education reform for Tamil Nadu schools",
        "language": "en", "severity": "MEDIUM", "alert_type": "POLICY_DEBATE",
        "issues": ["SENSITIVE_ISSUE"], "sentiment": "neutral",
        "topics": ["Policy discussion", "Education"],
        "confidence": 0.72, "explanation": "Government policy announcement — education reform"
    },
    {
        "content": "DMK வந்தா திராவிட மொழி அழியும், எங்க culture-ஐ காப்பாத்தணும்!",
        "translated": "If DMK comes, Dravidian language will be destroyed, we must save our culture!",
        "language": "ta", "severity": "MEDIUM", "alert_type": "NEGATIVE_CAMPAIGNING",
        "issues": ["POLARIZING_CONTENT"], "sentiment": "negative",
        "topics": ["Social issues", "Campaigning"],
        "confidence": 0.72, "explanation": "Polarizing cultural narrative against political party"
    },
    {
        "content": "Good speech by Stalin ji at the rally today. DMK has good vision for Tamil Nadu's future.",
        "language": "en", "severity": "LOW", "alert_type": "GENERAL_DISCUSSION",
        "issues": [], "sentiment": "positive",
        "topics": ["Campaigning"],
        "confidence": 0.90, "explanation": "Positive campaign discussion, no violations detected"
    },
    {
        "content": "Election Commission should ensure free and fair elections. Every vote matters!",
        "language": "en", "severity": "LOW", "alert_type": "GENERAL_DISCUSSION",
        "issues": [], "sentiment": "positive",
        "topics": ["Policy discussion"],
        "confidence": 0.95, "explanation": "Pro-democracy sentiment, no issues detected"
    },
    {
        "content": "BJP trying to impose Hindi in Tamil Nadu schools! This is cultural invasion!",
        "language": "en", "severity": "MEDIUM", "alert_type": "POLARIZING_CONTENT",
        "issues": ["POLARIZING_CONTENT"], "sentiment": "negative",
        "topics": ["Social issues", "Policy discussion"],
        "confidence": 0.71, "explanation": "Language politics rhetoric that can escalate"
    },
]


def seed_demo_posts(db, count=30):
    """Create a small set of sample posts for offline demonstration."""
    now = datetime.utcnow()
    platforms = ["news", "reddit", "youtube"]

    for i in range(count):
        mock = random.choice(DEMO_POSTS)
        hours_ago = random.uniform(0, 24 * 7)
        post_time = now - timedelta(hours=hours_ago)
        platform = random.choice(platforms)

        post = Post(
            platform=platform,
            post_id=f"demo_{platform}_{i}",
            author_name=f"Demo Source {i}",
            content=mock["content"],
            language=mock["language"],
            translated_content=mock.get("translated"),
            url=f"https://example.com/demo/{i}",
            timestamp=post_time,
            likes=random.randint(0, 500),
            shares=random.randint(0, 100),
            comments_count=random.randint(0, 50),
            location=random.choice(DISTRICTS),
            district=random.choice(DISTRICTS),
        )
        db.add(post)
        db.flush()

        analysis = AnalyzedPost(
            post_id=post.id,
            sentiment=mock["sentiment"],
            sentiment_score=round(random.uniform(0.5, 0.98), 2),
            topics=mock["topics"],
            entities={},
            severity=mock["severity"],
            severity_score=round(mock["confidence"], 2),
            detected_issues=mock["issues"],
            confidence_score=round(mock["confidence"], 2),
            explanation=mock["explanation"],
            key_phrases=mock.get("issues", [])[:3],
            analyzed_at=post_time + timedelta(seconds=random.randint(10, 60))
        )
        db.add(analysis)
        db.flush()

        if mock["severity"] in ["CRITICAL", "HIGH"] or (mock["severity"] == "MEDIUM" and random.random() < 0.3):
            alert = Alert(
                post_id=post.id,
                analyzed_post_id=analysis.id,
                severity=mock["severity"],
                alert_type=mock["alert_type"],
                description=mock["explanation"],
                evidence={"detected_issues": mock["issues"], "confidence": mock["confidence"]},
                status="NEW",
                assigned_to=random.choice([1, 3]),
                notes=[],
                created_at=post_time + timedelta(seconds=random.randint(15, 90)),
            )
            db.add(alert)

    db.commit()


def seed_database(include_demo=False):
    """Main seed function. Always creates users + keywords.
    Optionally adds demo posts if --demo flag is used."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        seed_users(db)
        seed_keywords(db)
        db.commit()

        print("[OK] Database seeded with users and keywords.")
        print(f"   Users: {db.query(User).count()}")
        print(f"   Keywords: {db.query(Keyword).count()}")

        if include_demo:
            seed_demo_posts(db, count=30)
            print(f"\n[OK] Demo data added (for offline testing):")
            print(f"   Posts: {db.query(Post).count()}")
            print(f"   Analyzed: {db.query(AnalyzedPost).count()}")
            print(f"   Alerts: {db.query(Alert).count()}")
        else:
            print("\n  No demo posts created.")
            print("  Real data will be collected automatically when the backend starts.")
            print("  (Use 'python seed_data.py --demo' to add sample posts for offline testing)")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    demo = "--demo" in sys.argv
    seed_database(include_demo=demo)
