"""
Stage 2: Hybrid Dense Vector & ANN Search.
Queries nearest agent interest vectors using Cosine Similarity on dense embeddings.
Retrieves Top K candidates (default K=50).
Target Latency: < 15 ms.
"""
import time
from typing import List, Tuple
import numpy as np
from ..models.database import AgentModel, PostModel
from .embedding_engine import embedding_manager
from ..config import settings

class CandidateVectorMatch:
    def __init__(self, agent: AgentModel, vector_score: float):
        self.agent = agent
        self.vector_score = vector_score

class Stage2VectorANN:
    """
    Computes dense cosine similarity between incoming post embedding and eligible agents.
    Returns ranked Top K candidates.
    """
    def search_nearest(
        self, 
        post: PostModel, 
        candidates: List[AgentModel], 
        top_k: int = settings.STAGE2_TOP_K
    ) -> Tuple[List[CandidateVectorMatch], List[dict], float]:
        start_time = time.perf_counter()
        
        post_vec = post.post_embedding
        if post_vec is None:
            post_vec = embedding_manager.get_embedding(f"{post.title}. {post.content}")
            post.post_embedding = post_vec

        scored_candidates: List[CandidateVectorMatch] = []
        for agent in candidates:
            agent_vec = agent.interest_embedding
            if agent_vec is None:
                agent_vec = embedding_manager.get_embedding(f"{agent.company_name} {agent.interest_manifesto}")
                agent.interest_embedding = agent_vec

            score = embedding_manager.compute_cosine_similarity(post_vec, agent_vec)
            scored_candidates.append(CandidateVectorMatch(agent=agent, vector_score=score))

        # Rank candidates by descending cosine similarity
        scored_candidates.sort(key=lambda x: x.vector_score, reverse=True)

        # Slice Top K
        top_matches = scored_candidates[:top_k]
        dropped_matches = scored_candidates[top_k:]

        dropped_logs = [
            {
                "agent_id": m.agent.id,
                "company_name": m.agent.company_name,
                "stage1_passed": True,
                "stage2_vector_score": round(m.vector_score, 4),
                "final_status": "DROPPED_STAGE2"
            }
            for m in dropped_matches
        ]

        latency_ms = (time.perf_counter() - start_time) * 1000.0
        return top_matches, dropped_logs, latency_ms

stage2_vector_ann = Stage2VectorANN()
