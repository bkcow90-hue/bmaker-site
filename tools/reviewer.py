"""검토자 표기(대표 2026-10-04 저자 신호 D) — 본문 바이라인과 JSON-LD reviewedBy 를 한 곳에서 만든다.

본문 줄: '작성 비즈니스 메이커 · 검토 김상표(대표) · 최종 확인 {날짜}' (자금 페이지와 같은 형식)
JSON-LD: WebPage 노드에 reviewedBy(Person #founder) + lastReviewed. reviewedBy 는 schema.org 에서 WebPage 속성이라
Article·BlogPosting 에 직접 달지 않고, 같은 주소의 WebPage 노드(@id = 주소#webpage)로 따로 낸다.
Person 의 자세한 정보(경력 등)는 홈 #founder 노드 한 곳에만 둔다. 자격은 확인된 것이 없어 넣지 않는다.
"""
import json, re

BYLINE = '작성 비즈니스 메이커 · 검토 김상표(대표) · 최종 확인 {}'
BYLINE_STYLE = 'margin-top:14px;font-size:.8rem;opacity:.7'
PERSON = {"@type": "Person", "@id": "https://bmaker.kr/#founder", "name": "김상표", "jobTitle": "대표",
          "worksFor": {"@id": "https://bmaker.kr/#org"}}
BYLINE_RE = re.compile(r'검토 김상표\(대표\) · 최종 확인 ([^<]+?)\s*<')


def byline_html(date):
    return f'<p class="byline" style="{BYLINE_STYLE}">{BYLINE.format(date)}</p>'


def iso(date_text):
    """바이라인 날짜 → ISO 8601(YYYY-MM-DD 또는 YYYY-MM). 모르는 형식이면 None."""
    t = date_text.strip()
    if re.fullmatch(r'\d{4}-\d{2}(-\d{2})?', t):
        return t
    m = re.fullmatch(r'(\d{4})년 (\d{1,2})월(?: (\d{1,2})일)?', t)
    if m:
        y, mo, d = m.groups()
        return f'{y}-{int(mo):02d}' + (f'-{int(d):02d}' if d else '')
    return None


def reviewed_ld(url, date_text):
    """data-reviewed 블록 하나. date_text 는 본문 바이라인에 찍힌 값 그대로."""
    node = {"@context": "https://schema.org", "@type": "WebPage", "@id": url + "#webpage", "url": url,
            "reviewedBy": PERSON}
    d = iso(date_text)
    if d:
        node["lastReviewed"] = d
    return '<script type="application/ld+json" data-reviewed>' + json.dumps(node, ensure_ascii=False) + '</script>'
