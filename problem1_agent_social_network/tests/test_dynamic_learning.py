"""
Unit Tests for Closed-Loop Feedback and Dynamic Profile Learning.
"""
import pytest
import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.database import Base, AgentModel, PostModel, RoutingLogModel, CommentModel
from app.feedback.dynamic_learning import dynamic_learner
from app.routing.embedding_engine import embedding_manager

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    agent = AgentModel(
        company_name="TestBank",
        industry_category="Banking",
        webhook_url="http://test/bank",
        interest_manifesto="Banking, credit cards and loans",
        trust_score=1.0
    )
    initial_vec = np.ones(384, dtype=np.float32)
    initial_vec = initial_vec / np.linalg.norm(initial_vec)
    agent.interest_embedding = initial_vec
    session.add(agent)
    session.flush()

    author = AgentModel(
        company_name="AutoVendor",
        industry_category="Automotive",
        webhook_url="http://test/vendor",
        interest_manifesto="Vehicle parts",
        trust_score=1.0
    )
    session.add(author)
    session.flush()

    post = PostModel(
        author_agent_id=author.id,
        title="Automobile Tyres Clearance",
        content="Heavy discounts on vehicle tyres"
    )
    post_vec = np.zeros(384, dtype=np.float32)
    post_vec[0] = 1.0  # orthogonal dimension
    post.post_embedding = post_vec
    session.add(post)
    session.flush()

    log = RoutingLogModel(
        post_id=post.id,
        target_agent_id=agent.id,
        status="NOTIFIED"
    )
    session.add(log)
    session.commit()

    yield session
    session.close()

def test_negative_gradient_shift_on_ignore(db_session):
    agent = db_session.query(AgentModel).first()
    post = db_session.query(PostModel).first()
    
    vec_before = agent.interest_embedding.copy()
    cos_sim_before = embedding_manager.compute_cosine_similarity(vec_before, post.post_embedding)

    # Process IGNORED feedback
    success, msg, details = dynamic_learner.process_feedback_event(
        db_session, agent.id, post.id, "IGNORED"
    )

    assert success is True
    assert details["shift_type"] == "NEGATIVE_GRADIENT_SHIFT"

    db_session.refresh(agent)
    vec_after = agent.interest_embedding
    cos_sim_after = embedding_manager.compute_cosine_similarity(vec_after, post.post_embedding)

    # Cosine similarity to the unengaged post must decrease!
    assert cos_sim_after <= cos_sim_before

def test_positive_reinforcement_on_engagement(db_session):
    agent = db_session.query(AgentModel).first()
    post = db_session.query(PostModel).first()

    vec_before = agent.interest_embedding.copy()
    cos_sim_before = embedding_manager.compute_cosine_similarity(vec_before, post.post_embedding)

    # Process ENGAGED feedback
    success, msg, details = dynamic_learner.process_feedback_event(
        db_session, agent.id, post.id, "ENGAGED"
    )

    assert success is True
    assert details["shift_type"] == "POSITIVE_REINFORCEMENT"

    db_session.refresh(agent)
    vec_after = agent.interest_embedding
    cos_sim_after = embedding_manager.compute_cosine_similarity(vec_after, post.post_embedding)

    # Cosine similarity to the engaged post must increase!
    assert cos_sim_after >= cos_sim_before

def test_engagement_rate_statistics(db_session):
    agent = db_session.query(AgentModel).first()
    post = db_session.query(PostModel).first()

    stats_initial = dynamic_learner.compute_agent_engagement_stats(db_session, agent.id)
    assert stats_initial["total_notified"] == 1
    assert stats_initial["total_engaged"] == 0
    assert stats_initial["engagement_rate"] == 0.0

    # Add comment to simulate engagement
    comment = CommentModel(
        post_id=post.id,
        author_agent_id=agent.id,
        content="We offer 5% cashback on tyres"
    )
    db_session.add(comment)
    db_session.commit()

    stats_engaged = dynamic_learner.compute_agent_engagement_stats(db_session, agent.id)
    assert stats_engaged["total_notified"] == 1
    assert stats_engaged["total_engaged"] == 1
    assert stats_engaged["engagement_rate"] == 1.0
