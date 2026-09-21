"""Regression boundaries: source-derived evidence, course consistency and usable links."""
import importlib.util
import json
import re
import sys
from pathlib import Path
from html import unescape
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'tools' / f'{name}.py')
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_course_rendering_keeps_timetable_and_printed_program_in_sync():
    builder = module('build_education')
    assert hasattr(builder, 'render_programs'), 'Course cards and printable table need one source'
    courses = [{'id': 'corporate', 'title': '법인 <실무>', 'audience': '대표 & 담당자',
                'minutes': 60, 'steps': [[20, '확인'], [40, '실습']], 'takeaway': '준비표'}]
    card = builder.render_programs(courses)
    table = builder.render_programs(courses, table=True)
    for output in (card, table):
        assert '법인 &lt;실무&gt;' in output and '대표 &amp; 담당자' in output
        assert '60분' in output and '준비표' in output
    assert '20분' in card and '40분' in card
    courses[0]['minutes'] = 90
    import pytest
    with pytest.raises(ValueError):
        builder.render_programs(courses)


def test_jaedan_evidence_is_computed_from_rows_not_legacy_copy():
    builder = module('build_jaedan')
    assert hasattr(builder, 'render_hub_cases'), 'Hub must derive the evidence table from the ledger'
    rows = [
        {'사례ID': 'T1', '지역(시도)': '서울', '기관': '서울신용보증재단', '자금명': '<자금>', '실행 연월': '2026-01', '실행 금액(만원)': '1000', '금리': '연 3%'},
        {'사례ID': 'T2', '지역(시도)': '부산', '기관': '부산신용보증재단', '자금명': '운전자금', '실행 연월': '2026-02', '실행 금액(만원)': '2000', '금리': '연 4%'},
        {'사례ID': 'T3', '지역(시도)': '서울', '기관': '서울신용보증재단', '자금명': '운전자금', '실행 연월': '2026-03', '실행 금액(만원)': '3000', '금리': '연 5%'}]
    out = builder.render_hub_cases(rows)
    assert '2개 지역' in out and '3건' in out and '6,000만원' in out
    assert '/cases#case-T1' in out and '&lt;자금&gt;' in out
    assert '1,000만원' in out and '3,000만원' in out
    empty = builder.render_hub_cases([])
    assert '0건' in empty and '<tbody><tr>' not in empty


def test_education_faq_schema_matches_visible_answers():
    h = (ROOT / 'education.html').read_text(encoding='utf-8')
    assert '중소기업' in re.search(r'<title>(.*?)</title>', h).group(1)
    assert '법인' in re.search(r'<main>(.*?)</main>', h, re.S).group(1)
    for raw in re.findall(r'<script type="application/ld\+json">(.*?)</script>', h, re.S):
        schema = json.loads(raw)
        if schema.get('@type') == 'FAQPage':
            for question in schema['mainEntity']:
                assert question['name'] in unescape(h)
                assert question['acceptedAnswer']['text'] in unescape(h)


def test_growth_links_are_real_and_priority_pages_have_multiple_referrers():
    files = list(ROOT.glob('*.html'))
    incoming = {}
    for file in files:
        h = file.read_text(encoding='utf-8')
        assert h.count('<!-- topic-links:start -->') <= 1, file.name
        targets = set()
        for href in re.findall(r'<a\b[^>]*href=["\']([^"\']+)', h):
            u = urlsplit(unescape(href))
            if u.netloc and u.netloc != 'bmaker.kr':
                continue
            if not u.path.startswith('/') or (u.path != '/' and '.' in u.path):
                continue
            slug = u.path.strip('/') or 'index'
            target = ROOT / (slug + '.html')
            if '<!-- topic-links:start -->' in h and href in h.split('<!-- topic-links:start -->')[1].split('<!-- topic-links:end -->')[0]:
                assert target.exists(), (file.name, href)
            if target.exists() and target != file:
                targets.add(slug)
        for slug in targets:
            incoming.setdefault(slug, set()).add(file.name)
    for slug in ['cheongnyeon', 'jaedojeon', 'hyeoksin', 'sogongin', 'daehwan', 'education-program', 'jaedan-seoul', 'jaedan-gyeonggi']:
        assert len(incoming.get(slug, set())) >= 2, (slug, incoming.get(slug))


def test_related_links_validate_routes_escape_labels_and_replace_idempotently():
    builder = module('build_editorial')
    assert hasattr(builder, 'topic_links')
    links = [['education-program', '교육 <준비> & 자료'], ['jaedan', '보증 안내']]
    rendered = builder.topic_links(links)
    assert '교육 &lt;준비&gt; &amp; 자료' in rendered
    assert 'href="/education-program"' in rendered
    page = '<main><p>원문</p></main>'
    once = builder.replace_block(page, 'topic-links', rendered)
    assert builder.replace_block(once, 'topic-links', rendered) == once
    import pytest
    with pytest.raises(ValueError):
        builder.topic_links([['missing-route-999', '없는 문서']])


def test_repayment_examples_keep_each_case_label_and_id_together():
    builder = module('build_editorial')
    assert hasattr(builder, 'repayment_examples')
    rows = [{'사례ID': 'T1', '실행 연월': '2026-08', '자금명': '상품 <가>',
             '실행 금액(만원)': '2000', '상환 조건': '12개월 거치'},
            {'사례ID': 'T2', '실행 연월': '2026-07', '자금명': '상품 나',
             '실행 금액(만원)': '3000', '상환 조건': '만기 상환'}]
    out = builder.repayment_examples(rows)
    assert '2건' in out and '/cases#case-T1' in out and '상품 &lt;가&gt;' in out
    assert '2,000만원' in out and '12개월 거치' in out
    assert builder.repayment_examples([]).count('<tbody><tr>') == 0


def test_microfinance_referral_bar_opens_the_official_institution_not_company_leads():
    page = (ROOT / 'microfinance-business.html').read_text(encoding='utf-8')
    bar = re.search(r'<div class="sticky".*?</div>', page, re.S).group(0)
    targets = re.findall(r'href="([^"]+)"', bar)
    assert targets == ['https://mmc.kinfa.or.kr/view/pdt/KFA_PDT_04010000']
    assert '#apply' not in bar and 'kakao.com' not in bar
