"""홈 폼 가이드북 이메일(2026-11-13) — 선택 칸이고, 적으면 /api/lead 에 email·guidebook_request 를 싣는다."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOME = (ROOT / 'index.html').read_text(encoding='utf-8')
JS = (ROOT / 'assets/conversion.js').read_text(encoding='utf-8')


def test_email_field_is_optional_and_home_only():
    tag = re.search(r'<input id="lf-email"[^>]*>', HOME).group(0)
    assert 'type="email"' in tag and 'required' not in tag
    assert '가이드북 받을 이메일 (선택)' in HOME
    assert '연락처로 함께 보내드립니다' not in HOME  # 폰으로는 보내지 않는다


def test_payload_carries_email_and_request():
    assert "email: email, guidebook_request: email !== ''" in JS
    assert "result.guidebook === 'sent'" in JS
