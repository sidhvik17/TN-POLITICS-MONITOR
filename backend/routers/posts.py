from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_
from typing import Optional
from datetime import datetime
from database import get_db
from models import Post, AnalyzedPost, User
from auth import get_current_user

router = APIRouter(prefix="/api/posts", tags=["posts"])


@router.get("")
def list_posts(
    platform: Optional[str] = None,
    district: Optional[str] = None,
    language: Optional[str] = None,
    severity: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Post)

    if platform:
        query = query.filter(Post.platform == platform)
    if district:
        query = query.filter(Post.district == district)
    if language:
        query = query.filter(Post.language == language)
    if severity:
        query = query.join(AnalyzedPost).filter(AnalyzedPost.severity == severity.upper())
    if date_from:
        query = query.filter(Post.timestamp >= datetime.fromisoformat(date_from))
    if date_to:
        query = query.filter(Post.timestamp <= datetime.fromisoformat(date_to))

    total = query.count()
    posts = query.order_by(desc(Post.timestamp)).offset((page - 1) * limit).limit(limit).all()

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "data": [serialize_post(p) for p in posts]
    }


@router.get("/search")
def search_posts(
    q: str = Query(..., min_length=1),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Post).filter(
        or_(
            Post.content.ilike(f"%{q}%"),
            Post.translated_content.ilike(f"%{q}%"),
            Post.author_name.ilike(f"%{q}%")
        )
    )
    total = query.count()
    posts = query.order_by(desc(Post.timestamp)).offset((page - 1) * limit).limit(limit).all()

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "data": [serialize_post(p) for p in posts]
    }


@router.get("/{post_id}")
def get_post(post_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Post not found")
    return serialize_post(post)


def serialize_post(p):
    result = {
        "id": p.id,
        "platform": p.platform,
        "post_id": p.post_id,
        "author_id": p.author_id,
        "author_name": p.author_name,
        "content": p.content,
        "language": p.language,
        "translated_content": p.translated_content,
        "url": p.url,
        "timestamp": p.timestamp.isoformat() if p.timestamp else None,
        "likes": p.likes,
        "shares": p.shares,
        "comments_count": p.comments_count,
        "district": p.district,
        "location": p.location,
        "analysis": None
    }
    if p.analysis:
        result["analysis"] = {
            "sentiment": p.analysis.sentiment,
            "sentiment_score": p.analysis.sentiment_score,
            "topics": p.analysis.topics,
            "severity": p.analysis.severity,
            "severity_score": p.analysis.severity_score,
            "detected_issues": p.analysis.detected_issues,
            "confidence_score": p.analysis.confidence_score
        }
    return result
