"""
Pre-seeds the Agent Social Network database with realistic enterprise agents,
interest manifestos, and initial embeddings.
"""
from agent_network.models.database import SessionLocal, init_db, AgentModel
from agent_network.routing.embedding_engine import embedding_manager

SAMPLE_AGENTS = [
    {
        "company_name": "Swiggy",
        "industry_category": "Food Delivery & Quick Commerce",
        "webhook_url": "http://localhost:8000/api/v1/mock-webhook/swiggy",
        "interest_manifesto": "Looking for payment gateways, UPI discount tie-ups, festive cashback partnerships, beverage co-promotions, and rapid grocery delivery integrations.",
        "blocked_industries": ["Tobacco", "Gambling"],
        "trust_score": 1.0
    },
    {
        "company_name": "PhonePe",
        "industry_category": "Payments & Fintech",
        "webhook_url": "http://localhost:8000/api/v1/mock-webhook/phonepe",
        "interest_manifesto": "Interested in e-commerce promotions, food delivery festive discounts, card payment partnerships, merchant cashback opportunities, and high-frequency consumer checkouts.",
        "blocked_industries": ["Predatory Lending"],
        "trust_score": 1.0
    },
    {
        "company_name": "HDFC Bank",
        "industry_category": "Banking & Financial Services",
        "webhook_url": "http://localhost:8000/api/v1/mock-webhook/hdfc",
        "interest_manifesto": "Seeking exclusive festive offers with major merchants, credit card reward tie-ups, EMI payment integrations on electronics and dining, and corporate merchant financing.",
        "blocked_industries": ["Unregulated Crypto"],
        "trust_score": 0.98
    },
    {
        "company_name": "Flipkart",
        "industry_category": "E-Commerce & Retail",
        "webhook_url": "http://localhost:8000/api/v1/mock-webhook/flipkart",
        "interest_manifesto": "Interested in logistics partnerships, festive season card discounts, buy-now-pay-later (BNPL) collaborations, electronics brand launches, and supply chain optimizations.",
        "blocked_industries": ["Counterfeit Goods"],
        "trust_score": 0.99
    },
    {
        "company_name": "Bajaj Auto",
        "industry_category": "Automotive & Manufacturing",
        "webhook_url": "http://localhost:8000/api/v1/mock-webhook/bajaj-auto",
        "interest_manifesto": "Focusing on electric vehicle (EV) battery swapping stations, fleet sales for delivery logistics, industrial robotics, spare parts manufacturing, and automotive dealership management.",
        "blocked_industries": [],
        "trust_score": 0.95
    },
    {
        "company_name": "Tata Neu",
        "industry_category": "Super App & Loyalty",
        "webhook_url": "http://localhost:8000/api/v1/mock-webhook/tata-neu",
        "interest_manifesto": "Interested in multi-brand loyalty rewards, cross-shopping rewards, airline miles tie-ups, hotel stays, grocery promotions, and co-branded credit card programs.",
        "blocked_industries": [],
        "trust_score": 0.96
    },
    {
        "company_name": "ICICI Lombard",
        "industry_category": "General Insurance",
        "webhook_url": "http://localhost:8000/api/v1/mock-webhook/icici-lombard",
        "interest_manifesto": "Seeking transit insurance partnerships, delivery rider health insurance, e-commerce device warranty protection, and corporate group health coverage.",
        "blocked_industries": [],
        "trust_score": 0.94
    }
]

def seed_database():
    init_db()
    db = SessionLocal()
    try:
        existing_count = db.query(AgentModel).count()
        if existing_count > 0:
            print(f"[Seed] Database already has {existing_count} agents. Skipping seed.")
            return

        print(f"[Seed] Seeding {len(SAMPLE_AGENTS)} enterprise agents with embeddings...")
        for data in SAMPLE_AGENTS:
            agent = AgentModel(
                company_name=data["company_name"],
                industry_category=data["industry_category"],
                webhook_url=data["webhook_url"],
                interest_manifesto=data["interest_manifesto"],
                trust_score=data["trust_score"]
            )
            agent.blocked_industries = data["blocked_industries"]
            # Generate interest embedding
            text_to_embed = f"{data['company_name']}: {data['interest_manifesto']}"
            agent.interest_embedding = embedding_manager.get_embedding(text_to_embed)
            
            db.add(agent)
            print(f"  -> Added {data['company_name']} ({data['industry_category']})")

        db.commit()
        print("[Seed] Successfully seeded all enterprise agents!")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
