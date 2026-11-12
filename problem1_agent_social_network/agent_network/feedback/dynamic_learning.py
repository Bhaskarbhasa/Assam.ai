"""
Closed-Loop Feedback & Dynamic Profile Learning Engine.
Dynamically updates agent interest vectors based on real-world notification engagement.
If an agent consistently ignores notifications on a topic, shifts the preference vector
away using negative gradient descent (v_new = normalize(v_old - alpha * v_post)).
If an agent engages (comments), reinforces the interest vector (v_new = normalize(v_old + beta * v_post)).
"""
import numpy as np
from typing import Dict, Any, Tuple
from sqlalchemy.orm import Session
from ..models.database import AgentModel, PostModel, RoutingLogModel, CommentModel
from ..config import settings

class DynamicProfileLearner:
    def __init__(
        self, 
        alpha_negative: float = settings.DYNAMIC_LEARNING_RATE,
        beta_positive: float = 0.20,
        consecutive_ignores_trigger: int = settings.CONSECUTIVE_IGNORES_TRIGGER
    ):
        self.alpha_negative = alpha_negative
        self.beta_positive = beta_positive
        self.consecutive_ignores_trigger = consecutive_ignores_trigger

    def compute_agent_engagement_stats(self, db: Session, agent_id: str) -> Dict[str, Any]:
        """
        Calculates Engagement Rate R = Comments / Notifications Sent.
        """
        notified_logs = db.query(RoutingLogModel).filter(
            RoutingLogModel.target_agent_id == agent_id,
            RoutingLogModel.status == "NOTIFIED"
        ).all()

        total_notified = len(notified_logs)
        if total_notified == 0:
            return {"total_notified": 0, "total_engaged": 0, "engagement_rate": 0.0}

        # Check how many led to comments
        engaged_count = 0
        for log in notified_logs:
            comment_exists = db.query(CommentModel).filter(
                CommentModel.post_id == log.post_id,
                CommentModel.author_agent_id == agent_id
            ).first()
            if comment_exists:
                engaged_count += 1

        rate = engaged_count / total_notified
        return {
            "total_notified": total_notified,
            "total_engaged": engaged_count,
            "engagement_rate": round(rate, 4)
        }

    def process_feedback_event(
        self, 
        db: Session, 
        agent_id: str, 
        post_id: str, 
        action: str  # "ENGAGED" (commented) or "IGNORED"
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Applies vector gradient shift to update the agent's interest profile.
        """
        agent = db.query(AgentModel).filter(AgentModel.id == agent_id).first()
        post = db.query(PostModel).filter(PostModel.id == post_id).first()

        if not agent or not post:
            return False, "Agent or Post not found", {}

        agent_vec = agent.interest_embedding
        post_vec = post.post_embedding

        if agent_vec is None or post_vec is None:
            return False, "Embeddings missing", {}

        old_norm = np.linalg.norm(agent_vec)
        shift_magnitude = 0.0

        if action == "ENGAGED":
            # Positive Reinforcement: pull interest vector towards post
            # v_new = normalize(v_old + beta * v_post)
            new_vec = agent_vec + (self.beta_positive * post_vec)
            shift_type = "POSITIVE_REINFORCEMENT"
            shift_magnitude = float(np.linalg.norm(new_vec - agent_vec))
        elif action == "IGNORED":
            # Negative Gradient Shift: push interest vector away from ignored post topic
            # v_new = normalize(v_old - alpha * v_post)
            new_vec = agent_vec - (self.alpha_negative * post_vec)
            shift_type = "NEGATIVE_GRADIENT_SHIFT"
            shift_magnitude = float(np.linalg.norm(new_vec - agent_vec))
        else:
            return False, f"Unknown action: {action}", {}

        # Normalize back to unit sphere
        norm = np.linalg.norm(new_vec)
        if norm > 1e-9:
            new_vec = new_vec / norm

        agent.interest_embedding = new_vec

        # Update routing log status
        log = db.query(RoutingLogModel).filter(
            RoutingLogModel.post_id == post_id,
            RoutingLogModel.target_agent_id == agent_id
        ).first()
        if log:
            log.status = action

        db.commit()

        details = {
            "agent_company": agent.company_name,
            "action": action,
            "shift_type": shift_type,
            "shift_magnitude": round(shift_magnitude, 4),
            "updated_vector_norm": round(float(np.linalg.norm(new_vec)), 4)
        }
        return True, f"Updated profile for {agent.company_name}", details

dynamic_learner = DynamicProfileLearner()
