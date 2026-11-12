"""
Multi-Stage Relevance Routing Pipeline Orchestrator.
Coordinates:
Stage 1 (SQL Metadata Guardrails) -> Stage 2 (Dense Vector ANN) -> Stage 3 (Reranker/Judge)
and persists routing logs for closed-loop dynamic learning.
"""
import time
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from ..models.database import AgentModel, PostModel, RoutingLogModel
from ..models.schemas import RoutingTelemetry, CandidateStageScore
from .stage1_sql_filter import stage1_filter
from .stage2_vector_ann import stage2_vector_ann
from .stage3_reranker import stage3_reranker

class RelevanceRoutingPipeline:
    """
    Executes the 3-stage candidate filtering pipeline.
    """
    def execute(
        self, 
        db: Session, 
        post: PostModel
    ) -> Tuple[List[dict], RoutingTelemetry]:
        pipeline_start = time.perf_counter()
        
        author = db.query(AgentModel).filter(AgentModel.id == post.author_agent_id).first()
        total_registered = db.query(AgentModel).count()

        # --- STAGE 1: Fast SQL Guardrails (< 2ms) ---
        stage1_eligible, stage1_dropped, stage1_ms = stage1_filter.filter_candidates(
            db=db, post=post, author=author
        )

        # --- STAGE 2: Dense Vector ANN Retrieval (< 15ms) ---
        stage2_matches, stage2_dropped, stage2_ms = stage2_vector_ann.search_nearest(
            post=post, candidates=stage1_eligible
        )

        # --- STAGE 3: High-Precision Reranker / LLM Judge (< 100ms) ---
        stage3_notified, stage3_dropped, stage3_ms = stage3_reranker.rerank_and_filter(
            post=post, stage2_matches=stage2_matches
        )

        total_pipeline_ms = (time.perf_counter() - pipeline_start) * 1000.0

        # Build candidate score list for explainability
        all_candidate_reports: List[CandidateStageScore] = []

        # Record Stage 1 drops
        for item in stage1_dropped:
            all_candidate_reports.append(CandidateStageScore(
                agent_id=item["agent_id"],
                company_name=item["company_name"],
                stage1_passed=False,
                stage1_reason=item["stage1_reason"],
                stage2_vector_score=None,
                stage3_rerank_score=None,
                final_status="DROPPED_STAGE1"
            ))
            # Persist to routing_logs
            db.add(RoutingLogModel(
                post_id=post.id,
                target_agent_id=item["agent_id"],
                stage1_passed=False,
                stage1_reason=item["stage1_reason"],
                vector_score=0.0,
                rerank_score=0.0,
                status="DROPPED_STAGE1"
            ))

        # Record Stage 2 drops
        for item in stage2_dropped:
            all_candidate_reports.append(CandidateStageScore(
                agent_id=item["agent_id"],
                company_name=item["company_name"],
                stage1_passed=True,
                stage2_vector_score=item["stage2_vector_score"],
                stage3_rerank_score=None,
                final_status="DROPPED_STAGE2"
            ))
            db.add(RoutingLogModel(
                post_id=post.id,
                target_agent_id=item["agent_id"],
                stage1_passed=True,
                vector_score=item["stage2_vector_score"],
                rerank_score=0.0,
                status="DROPPED_STAGE2"
            ))

        # Record Stage 3 drops
        for item in stage3_dropped:
            all_candidate_reports.append(CandidateStageScore(
                agent_id=item["agent_id"],
                company_name=item["company_name"],
                stage1_passed=True,
                stage2_vector_score=item["stage2_vector_score"],
                stage3_rerank_score=item["stage3_rerank_score"],
                final_status="DROPPED_STAGE3"
            ))
            db.add(RoutingLogModel(
                post_id=post.id,
                target_agent_id=item["agent_id"],
                stage1_passed=True,
                vector_score=item["stage2_vector_score"],
                rerank_score=item["stage3_rerank_score"],
                status="DROPPED_STAGE3"
            ))

        # Record Final Notified Targets
        for item in stage3_notified:
            all_candidate_reports.append(CandidateStageScore(
                agent_id=item["agent_id"],
                company_name=item["company_name"],
                stage1_passed=True,
                stage2_vector_score=item["stage2_vector_score"],
                stage3_rerank_score=item["stage3_rerank_score"],
                final_status="NOTIFIED"
            ))
            db.add(RoutingLogModel(
                post_id=post.id,
                target_agent_id=item["agent_id"],
                stage1_passed=True,
                vector_score=item["stage2_vector_score"],
                rerank_score=item["stage3_rerank_score"],
                status="NOTIFIED"
            ))

        db.commit()

        telemetry = RoutingTelemetry(
            post_id=post.id,
            total_registered_agents=total_registered,
            stage1_eligible_count=len(stage1_eligible),
            stage1_latency_ms=round(stage1_ms, 2),
            stage2_top_k_count=len(stage2_matches),
            stage2_latency_ms=round(stage2_ms, 2),
            stage3_notified_count=len(stage3_notified),
            stage3_latency_ms=round(stage3_ms, 2),
            total_pipeline_latency_ms=round(total_pipeline_ms, 2),
            candidates=all_candidate_reports
        )

        return stage3_notified, telemetry

routing_pipeline = RelevanceRoutingPipeline()
