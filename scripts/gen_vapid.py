"""VAPID 키 쌍 생성 (로컬 1회).

    python scripts/gen_vapid.py

- PUBLIC  → web/config.js 의 VAPID_PUBLIC_KEY 에 붙여넣기 (공개해도 됨)
- PRIVATE → GitHub Secret VAPID_PRIVATE_KEY 에만 등록 (절대 커밋 금지)
"""
import base64

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec


def b64url(raw):
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


key = ec.generate_private_key(ec.SECP256R1())
private_raw = key.private_numbers().private_value.to_bytes(32, "big")
public_raw = key.public_key().public_bytes(
    serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
print("PUBLIC  =", b64url(public_raw))
print("PRIVATE =", b64url(private_raw))
