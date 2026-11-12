"""
FastAPI Entrypoint for Problem 1: B2B Social Network for AI Agents.
Provides high-performance asynchronous REST endpoints, multi-stage relevance routing,
and security guardrails.
"""
from fastapi import FastAPI, Depends, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import time

from .config import settings
from .models.database import get_db, init_db, AgentModel, PostModel, CommentModel, RoutingLogModel
from .models.schemas import (
    AgentRegisterRequest, AgentResponse,
    PostCreateRequest, PostResponse,
    CommentCreateRequest, CommentResponse,
    RoutingTelemetry
)
from .routing.embedding_engine import embedding_manager
from .routing.pipeline import routing_pipeline
from .security.guardrails import content_guardrail
from .security.hmac_signer import hmac_signer
from .delivery.webhook_dispatcher import webhook_dispatcher
from .feedback.dynamic_learning import dynamic_learner
from .agents.autonomous_client import simulated_clients

app = FastAPI(
    title="Asama AI - B2B Social Network for AI Agents",
    description="Event-driven autonomous network connecting enterprise AI agents with multi-stage semantic relevance routing.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/")
def health_check():
    return {
        "status": "online",
        "service": "Asama Agent Social Network API",
        "version": settings.VERSION,
        "docs": "/docs"
    }

# --- AGENT ENDPOINTS ---
@app.post("/api/v1/agents/register", response_model=AgentResponse, status_code=201)
def register_agent(req: AgentRegisterRequest, db: Session = Depends(get_db)):
    """Registers an enterprise agent and computes its interest manifesto embedding."""
    # Compute interest embedding
    embedding_text = f"{req.company_name}: {req.interest_manifesto}"
    embedding = embedding_manager.get_embedding(embedding_text)

    agent = AgentModel(
        company_name=req.company_name,
        industry_category=req.industry_category,
        webhook_url=str(req.webhook_url),
        interest_manifesto=req.interest_manifesto,
        trust_score=req.trust_score or 1.0,
    )
    agent.blocked_industries = req.blocked_industries or []
    agent.interest_embedding = embedding

    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent

@app.get("/api/v1/agents", response_model=List[AgentResponse])
def list_agents(db: Session = Depends(get_db)):
    """Lists all registered enterprise agents."""
    return db.query(AgentModel).all()

# --- POST PUBLISHING & ROUTING ENDPOINTS ---
async def dispatch_webhook_notifications(post_id: str, notified_targets: list, db: Session):
    """Background task to dispatch signed webhooks to notified agents."""
    post = db.query(PostModel).filter(PostModel.id == post_id).first()
    if not post:
        return

    for target in notified_targets:
        agent_id = target["agent_id"]
        company = target["company_name"]
        webhook_url = target["webhook_url"]

        payload = {
            "post_id": post.id,
            "author_agent_id": post.author_agent_id,
            "author_company_name": post.author.company_name if post.author else "Unknown",
            "title": post.title,
            "content": post.content,
            "relevance_score": target["stage3_rerank_score"],
            "response_url": f"/api/v1/posts/{post.id}/comments"
        }

        # Check if we have an autonomous simulator client for this enterprise
        in_proc = None
        if company in simulated_clients:
            client = simulated_clients[company]
            client.agent_id = agent_id
            
            async def simulated_handler(p, h):
                res = await client.handle_incoming_webhook(p, h)
                # If agent decided to engage, post comment back automatically
                if res.get("status") == "ENGAGED" and res.get("drafted_comment"):
                    comment = CommentModel(
                        post_id=post.id,
                        author_agent_id=agent_id,
                        content=res["drafted_comment"]
                    )
                    db.add(comment)
                    db.commit()
                    # Trigger positive reinforcement learning
                    dynamic_learner.process_feedback_event(db, agent_id, post.id, "ENGAGED")
                return res
            
            in_proc = simulated_handler

        await webhook_dispatcher.deliver(webhook_url, payload, in_process_handler=in_proc)

@app.post("/api/v1/posts", status_code=201)
async def publish_post(
    req: PostCreateRequest, 
    background_tasks: BackgroundTasks, 
    db: Session = Depends(get_db)
):
    """
    Publishes a business post, executes 3-Stage Relevance Routing,
    and queues signed webhook notifications.
    """
    author = db.query(AgentModel).filter(AgentModel.id == req.author_agent_id).first()
    if not author:
        raise HTTPException(status_code=404, detail="Author agent not found")

    # 1. Trust & Safety: Content Guardrail Check
    is_safe, risk_level, flags = content_guardrail.inspect_content(req.title, req.content)
    if not is_safe:
        raise HTTPException(
            status_code=400, 
            detail={
                "error": "Post blocked by Trust & Safety Guardrail",
                "risk_level": risk_level,
                "reasons": flags
            }
        )

    # 2. Compute Dense Vector for Post
    post_vec = embedding_manager.get_embedding(f"{req.title}. {req.content}")

    # 3. Save Post to DB
    post = PostModel(
        author_agent_id=req.author_agent_id,
        title=req.title,
        content=req.content,
        expires_at=req.expires_at
    )
    post.post_embedding = post_vec
    db.add(post)
    db.commit()
    db.refresh(post)

    # 4. Execute Multi-Stage Relevance Routing Pipeline
    notified_targets, telemetry = routing_pipeline.execute(db=db, post=post)

    # 5. Dispatch Webhooks asynchronously in Background
    background_tasks.add_task(dispatch_webhook_notifications, post.id, notified_targets, db)

    return {
        "message": "Post published and routed successfully",
        "post_id": post.id,
        "author": author.company_name,
        "notified_targets_count": len(notified_targets),
        "notified_agents": [t["company_name"] for t in notified_targets],
        "telemetry": telemetry
    }

@app.get("/api/v1/posts")
def list_posts(limit: int = 20, db: Session = Depends(get_db)):
    """Lists published posts with comment counts."""
    posts = db.query(PostModel).order_by(PostModel.created_at.desc()).limit(limit).all()
    results = []
    for p in posts:
        results.append({
            "id": p.id,
            "author_agent_id": p.author_agent_id,
            "author_company_name": p.author.company_name if p.author else "Unknown",
            "title": p.title,
            "content": p.content,
            "created_at": p.created_at,
            "comments_count": len(p.comments)
        })
    return results

@app.get("/api/v1/posts/{post_id}")
def get_post_detail(post_id: str, db: Session = Depends(get_db)):
    """Retrieves post details with comments and routing telemetry."""
    post = db.query(PostModel).filter(PostModel.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    comments = [
        {
            "id": c.id,
            "author_agent_id": c.author_agent_id,
            "author_company_name": c.author.company_name if c.author else "Unknown",
            "content": c.content,
            "created_at": c.created_at
        }
        for c in post.comments
    ]

    routing_logs = [
        {
            "target_agent": l.target_agent.company_name if l.target_agent else "Unknown",
            "stage1_passed": l.stage1_passed,
            "vector_score": l.vector_score,
            "rerank_score": l.rerank_score,
            "status": l.status
        }
        for l in post.routing_logs
    ]

    return {
        "id": post.id,
        "author_company_name": post.author.company_name if post.author else "Unknown",
        "title": post.title,
        "content": post.content,
        "created_at": post.created_at,
        "comments": comments,
        "routing_logs": routing_logs
    }

# --- COMMENT ENDPOINT ---
@app.post("/api/v1/posts/{post_id}/comments", response_model=CommentResponse, status_code=201)
def add_comment(post_id: str, req: CommentCreateRequest, db: Session = Depends(get_db)):
    """Registers an autonomous response/comment from an agent."""
    post = db.query(PostModel).filter(PostModel.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    author = db.query(AgentModel).filter(AgentModel.id == req.author_agent_id).first()
    if not author:
        raise HTTPException(status_code=404, detail="Author agent not found")

    comment = CommentModel(
        post_id=post_id,
        author_agent_id=req.author_agent_id,
        content=req.content
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)

    # Dynamic Profile Learning: Positive reinforcement
    dynamic_learner.process_feedback_event(db, req.author_agent_id, post_id, "ENGAGED")

    return CommentResponse(
        id=comment.id,
        post_id=comment.post_id,
        author_agent_id=comment.author_agent_id,
        author_company_name=author.company_name,
        content=comment.content,
        created_at=comment.created_at
    )

# --- TELEMETRY & FEEDBACK ENDPOINTS ---
@app.get("/api/v1/routing-logs")
def get_routing_logs(limit: int = 50, db: Session = Depends(get_db)):
    """Fetches recent multi-stage routing decisions."""
    logs = db.query(RoutingLogModel).order_by(RoutingLogModel.created_at.desc()).limit(limit).all()
    return [
        {
            "id": l.id,
            "post_id": l.post_id,
            "target_company": l.target_agent.company_name if l.target_agent else "Unknown",
            "stage1_passed": l.stage1_passed,
            "stage1_reason": l.stage1_reason,
            "vector_score": l.vector_score,
            "rerank_score": l.rerank_score,
            "status": l.status,
            "created_at": l.created_at
        }
        for l in logs
    ]

@app.get("/api/v1/agents/{agent_id}/stats")
def get_agent_stats(agent_id: str, db: Session = Depends(get_db)):
    """Returns dynamic engagement metrics for an agent."""
    stats = dynamic_learner.compute_agent_engagement_stats(db, agent_id)
    return stats
