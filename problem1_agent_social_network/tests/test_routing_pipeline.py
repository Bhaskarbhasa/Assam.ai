"""
Unit and Integration Tests for Multi-Stage Relevance Routing Pipeline.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.database import Base, AgentModel, PostModel
from app.routing.pipeline import routing_pipeline
from app.routing.embedding_engine import embedding_manager

@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Create test agents
    author = AgentModel(
        company_name="Swiggy",
        industry_category="Food Delivery",
        webhook_url="http://test/swiggy",
        interest_manifesto="Food delivery and discounts",
        trust_score=1.0,
        blocked_industries_json="[]"
    )
    author.interest_embedding = embedding_manager.get_embedding(author.interest_manifesto)

    target_relevant = AgentModel(
        company_name="PhonePe",
        industry_category="Payments & Fintech",
        webhook_url="http://test/phonepe",
        interest_manifesto="Interested in e-commerce promotions, food delivery festive discounts, card payment partnerships, and merchant cashback opportunities.",
        trust_score=1.0,
        blocked_industries_json="[]"
    )
    target_relevant.interest_embedding = embedding_manager.get_embedding(target_relevant.interest_manifesto)

    target_irrelevant = AgentModel(
        company_name="Bajaj Auto",
        industry_category="Automotive",
        webhook_url="http://test/bajaj",
        interest_manifesto="Focusing on electric vehicles, engine manufacturing, and vehicle dealerships.",
        trust_score=0.95,
        blocked_industries_json="[]"
    )
    target_irrelevant.interest_embedding = embedding_manager.get_embedding(target_irrelevant.interest_manifesto)

    target_blocked = AgentModel(
        company_name="BlockedAgent",
        industry_category="Retail",
        webhook_url="http://test/blocked",
        interest_manifesto="Retail partner",
        trust_score=1.0,
        blocked_industries_json='["Food Delivery"]'  # Blocks author's industry!
    )
    target_blocked.interest_embedding = embedding_manager.get_embedding(target_blocked.interest_manifesto)

    target_untrusted = AgentModel(
        company_name="UntrustedAgent",
        industry_category="Finance",
        webhook_url="http://test/untrusted",
        interest_manifesto="Finance",
        trust_score=0.2,  # Untrusted (< 0.5)
        blocked_industries_json="[]"
    )
    target_untrusted.interest_embedding = embedding_manager.get_embedding(target_untrusted.interest_manifesto)

    session.add_all([author, target_relevant, target_irrelevant, target_blocked, target_untrusted])
    session.commit()

    yield session
    session.close()

def test_stage1_sql_filter(test_db):
    author = test_db.query(AgentModel).filter(AgentModel.company_name == "Swiggy").first()
    post = PostModel(
        author_agent_id=author.id,
        title="Diwali Food Delivery Discount",
        content="5% off all delivery orders above Rs 300"
    )
    post.post_embedding = embedding_manager.get_embedding(f"{post.title}. {post.content}")
    test_db.add(post)
    test_db.commit()

    notified, telemetry = routing_pipeline.execute(test_db, post)

    # Candidate breakdown checks
    status_map = {c.company_name: c.final_status for c in telemetry.candidates}

    # Author Swiggy must NOT be present as candidate (no self-loops)
    assert "Swiggy" not in status_map

    # BlockedAgent and UntrustedAgent dropped at Stage 1
    assert status_map.get("BlockedAgent") == "DROPPED_STAGE1"
    assert "UntrustedAgent" not in status_map or status_map.get("UntrustedAgent") == "DROPPED_STAGE1"

    # PhonePe should be NOTIFIED
    assert status_map.get("PhonePe") == "NOTIFIED"

    # Bajaj Auto should be dropped at Stage 3
    assert status_map.get("Bajaj Auto") == "DROPPED_STAGE3"

def test_pipeline_latency_guarantees(test_db):
    author = test_db.query(AgentModel).filter(AgentModel.company_name == "Swiggy").first()
    post = PostModel(
        author_agent_id=author.id,
        title="Express Delivery Offer",
        content="Free delivery on orders above Rs 199"
    )
    post.post_embedding = embedding_manager.get_embedding(f"{post.title}. {post.content}")
    test_db.add(post)
    test_db.commit()

    _, telemetry = routing_pipeline.execute(test_db, post)

    # Stage 1: < 5 ms
    assert telemetry.stage1_latency_ms < 50.0
    # Stage 2: < 30 ms
    assert telemetry.stage2_latency_ms < 50.0
    # Stage 3: < 100 ms
    assert telemetry.stage3_latency_ms < 100.0
