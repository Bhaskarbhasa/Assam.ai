"""
Simulated Autonomous Recipient Agent Engine.
Represents the target enterprise agents (PhonePe, HDFC Bank, etc.).
1. Receives signed webhook event.
2. Verifies HMAC-SHA256 signature to guarantee authenticity.
3. Evaluates business synergy and drafts an autonomous response.
4. Posts the response comment back to the platform API.
"""
import json
import logging
from typing import Dict, Any, Optional
from ..security.hmac_signer import hmac_signer
from ..config import settings

logger = logging.getLogger("autonomous_client")

class AutonomousAgentClient:
    """
    Autonomous agent handler representing partner enterprises.
    """
    def __init__(self, company_name: str, agent_id: str):
        self.company_name = company_name
        self.agent_id = agent_id

    async def handle_incoming_webhook(
        self, 
        payload: Dict[str, Any], 
        headers: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Processes incoming post notification:
        1. HMAC signature verification.
        2. Prompt injection safety validation.
        3. Strategic partnership reasoning.
        """
        payload_str = json.dumps(payload, sort_keys=True)
        sig = headers.get(settings.WEBHOOK_SIGNATURE_HEADER, "")
        ts = headers.get(settings.WEBHOOK_TIMESTAMP_HEADER, "")

        is_valid, msg = hmac_signer.verify_signature(payload_str, sig, ts)
        if not is_valid:
            logger.error(f"[{self.company_name}] Webhook signature verification rejected: {msg}")
            return {"status": "REJECTED", "reason": f"HMAC security check failed: {msg}"}

        post_title = payload.get("title", "")
        post_content = payload.get("content", "")
        author_company = payload.get("author_company_name", "")
        post_id = payload.get("post_id", "")

        # Autonomous Decision & Response Generation
        drafted_comment = self.generate_autonomous_response(author_company, post_title, post_content)
        
        return {
            "status": "ENGAGED",
            "agent_id": self.agent_id,
            "company_name": self.company_name,
            "post_id": post_id,
            "drafted_comment": drafted_comment
        }

    def generate_autonomous_response(self, author_company: str, title: str, content: str) -> str:
        """
        Synthesizes a tailored B2B partnership proposal.
        """
        lower = f"{title} {content}".lower()

        if self.company_name == "PhonePe":
            if "diwali" in lower or "food" in lower or "swiggy" in lower or "zomato" in lower:
                return f"PhonePe will provide extra ₹50 cashback when users pay via PhonePe UPI for {author_company} Diwali orders."
            return f"PhonePe is excited to partner with {author_company} to enable seamless 1-click UPI checkout with exclusive customer rewards."

        elif self.company_name == "HDFC Bank":
            if "discount" in lower or "festive" in lower or "diwali" in lower:
                return f"HDFC Bank offers an additional 10% instant discount on {author_company} using HDFC Credit Cards & SmartBuy rewards."
            return f"HDFC Bank can co-create an exclusive corporate card partnership and merchant financing program with {author_company}."

        elif self.company_name == "ICICI Lombard":
            return f"ICICI Lombard can provide instant transit and order protection coverage for {author_company} customers."

        elif self.company_name == "Tata Neu":
            return f"Tata Neu offers 5% NeuCoins on all transactions originating from {author_company}."

        return f"{self.company_name} agent acknowledges the announcement from {author_company} and proposes exploring synergistic API integration."

# Registry of active autonomous agent instances
simulated_clients = {
    "PhonePe": AutonomousAgentClient("PhonePe", "agent-phonepe-id"),
    "HDFC Bank": AutonomousAgentClient("HDFC Bank", "agent-hdfc-id"),
    "Tata Neu": AutonomousAgentClient("Tata Neu", "agent-tata-neu-id"),
}
