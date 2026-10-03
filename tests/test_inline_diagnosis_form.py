"""자금·재단 상세의 인라인 진단 폼 — 정적 구성과 실제 전송 payload 를 본다.

문자열 검사만으로는 전송이 되는지 알 수 없다(규격 10절). 여기서는 /api/lead 호출을 가로채
실제로 나가는 payload 를 확인한다 — 진짜 제출을 보내지 않으므로 운영 메일함이 오염되지 않는다.

사업자 형태·유입 페이지는 /api/lead 가 화이트리스트로 거르는 최상위 키로는 전달되지 않는다.
answers_text 와 diagnosis 에 실려야 알림 메일 본문에 찍히므로 그 두 곳을 함께 검사한다.

로컬 실행: python -m pytest tests/test_inline_diagnosis_form.py
playwright·Chromium 이 없으면 skip (REQUIRE_BROWSER 가 설정된 CI 에서는 실패).
"""
import csv
import functools
import http.server
import json
import os
import re
import threading
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PHONE = {"width": 390, "height": 844}
REQUIRE_BROWSER = bool(os.environ.get("REQUIRE_BROWSER"))

try:
    from playwright import sync_api
except ImportError:
    sync_api = None


def _unavailable(reason):
    if REQUIRE_BROWSER:
        pytest.fail(f"REQUIRE_BROWSER 가 설정된 환경인데 브라우저 테스트를 실행할 수 없습니다 — {reason}")
    pytest.skip(reason)


def _slugs(source, key):
    with (ROOT / f"data/{source}.source.csv").open(encoding="utf-8-sig", newline="") as f:
        return [r[key] for r in csv.DictReader(f) if r.get("사이트 공개", "").upper() == "Y"]


FUND_SLUGS = _slugs("funds", "자금ID")
JAEDAN_SLUGS = _slugs("jaedan", "재단ID")
FORM_PAGES = FUND_SLUGS + JAEDAN_SLUGS + ["jaedan"]


# ── 정적 구성 ──────────────────────────────────────────────────────────────

def test_every_fund_and_foundation_page_has_exactly_one_form():
    assert len(FORM_PAGES) == 33, f"자금 15 + 재단 18 이어야 한다: {len(FORM_PAGES)}"
    for slug in FORM_PAGES:
        s = (ROOT / f"{slug}.html").read_text(encoding="utf-8")
        assert s.count('id="leadForm"') == 1, f"{slug}: 폼이 {s.count('id=\"leadForm\"')}개"
        assert s.count('id="apply"') == 1, f"{slug}: apply 앵커가 1개가 아니다"


def test_no_other_page_gained_a_form():
    """폼은 홈 + 자금·재단 33장에만 있어야 한다 — conversion.js 는 페이지당 폼 1개를 전제한다."""
    # 홈 + 자금·재단 33장 + 분기별 접수 안내(자체 폼을 가진 정적 페이지)
    # 블로그 목록(blog.html)도 허브와 같은 인라인 폼 1개 — 글·카테고리 페이지(blog/**)는 루트 glob 밖이라 여기서 세지 않는다
    # 지역별 창구 목록(region.html, build_region)도 도시 페이지와 같은 인라인 폼 1개(2026-10-04)
    expected = set(FORM_PAGES) | {"index", "2026-4q-sosangin", "sosangin", "jungsogieop", "blog", "region"}
    found = {p.stem for p in ROOT.glob("*.html") if 'id="leadForm"' in p.read_text(encoding="utf-8")}
    assert found == expected, f"예상 밖: {found ^ expected}"


def test_form_fields_and_wording():
    s = (ROOT / "cheongnyeon.html").read_text(encoding="utf-8")
    assert "이 자금, 우리 회사도 되는지 무료로 확인" in s
    assert "무료 진단 신청" in s
    for label in ("개인사업자", "법인사업자", "창업 예정"):
        assert f'class="biz-opt" aria-pressed="false">{label}<' in s, label
    for fid in ("lf-name", "lf-phone", "lf-consent", "lf-website", "lf-page", "lf-service"):
        assert f'id="{fid}"' in s, fid
    # 동의는 미리 체크하지 않는다 · 허니팟은 화면에서 숨긴다(규격 4절)
    assert 'id="lf-consent" required>' in s and "checked" not in s.split('id="lf-consent"')[1][:40]
    assert "개인정보처리방침 보기" in s


def test_hidden_page_field_identifies_the_source_page():
    for slug, label in [("cheongnyeon", "청년고용연계자금"), ("jaedan-seoul", "서울신용보증재단"),
                        ("jaedan", "신용보증재단 사업자대출")]:
        s = (ROOT / f"{slug}.html").read_text(encoding="utf-8")
        m = re.search(r'id="lf-page" value="([^"]*)"', s)
        assert m, f"{slug}: lf-page 없음"
        assert m.group(1) == f"/{slug} ({label})", f"{slug}: {m.group(1)}"


def test_page_marks_policy_service_so_form_opens_as_policy():
    for slug in ("cheongnyeon", "jaedan-seoul", "jaedan"):
        s = (ROOT / f"{slug}.html").read_text(encoding="utf-8")
        assert '<body data-service="policy">' in s, slug


def test_bottom_cta_points_at_the_on_page_form():
    """폼이 생겼으니 하단 CTA 는 홈이 아니라 이 페이지 폼으로 내려가야 한다."""
    shell = re.compile('<(header|footer)\\b.*?</\\1>', re.S)
    for slug in ("cheongnyeon", "jaedan-seoul", "jaedan"):
        # 전역 내비의 /#apply 는 메뉴라서 대상이 아니다 — 본문 CTA 만 본다
        s = shell.sub('', (ROOT / f"{slug}.html").read_text(encoding="utf-8"))
        assert 'href="/#apply"' not in s, f"{slug}: 홈 폼으로 나가는 CTA 가 남아 있다"
        assert 'href="#apply"' in s, slug


# ── 브라우저 동작 ──────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def site():
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()


@pytest.fixture(scope="module")
def browser():
    if sync_api is None:
        _unavailable("playwright 미설치 — pip install playwright")
    try:
        driver = sync_api.sync_playwright().start()
    except Exception as exc:
        _unavailable(f"playwright 드라이버를 시작할 수 없음: {exc}")
    try:
        b = driver.chromium.launch()
    except sync_api.Error as exc:
        driver.stop()
        _unavailable(f"Chromium 을 띄울 수 없음: {exc} (playwright install chromium)")
    try:
        yield b
    finally:
        b.close()
        driver.stop()


def _submit(browser, site, slug):
    """폼을 채워 제출하고, 실제로 나가는 /api/lead payload 를 가로채 돌려준다."""
    page = browser.new_page(viewport=PHONE, is_mobile=True, has_touch=True, reduced_motion="reduce")
    sent = {}
    events = []

    def handle(route):
        sent["payload"] = json.loads(route.request.post_data)
        route.fulfill(status=200, content_type="application/json",
                      body=json.dumps({"ok": True, "delivery": "accepted"}))

    # 외부로는 한 바이트도 내보내지 않는다.
    # playwright 는 나중에 등록한 핸들러를 먼저 본다 — catch-all 을 먼저 걸고 /api/lead 를 나중에.
    page.route("**/*", lambda r: r.continue_() if r.request.url.startswith("http://127.0.0.1:") else r.abort())
    page.route("**/api/lead", handle)
    page.goto(f"{site}/{slug}.html", wait_until="domcontentloaded")
    page.add_init_script("window.__ev=[]")
    page.evaluate("window.gtag = (kind, name, params) => (window.__ev ||= []).push([name, params])")

    page.locator("#lf-biztype .biz-opt", has_text="법인사업자").click()
    page.fill("#lf-name", "테스트")
    page.fill("#lf-phone", "010-1234-5678")
    page.locator("#lf-time .time-opt", has_text="오전").click()
    page.check("#lf-consent")
    page.locator("#leadForm button[type=submit]").click()
    page.wait_for_function("document.getElementById('applyMsg').textContent.length > 0", timeout=5000)
    events.extend(page.evaluate("window.__ev || []"))
    message = page.locator("#applyMsg").inner_text()
    page.close()
    return sent.get("payload"), events, message


def test_submission_carries_business_type_and_source_page(browser, site):
    payload, events, message = _submit(browser, site, "cheongnyeon")
    assert payload, "제출이 /api/lead 로 나가지 않았다"

    # 메일 본문에 실제로 찍히는 두 경로에 모두 들어 있어야 한다
    assert "[사업자 형태] 법인사업자" in payload["answers_text"], payload["answers_text"]
    assert "[유입] /cheongnyeon (청년고용연계자금)" in payload["answers_text"], payload["answers_text"]
    assert payload["diagnosis"]["사업자 형태"] == "법인사업자"
    assert payload["diagnosis"]["유입 페이지"] == "/cheongnyeon (청년고용연계자금)"

    # 기존 계약은 그대로
    assert payload["kind"] == "consult" and payload["service"] == "pfm"
    assert payload["consultation_service"] == "policy"
    assert payload["name"] == "테스트" and payload["phone"] == "01012345678"
    assert payload["preferred_time"].startswith("오전")
    assert payload["consent_privacy"] is True and payload["website"] == ""
    assert "접수됐습니다" in message


def test_generate_lead_reports_the_page_path(browser, site):
    """페이지별 전환율을 보려면 generate_lead 에 그 페이지 경로가 실려야 한다."""
    _, events, _ = _submit(browser, site, "jaedan-seoul")
    lead = [params for name, params in events if name == "generate_lead"]
    assert lead, [name for name, _ in events]
    assert lead[0]["page_path"] == "/jaedan-seoul.html", lead[0]
    assert lead[0]["service_category"] == "policy", lead[0]
    assert lead[0]["method"] == "consultation_form"


def test_foundation_hub_form_also_submits(browser, site):
    payload, _, _ = _submit(browser, site, "jaedan")
    assert payload["diagnosis"]["유입 페이지"] == "/jaedan (신용보증재단 사업자대출)"
    assert payload["diagnosis"]["사업자 형태"] == "법인사업자"


# ── 선택형 그룹: 클릭 → 선택 상태 → 선택 표시 → payload ─────────────────────
# 2026-09-28 대표 제보 "사업자 형태 선택 불가" 이후 추가. 선택지 하나하나를 실제로 눌러
# aria-pressed(=선택 상태)·계산된 배경색(=화면 표시)·전송 payload 를 모두 본다.
# 이 그룹들은 <input> 이 아니라 aria-pressed 토글 버튼이므로 'checked' 대신 aria-pressed 를 본다.
SELECTED_BG = "rgb(36, 84, 188)"   # FORM CSS .opts button[aria-pressed=true] 의 #2454bc
GROUPS = [
    ("#lf-biztype .biz-opt", ["개인사업자", "법인사업자", "창업 예정"],
     lambda p: p["diagnosis"].get("사업자 형태")),
    ("#lf-time .time-opt", ["오전 (9~12시)", "오후 (12~6시)", "아무 때나"],
     lambda p: p["preferred_time"]),
]


@pytest.mark.parametrize("viewport", [PHONE, {"width": 1280, "height": 800}], ids=["390", "1280"])
@pytest.mark.parametrize("selector,labels,read", GROUPS, ids=["biztype", "time"])
def test_every_choice_selects_shows_and_is_sent(browser, site, viewport, selector, labels, read):
    for label in labels:
        page = browser.new_page(viewport=viewport)
        sent = {}

        def handle(route):
            sent["payload"] = json.loads(route.request.post_data)
            route.fulfill(status=200, content_type="application/json",
                          body=json.dumps({"ok": True, "delivery": "accepted"}))

        page.route("**/*", lambda r: r.continue_() if r.request.url.startswith("http://127.0.0.1:") else r.abort())
        page.route("**/api/lead", handle)
        page.goto(f"{site}/cheongnyeon.html", wait_until="domcontentloaded")
        target = page.locator(selector, has_text=label)
        target.click()
        assert target.get_attribute("aria-pressed") == "true", f"{label}: 눌러도 선택 상태가 안 됨"
        others = [b.get_attribute("aria-pressed") for b in page.locator(selector).all()
                  if b.inner_text().strip() != label]
        assert others == ["false"] * (len(labels) - 1), f"{label}: 다른 선택지가 풀리지 않음 {others}"
        bg = target.evaluate("e => getComputedStyle(e).backgroundColor")
        assert bg == SELECTED_BG, f"{label}: 선택 표시가 안 보임 (배경 {bg})"
        page.fill("#lf-name", "테스트")
        page.fill("#lf-phone", "010-1234-5678")
        page.check("#lf-consent")
        page.locator("#leadForm button[type=submit]").click()
        page.wait_for_function("document.getElementById('applyMsg').textContent.length > 0", timeout=5000)
        assert sent.get("payload"), f"{label}: 제출이 /api/lead 로 나가지 않음"
        assert read(sent["payload"]) == label, (label, sent["payload"]["answers_text"])
        page.close()


# ── 방어 코드: 칸이 없거나 예상 못 한 오류가 나도 조용히 멈추지 않는다 ────────────
# 2026-09-28 옛 캐시 JS 가 없는 칸을 읽다 멈춰 전송도 안내도 없었다. 이제는 어떤 오류든
# 연락처 안내(전화·카톡 버튼)를 띄우고 GA4 form_error(페이지 경로·오류 앞 100자)를 남긴다.
CRASH_TEXT = "전송에 실패했습니다. 1666-2425 또는 카카오톡으로 연락 주세요."


def _submit_broken(browser, site, *, remove=(), init_script=None):
    page = browser.new_page(viewport=PHONE)
    sent = []

    def serve_page(route):
        body = route.fetch().text()
        for pattern in remove:
            body, n = re.subn(pattern, "", body, count=1)
            assert n == 1, f"지울 칸을 찾지 못함: {pattern}"
        route.fulfill(status=200, content_type="text/html; charset=utf-8", body=body)

    def handle(route):
        sent.append(json.loads(route.request.post_data))
        route.fulfill(status=200, content_type="application/json",
                      body=json.dumps({"ok": True, "delivery": "accepted"}))

    page.route("**/*", lambda r: r.continue_() if r.request.url.startswith("http://127.0.0.1:") else r.abort())
    page.route("**/cheongnyeon.html", serve_page)
    page.route("**/api/lead", handle)
    if init_script:
        page.add_init_script(init_script)
    page.goto(f"{site}/cheongnyeon.html", wait_until="domcontentloaded")
    page.evaluate("window.gtag = (kind, name, params) => (window.__ev ||= []).push([name, params])")
    if page.locator("#lf-name").count():
        page.fill("#lf-name", "테스트")
    if page.locator("#lf-phone").count():
        page.fill("#lf-phone", "010-1234-5678")
    page.check("#lf-consent")
    page.locator("#leadForm button[type=submit]").click()
    page.wait_for_function("document.getElementById('applyMsg').textContent.length > 0", timeout=5000)
    result = {
        "sent": sent,
        "message": page.locator("#applyMsg").inner_text(),
        "fallback": page.locator("#applyMsg .apply-fallback a").evaluate_all("as => as.map(a => a.getAttribute('href'))"),
        "errors": [p for n, p in page.evaluate("window.__ev || []") if n == "form_error"],
        "button": page.locator("#leadForm button[type=submit]").evaluate("b => [b.disabled, b.textContent]"),
    }
    page.close()
    return result


def test_missing_required_field_shows_contact_fallback_and_reports_form_error(browser, site):
    r = _submit_broken(browser, site, remove=[r'<input id="lf-phone"[^>]*>'])
    assert not r["sent"], "연락처 칸이 없는데 전송됐다"
    assert CRASH_TEXT in r["message"], r["message"]
    assert r["fallback"] == ["https://pf.kakao.com/_GKuxfn/chat", "tel:1666-2425"], r["fallback"]
    assert len(r["errors"]) == 1, r["errors"]
    assert r["errors"][0]["page_path"] == "/cheongnyeon.html"
    assert "lf-phone" in r["errors"][0]["error_message"]
    assert r["button"] == [False, "무료 진단 신청"], "버튼이 '전송 중' 에 묶였다"


def test_unexpected_runtime_error_is_caught_too(browser, site):
    """칸 누락이 아닌 임의의 오류도 같은 경로로 — 오류 문구는 앞 100자만 보낸다."""
    r = _submit_broken(browser, site, init_script="crypto.randomUUID = () => { throw new Error('x'.repeat(300)) }")
    assert not r["sent"] and CRASH_TEXT in r["message"], r
    assert len(r["errors"]) == 1 and r["errors"][0]["error_message"] == "x" * 100, r["errors"]


def test_missing_optional_fields_do_not_block_submission(browser, site):
    """허니팟·유입 페이지·사업자 형태 칸이 없어도 null 로 처리하고 전송은 나간다."""
    r = _submit_broken(browser, site, remove=[r'<input type="text" name="website" id="lf-website"[^>]*>',
                                              r'<input type="hidden" id="lf-page"[^>]*>',
                                              r'<div class="opts" role="group" aria-labelledby="lf-biztype-label" id="lf-biztype">.*?</div>'])
    assert len(r["sent"]) == 1 and not r["errors"], r
    assert r["sent"][0]["website"] == ""
    assert "접수됐습니다" in r["message"]
