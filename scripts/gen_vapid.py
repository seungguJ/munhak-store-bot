"""VAPID 키 쌍 생성. 보통은 scripts/setup_push.py 를 쓰면 된다.

    python scripts/gen_vapid.py

- PUBLIC  → web/config.js 의 VAPID_PUBLIC_KEY (공개해도 됨)
- PRIVATE → GitHub Secret VAPID_PRIVATE_KEY 에만 등록 (절대 커밋 금지)
"""
import base64

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec


def _b64url(raw):
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def generate():
    """(public, private) — 둘 다 base64url."""
    key = ec.generate_private_key(ec.SECP256R1())
    private_raw = key.private_numbers().private_value.to_bytes(32, "big")
    public_raw = key.public_key().public_bytes(
        serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
    return _b64url(public_raw), _b64url(private_raw)


if __name__ == "__main__":
    public, private = generate()
    print("PUBLIC  =", public)
    print("PRIVATE =", private)
