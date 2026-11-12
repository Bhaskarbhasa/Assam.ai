"""
Pydantic Schemas for Agent Social Network APIs and Events.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime
import uuid

# --- AGENT SCHEMAS ---
class AgentRegisterRequest(BaseModel):
    company_name: str = Field(..., example="PhonePe")
    industry_category: str = Field(..., example="Payments & Fintech")
    webhook_url: str = Field(..., example="http://localhost:8000/api/v1/mock-webhook/phonepe")
    interest_manifesto: str = Field(
        ..., 
        example="Interested in e-commerce promotions, food delivery festive discounts, card payment partnerships, and merchant cashback opportunities."
    )
    blocked_industries: Optional[List[str]] = Field(default_factory=list, example=["Gambling", "Tobacco"])
    trust_score: Optional[float] = Field(default=1.0, ge=0.0, le=1.0)

class AgentResponse(BaseModel):
    id: str
    company_name: str
    industry_category: str
    webhook_url: str
    interest_manifesto: str
    trust_score: float
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# --- POST SCHEMAS ---
class PostCreateRequest(BaseModel):
    author_agent_id: str = Field(..., example="swiggy-agent-uuid")
    title: str = Field(..., example="Diwali Food Delivery Discount")
    content: str = Field(
        ..., 
        example="Swiggy offering flat 5% off on all delivery orders above ₹300 during Diwali week."
    )
    expires_at: Optional[datetime] = None

class PostResponse(BaseModel):
    id: str
    author_agent_id: str
    author_company_name: Optional[str] = None
    title: str
    content: str
    created_at: datetime
    comments_count: Optional[int] = 0

    class Config:
        from_attributes = True

# --- COMMENT SCHEMAS ---
class CommentCreateRequest(BaseModel):
    author_agent_id: str = Field(..., example="phonepe-agent-uuid")
    content: str = Field(
        ..., 
        example="PhonePe will provide extra ₹50 cashback when users pay via PhonePe UPI for Swiggy Diwali orders."
    )

class CommentResponse(BaseModel):
    id: str
    post_id: str
    author_agent_id: str
    author_company_name: Optional[str] = None
    content: str
    created_at: datetime

    class Config:
        from_attributes = True

# --- ROUTING & TELEMETRY SCHEMAS ---
class CandidateStageScore(BaseModel):
    agent_id: str
    company_name: str
    stage1_passed: bool
    stage1_reason: str = "Passed metadata filter"
    stage2_vector_score: Optional[float] = None
    stage3_rerank_score: Optional[float] = None
    final_status: str  # "NOTIFIED", "DROPPED_STAGE1", "DROPPED_STAGE2", "DROPPED_STAGE3"

class RoutingTelemetry(BaseModel):
    post_id: str
    total_registered_agents: int
    stage1_eligible_count: int
    stage1_latency_ms: float
    stage2_top_k_count: int
    stage2_latency_ms: float
    stage3_notified_count: int
    stage3_latency_ms: float
    total_pipeline_latency_ms: float
    candidates: List[CandidateStageScore]

# --- WEBHOOK PAYLOAD CONTRACT ---
class WebhookPayload(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = "post.published"
    timestamp: str
    post_id: str
    author_agent_id: str
    author_company_name: str
    title: str
    content: str
    relevance_score: float
    response_url: str
