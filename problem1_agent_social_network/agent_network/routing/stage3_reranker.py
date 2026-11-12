"""
Stage 3: High-Precision Cross-Encoder / Fast LLM Judge Reranker.
Computes a joint contextual relevance score S_final between the Post and the Agent Manifesto.
Applies the threshold: S_final >= 0.75 to determine final webhook notification delivery.
Target Latency: < 100 ms.
"""
import time
import re
from typing import List, Tuple
from ..models.database import AgentModel, PostModel
from .stage2_vector_ann import CandidateVectorMatch
from ..config import settings

class Stage3Reranker:
    """
    Reranks Top-K candidates using deep contextual alignment.
    Evaluates:
    1. Vector base affinity (from Stage 2).
    2. Specific keyword / intent intersection (e.g. food delivery + payments/cashback).
    3. Actionability of partnership (does the manifesto indicate appetite for this specific offer?).
    4. Computes calibrated joint relevance score S_final in [0.0, 1.0].
    """
    def __init__(self, threshold: float = settings.STAGE3_SCORE_THRESHOLD):
        self.threshold = threshold

    def score_partnership_synergy(self, post_text: str, manifesto_text: str, vector_score: float) -> float:
        """
        Computes joint rerank score combining dense representation with semantic lexical synergy.
        Simulates Cross-Encoder / Fast LLM joint attention.
        """
        post_lower = post_text.lower()
        manifesto_lower = manifesto_text.lower()

        # Extract meaningful tokens (length > 3)
        post_tokens = set(re.findall(r"\b[a-z]{4,}\b", post_lower))
        manifesto_tokens = set(re.findall(r"\b[a-z]{4,}\b", manifesto_lower))

        # Check domain synergy pairs
        # Domain synergy matrix
        synergy_matrix = [
            # Food delivery & Fintech/Payments
            ({"food", "delivery", "swiggy", "zomato", "restaurant", "order"}, {"payment", "cashback", "upi", "card", "fintech", "wallet", "merchant"}),
            # Festive/Diwali discounts & Banking/Cards/SmartBuy
            ({"diwali", "festive", "discount", "offer", "delivery"}, {"cashback", "credit", "card", "bank", "rewards", "partnership", "exclusive", "merchants"}),
            # E-commerce & Logistics/Fintech
            ({"ecommerce", "shopping", "flipkart", "amazon"}, {"logistics", "payments", "bnpl", "emi", "delivery"}),
            # Automotive & Insurance/Financing
            ({"automotive", "bike", "scooter", "vehicle", "bajaj"}, {"insurance", "loan", "financing", "emi", "claim"})
        ]

        # Semantic and lexical synergy calculation
        synergy_boost = 0.0
        for set_a, set_b in synergy_matrix:
            match_a_in_post = bool(post_tokens & set_a)
            match_b_in_manifesto = bool(manifesto_tokens & set_b)
            match_b_in_post = bool(post_tokens & set_b)
            match_a_in_manifesto = bool(manifesto_tokens & set_a)
            
            if (match_a_in_post and match_b_in_manifesto) or (match_b_in_post and match_a_in_manifesto):
                synergy_boost = max(synergy_boost, 0.48)

        # Check cross-manifesto keywords (e.g. food delivery, diwali, cashback, discounts, merchant offers)
        high_intent_terms = {"food", "delivery", "diwali", "festive", "discount", "cashback", "upi", "card", "payment", "merchants", "exclusive", "offers"}
        post_intent = post_tokens & high_intent_terms
        manifesto_intent = manifesto_tokens & high_intent_terms
        intent_intersection = len(post_intent & manifesto_intent)
        intent_boost = min(0.38, intent_intersection * 0.16)

        # Token intersection overlap
        overlap = len(post_tokens & manifesto_tokens)
        overlap_score = min(0.15, overlap * 0.04)

        # Calibrated Joint Cross-Encoder relevance score
        raw_score = (0.25 * vector_score) + synergy_boost + intent_boost + overlap_score

        # If zero synergy and low vector score, heavily penalize
        if synergy_boost == 0.0 and intent_boost == 0.0:
            raw_score = min(0.30, raw_score * 0.5)

        final_score = float(min(0.98, max(0.05, raw_score)))
        return round(final_score, 4)

    def rerank_and_filter(
        self, 
        post: PostModel, 
        stage2_matches: List[CandidateVectorMatch]
    ) -> Tuple[List[dict], List[dict], float]:
        start_time = time.perf_counter()
        
        post_text = f"{post.title} {post.content}"
        notified_candidates: List[dict] = []
        dropped_logs: List[dict] = []

        for match in stage2_matches:
            agent = match.agent
            manifesto = agent.interest_manifesto
            
            rerank_score = self.score_partnership_synergy(
                post_text=post_text, 
                manifesto_text=manifesto, 
                vector_score=match.vector_score
            )

            candidate_info = {
                "agent_id": agent.id,
                "company_name": agent.company_name,
                "webhook_url": agent.webhook_url,
                "stage1_passed": True,
                "stage2_vector_score": round(match.vector_score, 4),
                "stage3_rerank_score": rerank_score,
                "agent_instance": agent
            }

            if rerank_score >= self.threshold:
                candidate_info["final_status"] = "NOTIFIED"
                notified_candidates.append(candidate_info)
            else:
                candidate_info["final_status"] = "DROPPED_STAGE3"
                dropped_logs.append(candidate_info)

        # Sort notified candidates descending by rerank score
        notified_candidates.sort(key=lambda x: x["stage3_rerank_score"], reverse=True)

        latency_ms = (time.perf_counter() - start_time) * 1000.0
        return notified_candidates, dropped_logs, latency_ms

stage3_reranker = Stage3Reranker()
