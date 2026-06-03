import hmac
import hashlib


def verify_hmac_sha256(payload: bytes, secret: str, signature: str) -> bool:
    if not signature or not secret:
        return False
    mac = hmac.new(secret.encode(), msg=payload, digestmod=hashlib.sha256)
    expected = f"sha256={mac.hexdigest()}"
    return hmac.compare_digest(expected, signature)
