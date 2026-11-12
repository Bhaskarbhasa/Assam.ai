"""
HMAC-SHA256 Security & Verification Module.
Signs outgoing webhook notifications and validates signatures to guarantee payload authenticity
and protect against tampering and replay attacks.
"""
import hmac
import hashlib
import time
from typing import Dict, Tuple
from ..config import settings

class HMACSigner:
    def __init__(self, secret_key: str = settings.HMAC_SECRET_KEY):
        self.secret_key = secret_key.encode("utf-8")

    def generate_signature(self, payload_str: str, timestamp: str) -> str:
        """
        Generates HMAC-SHA256 signature for: timestamp + '.' + payload_str
        """
        canonical_string = f"{timestamp}.{payload_str}".encode("utf-8")
        signature = hmac.new(self.secret_key, canonical_string, hashlib.sha256).hexdigest()
        return signature

    def build_signed_headers(self, payload_str: str) -> Dict[str, str]:
        """
        Returns the HTTP headers to attach to webhook requests.
        """
        timestamp = str(int(time.time()))
        signature = self.generate_signature(payload_str, timestamp)
        return {
            "Content-Type": "application/json",
            settings.WEBHOOK_SIGNATURE_HEADER: signature,
            settings.WEBHOOK_TIMESTAMP_HEADER: timestamp,
        }

    def verify_signature(
        self, 
        payload_str: str, 
        signature: str, 
        timestamp: str, 
        max_age_seconds: int = 300
    ) -> Tuple[bool, str]:
        """
        Verifies HMAC signature and protects against replay attacks by checking timestamp freshness.
        """
        if not signature or not timestamp:
            return False, "Missing signature or timestamp header"

        # Check timestamp age (replay protection)
        try:
            ts_int = int(timestamp)
            current_time = int(time.time())
            if abs(current_time - ts_int) > max_age_seconds:
                return False, f"Timestamp expired or skew too large ({abs(current_time - ts_int)}s > {max_age_seconds}s)"
        except ValueError:
            return False, "Invalid timestamp format"

        # Compute expected signature
        expected_sig = self.generate_signature(payload_str, timestamp)
        
        # Constant-time comparison to prevent timing attacks
        is_valid = hmac.compare_digest(expected_sig, signature)
        if not is_valid:
            return False, "Signature mismatch"

        return True, "Valid"

hmac_signer = HMACSigner()
