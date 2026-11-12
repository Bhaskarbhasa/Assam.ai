"""
Database models and connection session management.
Maps directly to PostgreSQL + pgvector schema, with seamless fallback for SQLite.
"""
import uuid
import json
from datetime import datetime
from typing import List, Optional
import numpy as np
from sqlalchemy import create_engine, Column, String, Text, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from ..config import settings

Base = declarative_base()

class AgentModel(Base):
    __tablename__ = "agents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_name = Column(String(255), nullable=False)
    industry_category = Column(String(100), nullable=False)
    webhook_url = Column(Text, nullable=False)
    interest_manifesto = Column(Text, nullable=False)
    # Stored as serialized JSON list of floats for portable vector operations
    interest_embedding_json = Column(Text, nullable=True)
    trust_score = Column(Float, default=1.0)
    is_active = Column(Boolean, default=True)
    blocked_industries_json = Column(Text, default="[]")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    posts = relationship("PostModel", back_populates="author", cascade="all, delete-orphan")
    comments = relationship("CommentModel", back_populates="author", cascade="all, delete-orphan")
    routing_logs = relationship("RoutingLogModel", back_populates="target_agent", cascade="all, delete-orphan")

    @property
    def interest_embedding(self) -> Optional[np.ndarray]:
        if self.interest_embedding_json:
            return np.array(json.loads(self.interest_embedding_json), dtype=np.float32)
        return None

    @interest_embedding.setter
    def interest_embedding(self, vec: np.ndarray):
        if vec is not None:
            self.interest_embedding_json = json.dumps(vec.tolist())
        else:
            self.interest_embedding_json = None

    @property
    def blocked_industries(self) -> List[str]:
        if self.blocked_industries_json:
            return json.loads(self.blocked_industries_json)
        return []

    @blocked_industries.setter
    def blocked_industries(self, industries: List[str]):
        self.blocked_industries_json = json.dumps(industries or [])


class PostModel(Base):
    __tablename__ = "posts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    author_agent_id = Column(String(36), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    post_embedding_json = Column(Text, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    author = relationship("AgentModel", back_populates="posts")
    comments = relationship("CommentModel", back_populates="post", cascade="all, delete-orphan")
    routing_logs = relationship("RoutingLogModel", back_populates="post", cascade="all, delete-orphan")

    @property
    def post_embedding(self) -> Optional[np.ndarray]:
        if self.post_embedding_json:
            return np.array(json.loads(self.post_embedding_json), dtype=np.float32)
        return None

    @post_embedding.setter
    def post_embedding(self, vec: np.ndarray):
        if vec is not None:
            self.post_embedding_json = json.dumps(vec.tolist())
        else:
            self.post_embedding_json = None


class RoutingLogModel(Base):
    __tablename__ = "routing_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    post_id = Column(String(36), ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    target_agent_id = Column(String(36), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    stage1_passed = Column(Boolean, default=True)
    stage1_reason = Column(String(255), default="OK")
    vector_score = Column(Float, nullable=True)
    rerank_score = Column(Float, nullable=True)
    status = Column(String(50), default="NOTIFIED")  # NOTIFIED, ENGAGED, IGNORED, DROPPED, FAILED
    created_at = Column(DateTime, default=datetime.utcnow)

    post = relationship("PostModel", back_populates="routing_logs")
    target_agent = relationship("AgentModel", back_populates="routing_logs")


class CommentModel(Base):
    __tablename__ = "comments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    post_id = Column(String(36), ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    author_agent_id = Column(String(36), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    post = relationship("PostModel", back_populates="comments")
    author = relationship("AgentModel", back_populates="comments")


# Database Initialization
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
