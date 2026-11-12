"""
Stage 1: Fast SQL Metadata Guardrails.
Filters candidate agents using relational rules before any compute-heavy ML stages.
Target Latency: < 2 ms.
"""
import time
from typing import List, Tuple
from sqlalchemy.orm import Session
from ..models.database import AgentModel, PostModel

class Stage1SQLFilter:
    """
    Applies hard relational filters:
    1. Excludes the publishing author agent itself (no self-loops).
    2. Excludes deactivated / suspended agents (is_active == False).
    3. Excludes agents below minimum trust score (< 0.5).
    4. Excludes agents with explicit industry blocklists matching author's industry.
    """
    def filter_candidates(
        self, 
        db: Session, 
        post: PostModel, 
        author: AgentModel
    ) -> Tuple[List[AgentModel], List[dict], float]:
        start_time = time.perf_counter()
        
        # Query active agents excluding author
        query = db.query(AgentModel).filter(
            AgentModel.id != post.author_agent_id,
            AgentModel.is_active == True,
            AgentModel.trust_score >= 0.5
        )
        
        all_candidates = query.all()
        eligible_agents: List[AgentModel] = []
        dropped_logs: List[dict] = []
        
        author_industry = author.industry_category.lower() if author else ""

        for agent in all_candidates:
            # Check domain / industry blocklists
            blocked = [ind.lower() for ind in agent.blocked_industries]
            if author_industry in blocked:
                dropped_logs.append({
                    "agent_id": agent.id,
                    "company_name": agent.company_name,
                    "stage1_passed": False,
                    "stage1_reason": f"Author industry '{author.industry_category}' is in agent blocklist",
                    "final_status": "DROPPED_STAGE1"
                })
            else:
                eligible_agents.append(agent)

        latency_ms = (time.perf_counter() - start_time) * 1000.0
        return eligible_agents, dropped_logs, latency_ms

stage1_filter = Stage1SQLFilter()
