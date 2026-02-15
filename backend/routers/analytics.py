from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, extract, case
from typing import Optional
from datetime import datetime, timedelta
from database import get_db
from models import Post, AnalyzedPost, Alert, User
from auth import get_current_user

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

TN_DISTRICTS = [
    "Chennai", "Coimbatore", "Madurai", "Tiruchirappalli", "Salem",
    "Tirunelveli", "Tiruppur", "Erode", "Vellore", "Thoothukudi",
    "Dindigul", "Thanjavur", "Ranipet", "Sivagangai", "Karur",
    "Kanyakumari", "Theni", "Namakkal", "Nagapattinam", "Cuddalore",
    "Krishnagiri", "Dharmapuri", "Ramanathapuram", "Virudhunagar",
    "Villupuram", "Perambalur", "Ariyalur", "Nilgiris", "Tiruvannamalai",
    "Tirupathur", "Chengalpattu", "Kanchipuram", "Kallakurichi",
    "Tiruvarur", "Mayiladuthurai", "Pudukkottai", "Tenkasi", "Tiruvallur"
]


@router.get("/trends")
def get_trends(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    since = datetime.utcnow() - timedelta(days=days)
    prev_since = since - timedelta(days=days)

    # Top topics from analyzed posts
    posts = db.query(AnalyzedPost).join(Post).filter(Post.timestamp >= since).all()
    topic_counts = {}
    for p in posts:
        if p.topics:
            for t in p.topics:
                topic_counts[t] = topic_counts.get(t, 0) + 1

    sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:10]

    # Previous period for comparison
    prev_posts = db.query(AnalyzedPost).join(Post).filter(
        Post.timestamp >= prev_since, Post.timestamp < since
    ).all()
    prev_topic_counts = {}
    for p in prev_posts:
        if p.topics:
            for t in p.topics:
                prev_topic_counts[t] = prev_topic_counts.get(t, 0) + 1

    trends = []
    for topic, count in sorted_topics:
        prev_count = prev_topic_counts.get(topic, 0)
        change = ((count - prev_count) / max(prev_count, 1)) * 100
        trends.append({
            "topic": topic,
            "count": count,
            "previous_count": prev_count,
            "change_percent": round(change, 1),
            "direction": "up" if change > 5 else ("down" if change < -5 else "stable")
        })

    # Word cloud data - all entity names
    word_data = []
    entity_counts = {}
    for p in posts:
        if p.entities:
            for etype, elist in p.entities.items():
                for e in elist:
                    name = e if isinstance(e, str) else e.get("name", str(e))
                    entity_counts[name] = entity_counts.get(name, 0) + 1
    for word, count in sorted(entity_counts.items(), key=lambda x: x[1], reverse=True)[:30]:
        word_data.append({"text": word, "value": count})

    return {"trends": trends, "word_cloud": word_data}


@router.get("/sentiment")
def get_sentiment(
    days: int = Query(30, ge=1, le=90),
    entity: Optional[str] = None,
    district: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    since = datetime.utcnow() - timedelta(days=days)
    query = db.query(
        func.date(Post.timestamp).label("date"),
        AnalyzedPost.sentiment,
        func.count(AnalyzedPost.id).label("count")
    ).join(Post, AnalyzedPost.post_id == Post.id).filter(Post.timestamp >= since)

    if district:
        query = query.filter(Post.district == district)

    results = query.group_by(func.date(Post.timestamp), AnalyzedPost.sentiment).all()

    date_data = {}
    for date_val, sentiment, count in results:
        d = str(date_val)
        if d not in date_data:
            date_data[d] = {"date": d, "positive": 0, "negative": 0, "neutral": 0, "mixed": 0}
        if sentiment:
            date_data[d][sentiment.lower()] = count

    return {"data": sorted(date_data.values(), key=lambda x: x["date"])}


@router.get("/geographic")
def get_geographic(
    days: int = Query(7, ge=1, le=90),
    severity: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    since = datetime.utcnow() - timedelta(days=days)
    query = db.query(
        Post.district,
        func.count(Alert.id).label("alert_count")
    ).join(Alert, Alert.post_id == Post.id).filter(Alert.created_at >= since)

    if severity:
        query = query.filter(Alert.severity == severity.upper())

    results = query.filter(Post.district != None).group_by(Post.district).all()
    district_data = {d: 0 for d in TN_DISTRICTS}
    for district, count in results:
        if district in district_data:
            district_data[district] = count

    # Top districts
    sorted_districts = sorted(district_data.items(), key=lambda x: x[1], reverse=True)

    return {
        "districts": district_data,
        "top_districts": [{"name": d, "count": c} for d, c in sorted_districts[:10]],
        "total_alerts": sum(district_data.values())
    }


@router.get("/platforms")
def get_platforms(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    since = datetime.utcnow() - timedelta(days=days)
    results = db.query(
        Post.platform,
        func.count(Post.id).label("count")
    ).filter(Post.timestamp >= since).group_by(Post.platform).all()

    return {"data": [{"platform": p, "count": c} for p, c in results]}


@router.get("/overview")
def get_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = today - timedelta(days=7)

    total_posts = db.query(func.count(Post.id)).scalar()
    today_posts = db.query(func.count(Post.id)).filter(Post.timestamp >= today).scalar()
    total_alerts = db.query(func.count(Alert.id)).scalar()
    active_alerts = db.query(func.count(Alert.id)).filter(
        Alert.status.in_(["NEW", "IN_REVIEW"])
    ).scalar()
    critical_alerts = db.query(func.count(Alert.id)).filter(
        Alert.severity == "CRITICAL", Alert.status.in_(["NEW", "IN_REVIEW"])
    ).scalar()
    resolved_today = db.query(func.count(Alert.id)).filter(
        Alert.resolved_at >= today
    ).scalar()

    return {
        "total_posts": total_posts,
        "today_posts": today_posts,
        "total_alerts": total_alerts,
        "active_alerts": active_alerts,
        "critical_alerts": critical_alerts,
        "resolved_today": resolved_today,
        "districts_monitored": len(TN_DISTRICTS),
        "platforms_active": db.query(func.count(func.distinct(Post.platform))).scalar()
    }
