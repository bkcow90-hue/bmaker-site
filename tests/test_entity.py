"""엔티티 일관성 회귀 테스트 — AI 검색엔진이 회사를 한 개체로 인식하도록 JSON-LD @id·sameAs·요금 문구를 고정한다.

배경(2026-08-28 AI 인용 기준선): Perplexity가 소재지를 틀리게 답하고 Gemini가 근거 없는 서술을 붙였다.
엔티티 정보가 얇거나 페이지마다 다르면 AI가 지어낸다. 모든 페이지가 같은 @id를 가리키고, 요금 원칙은 한 문장으로만 쓴다.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ORG_ID = "https://bmaker.kr/#org"
FEE = "착수금·진행비 등 실행 전 비용은 일절 받지 않고, 자금이 실제 실행된 경우에만 성공보수를 받습니다."
SERVICE_PAGES = ["sojingong.html", "jungjingong.html", "bojeung.html", "certification.html"]


def _ld(name: str):
    html = (ROOT / name).read_text(encoding="utf-8")
    return [json.loads(m) for m in re.findall(r'<script type="application/ld\+json">\s*(.*?)\s*</script>', html, re.S)]


def test_home_declares_org_with_id_and_identity_surfaces():
    org = next(d for d in _ld("index.html") if d.get("@type") == "ProfessionalService")
    assert org["@id"] == ORG_ID
    assert org["url"] == "https://bmaker.kr/"
    assert "비즈니스메이커" in org["alternateName"]
    assert org["founder"]["name"] == "김상표"
    assert org["address"]["addressLocality"] == "강서구" and "마곡" in org["address"]["streetAddress"]
    for surface in ("instagram.com/bmaker_kr", "blog.naver.com/bmaker_kr", "pf.kakao.com/_GKuxfn"):
        assert any(surface in s for s in org["sameAs"]), f"sameAs 누락: {surface}"
    site = next(d for d in _ld("index.html") if d.get("@type") == "WebSite")
    assert site["publisher"]["@id"] == ORG_ID


def test_service_pages_reference_the_same_org_id():
    for name in SERVICE_PAGES:
        svc = next(d for d in _ld(name) if d.get("@type") == "Service")
        prov = svc["provider"]
        assert prov["@id"] == ORG_ID, f"{name}: provider @id 불일치"
        assert prov["url"] == "https://bmaker.kr/", f"{name}: provider url 은 정본(슬래시 포함)이어야"


def test_fee_policy_wording_is_single_sentence_everywhere():
    """요금 원칙은 홈 본문·FAQ LD·llms.txt 에 동일 문장으로만. 요율·산정 방식은 어디에도 쓰지 않는다(비공개)."""
    home = (ROOT / "index.html").read_text(encoding="utf-8")
    llms = (ROOT / "llms.txt").read_text(encoding="utf-8")
    assert FEE in home, "홈에 고정 요금 문장 없음"
    assert "착수금·진행비 등 실행 전 비용은 일절 받지 않고" in llms
    for text, where in ((home, "index.html"), (llms, "llms.txt")):
        assert not re.search(r"성공보수[^.\n]{0,20}\d+\s*%|\d+\s*%[^.\n]{0,10}성공보수", text), f"{where}: 성공보수 요율 노출 금지"
        assert "갚" not in text, f"{where}: '갚다' 계열 표현 금지 (상환/돌려주다 사용)"
