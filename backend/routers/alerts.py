from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, and_, or_
from typing import Optional, List
from datetime import datetime
from database import get_db
from models import Alert, Post, AnalyzedPost, User, AuditLog
from auth import get_current_user

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("")
def list_alerts(
    severity: Optional[str] = None,
    status: Optional[str] = None,
    district: Optional[str] = None,
    platform: Optional[str] = None,
    alert_type: Optional[str] = None,
    search: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Alert).options(
        joinedload(Alert.post),
        joinedload(Alert.analyzed_post),
        joinedload(Alert.assigned_user)
    )

    if severity:
        query = query.filter(Alert.severity == severity.upper())
    if status:
        query = query.filter(Alert.status == status.upper())
    if district:
        query = query.join(Post).filter(Post.district == district)
    if platform:
        query = query.join(Post, isouter=True).filter(Post.platform == platform)
    if alert_type:
        query = query.filter(Alert.alert_type == alert_type)
    if search:
        query = query.join(Post, isouter=True).filter(
            or_(
                Post.content.ilike(f"%{search}%"),
                Post.translated_content.ilike(f"%{search}%"),
                Post.author_name.ilike(f"%{search}%"),
                Alert.description.ilike(f"%{search}%")
            )
        )
    if date_from:
        query = query.filter(Alert.created_at >= datetime.fromisoformat(date_from))
    if date_to:
        query = query.filter(Alert.created_at <= datetime.fromisoformat(date_to))

    total = query.count()
    alerts = query.order_by(desc(Alert.created_at)).offset((page - 1) * limit).limit(limit).all()

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "data": [serialize_alert(a) for a in alerts]
    }


@router.get("/stats")
def alert_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from sqlalchemy import func
    stats = db.query(Alert.severity, func.count(Alert.id)).group_by(Alert.severity).all()
    status_stats = db.query(Alert.status, func.count(Alert.id)).group_by(Alert.status).all()
    return {
        "by_severity": {s: c for s, c in stats},
        "by_status": {s: c for s, c in status_stats},
        "total": sum(c for _, c in stats)
    }


@router.get("/{alert_id}")
def get_alert(alert_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    alert = db.query(Alert).options(
        joinedload(Alert.post),
        joinedload(Alert.analyzed_post),
        joinedload(Alert.assigned_user)
    ).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return serialize_alert(alert)


@router.put("/{alert_id}/status")
def update_alert_status(
    alert_id: int,
    body: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    new_status = body.get("status", "").upper()
    valid = ["NEW", "IN_REVIEW", "ACTIONABLE", "FALSE_POSITIVE", "RESOLVED", "ESCALATED"]
    if new_status not in valid:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of {valid}")

    alert.status = new_status
    if new_status == "RESOLVED":
        alert.resolved_at = datetime.utcnow()
    alert.updated_at = datetime.utcnow()

    db.add(AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action="UPDATE_ALERT_STATUS",
        resource_type="alert",
        resource_id=alert_id,
        details={"old_status": alert.status, "new_status": new_status}
    ))
    db.commit()
    return {"message": "Status updated", "status": new_status}


@router.post("/{alert_id}/notes")
def add_note(
    alert_id: int,
    body: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    note = {
        "user": current_user.username,
        "user_name": current_user.full_name,
        "text": body.get("text", ""),
        "timestamp": datetime.utcnow().isoformat()
    }
    existing = alert.notes or []
    existing.append(note)
    alert.notes = existing
    alert.updated_at = datetime.utcnow()
    db.commit()
    return {"message": "Note added", "note": note}


def serialize_alert(a):
    result = {
        "id": a.id,
        "severity": a.severity,
        "alert_type": a.alert_type,
        "description": a.description,
        "status": a.status,
        "notes": a.notes or [],
        "created_at": a.created_at.isoformat() if a.created_at else None,
        "updated_at": a.updated_at.isoformat() if a.updated_at else None,
        "resolved_at": a.resolved_at.isoformat() if a.resolved_at else None,
        "assigned_to": None,
        "post": None,
        "analysis": None
    }
    if a.assigned_user:
        result["assigned_to"] = {
            "id": a.assigned_user.id,
            "username": a.assigned_user.username,
            "full_name": a.assigned_user.full_name,
            "role": a.assigned_user.role
        }
    if a.post:
        result["post"] = {
            "id": a.post.id,
            "platform": a.post.platform,
            "author_name": a.post.author_name,
            "author_id": a.post.author_id,
            "content": a.post.content,
            "language": a.post.language,
            "translated_content": a.post.translated_content,
            "url": a.post.url,
            "timestamp": a.post.timestamp.isoformat() if a.post.timestamp else None,
            "likes": a.post.likes,
            "shares": a.post.shares,
            "comments_count": a.post.comments_count,
            "district": a.post.district,
            "location": a.post.location
        }
    if a.analyzed_post:
        result["analysis"] = {
            "sentiment": a.analyzed_post.sentiment,
            "sentiment_score": a.analyzed_post.sentiment_score,
            "topics": a.analyzed_post.topics,
            "entities": a.analyzed_post.entities,
            "severity": a.analyzed_post.severity,
            "severity_score": a.analyzed_post.severity_score,
            "detected_issues": a.analyzed_post.detected_issues,
            "confidence_score": a.analyzed_post.confidence_score,
            "explanation": a.analyzed_post.explanation,
            "key_phrases": a.analyzed_post.key_phrases
        }
    return result
