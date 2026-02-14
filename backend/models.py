from sqlalchemy import Column, Integer, BigInteger, String, Text, Float, Boolean, DateTime, JSON, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(String(50), nullable=False)  # duty_officer, analyst, senior_official, admin, auditor
    phone = Column(String(20))
    is_active = Column(Boolean, default=True)
    mfa_enabled = Column(Boolean, default=False)
    last_login = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    alerts = relationship("Alert", back_populates="assigned_user")


class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String(50), nullable=False, index=True)
    post_id = Column(String(255), nullable=False)
    author_id = Column(String(255))
    author_name = Column(String(255))
    content = Column(Text, nullable=False)
    language = Column(String(10))
    translated_content = Column(Text)
    url = Column(Text)
    timestamp = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now())
    likes = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    location = Column(String(255))
    district = Column(String(100), index=True)
    metadata_json = Column(JSON)
    analysis = relationship("AnalyzedPost", back_populates="post", uselist=False)
    alerts = relationship("Alert", back_populates="post")


class AnalyzedPost(Base):
    __tablename__ = "analyzed_posts"
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    sentiment = Column(String(20))  # positive, negative, neutral, mixed
    sentiment_score = Column(Float)
    topics = Column(JSON)  # list of topic strings
    entities = Column(JSON)  # dict of entity type -> list of entities
    severity = Column(String(20), index=True)  # CRITICAL, HIGH, MEDIUM, LOW
    severity_score = Column(Float)
    detected_issues = Column(JSON)  # list of issue strings
    confidence_score = Column(Float)
    explanation = Column(Text)
    key_phrases = Column(JSON)
    analyzed_at = Column(DateTime, server_default=func.now())
    post = relationship("Post", back_populates="analysis")


class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    analyzed_post_id = Column(Integer, ForeignKey("analyzed_posts.id"))
    severity = Column(String(20), nullable=False, index=True)
    alert_type = Column(String(50))
    description = Column(Text)
    evidence = Column(JSON)
    status = Column(String(20), default="NEW", index=True)
    assigned_to = Column(Integer, ForeignKey("users.id"))
    notes = Column(JSON)  # list of {user, text, timestamp}
    created_at = Column(DateTime, server_default=func.now(), index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    resolved_at = Column(DateTime)
    post = relationship("Post", back_populates="alerts")
    assigned_user = relationship("User", back_populates="alerts")
    analyzed_post = relationship("AnalyzedPost")


class Keyword(Base):
    __tablename__ = "keywords"
    id = Column(Integer, primary_key=True, index=True)
    word = Column(String(255), nullable=False, index=True)
    category = Column(String(100), nullable=False)  # political_parties, politicians, issues, locations, threats
    language = Column(String(10), default="en")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    created_by = Column(Integer, ForeignKey("users.id"))


class AuditLog(Base):
    __tablename__ = "audit_log"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    username = Column(String(100))
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50))
    resource_id = Column(Integer)
    details = Column(JSON)
    ip_address = Column(String(45))
    timestamp = Column(DateTime, server_default=func.now(), index=True)
