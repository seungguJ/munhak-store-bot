"""웹푸시 전송 (VAPID)."""
import json

from pywebpush import WebPushException, webpush

EXPIRED_STATUS = {404, 410}  # 구독 해지/만료


def send_all(alerts, subscriptions, vapid_private_key, subject):
    """모든 구독에 모든 알림 전송. 만료된 구독 endpoint 목록 반환."""
    expired = []
    for sub in subscriptions:
        for alert in alerts:
            try:
                webpush(
                    subscription_info=sub,
                    data=json.dumps(alert, ensure_ascii=False),
                    vapid_private_key=vapid_private_key,
                    vapid_claims={"sub": subject},
                    ttl=24 * 3600,
                )
            except WebPushException as err:
                status = getattr(err.response, "status_code", None)
                if status in EXPIRED_STATUS:
                    expired.append(sub["endpoint"])
                    break
                raise
    return expired
