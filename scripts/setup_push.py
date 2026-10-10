"""웹푸시 키 설정 (1회, gh 로그인 필요).

    python scripts/setup_push.py [owner/repo]

- VAPID 키 쌍 생성
- 비밀키 → GitHub Secret VAPID_PRIVATE_KEY (화면에 출력하지 않음)
- VAPID_SUBJECT → GitHub Secret (Pages 주소)
- 공개키 → web/config.js (이후 commit/push)
"""
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gen_vapid import generate  # noqa: E402

repo = sys.argv[1] if len(sys.argv) > 1 else "seungguJ/munhak-store-bot"
owner, name = repo.split("/")
public, private = generate()


def secret(key, value):
    subprocess.run(["gh", "secret", "set", key, "-R", repo], input=value.encode(), check=True)


secret("VAPID_PRIVATE_KEY", private)
secret("VAPID_SUBJECT", "https://%s.github.io" % owner.lower())

config = Path(__file__).resolve().parent.parent / "web" / "config.js"
text = re.sub(r'VAPID_PUBLIC_KEY: "[^"]*"', 'VAPID_PUBLIC_KEY: "%s"' % public, config.read_text(encoding="utf-8"))
with open(config, "w", encoding="utf-8", newline="\n") as f:
    f.write(text)
print("완료: Secret 2개 등록, web/config.js 공개키 갱신")
