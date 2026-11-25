"""도구 묶음 2차(2026-11-25) — 청년창업 나이·업력·제외 업종·보증료·거치기간·연구소 요건.

기준 숫자와 계산이 출처(공고·법령)와 어긋나지 않게 지킨다. 계산은 node 로 실제 스크립트를 불러 확인한다.
 - 만 39세 이하·업력 3년/7년/10년: 2026년 중소기업 정책자금 융자계획(중기부 공고 제2025-649호), 중진공 누리집
 - 15~34세·병역 6년 차감: 조세특례제한법 시행령 제5조
 - 제외 업종: 소진공 누리집 제외업종 표·공고 제2025-656호 별표 1, 중진공 공고 제2025-649호 별표 1
 - 연구전담요원 수: /research-institute 본문 표와 같은 값
"""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
NODE = shutil.which('node')
PAGES = {
    'cheongnyeon-nai': 'cheongnyeon-nai',
    'eopryeok-gyesangi': 'eopryeok-gyesangi',
    'jeoe-eopjong': 'jeoe-eopjong',
    'bojeungryo-gyesangi': 'bojeungryo-gyesangi',
    'geochi-gyesangi': 'geochi-gyesangi',
    'research-institute': 'yeonguso-yogeon',
}


def run(tool, expr):
    if not NODE:
        pytest.skip('node 없음')
    code = "const m=require(%s);const D=m.parseDate;console.log(JSON.stringify(%s))" % (
        json.dumps(str(ROOT / 'assets' / f'tool-{tool}.js')), expr)
    return json.loads(subprocess.run([NODE, '-e', code], capture_output=True, text=True, check=True).stdout)


@pytest.mark.parametrize('page,tool', PAGES.items())
def test_page_has_tool_and_apply_route(page, tool):
    html = (ROOT / f'{page}.html').read_text(encoding='utf-8')
    assert 'id="toolForm"' in html and f'/assets/tool-{tool}.js' in html
    assert 'class="inline-diag"' in html          # 도구 페이지에도 자금 접수 경로가 있어야 한다
    assert '참고 안내' in html
    js = (ROOT / 'assets' / f'tool-{tool}.js').read_text(encoding='utf-8')
    assert 'lf-memo' in js and 'tool_result' in js   # 결과가 상담 신청 메모로 넘어가고 측정된다
    assert '갚' not in js and '보장' not in js


def test_hub_links_every_tool():
    html = (ROOT / 'dogu.html').read_text(encoding='utf-8')
    for slug in ('jagajindan', 'sosangin-gijun', 'jungsogieop-gijun', 'jeoe-eopjong', 'eopryeok-gyesangi',
                 'cheongnyeon-nai', 'research-institute', 'bojeungryo-gyesangi', 'geochi-gyesangi'):
        assert f'href="https://bmaker.kr/{slug}"' in html or f'href="/{slug}"' in html, slug


def test_age_thresholds():
    assert run('cheongnyeon-nai', '[m.LOAN_AGE,m.TAX_MAX,m.MIL_CAP]') == [39, 34, 72]
    # 만 40세 생일 전날까지 만 39세
    r = run('cheongnyeon-nai', "[m.calc(D('1987-11-25'),D('2026-11-25'),0),m.calc(D('1986-11-25'),D('2026-11-25'),0)]")
    assert (r[0]['age'], r[0]['loanOk'], r[0]['lastLoanDay']) == (39, True, '2027-11-24')
    assert (r[1]['age'], r[1]['loanOk']) == (40, False)
    # 병역 21개월을 빼면 만 36세도 34세 기준 안, 차감은 6년(72개월)까지
    r = run('cheongnyeon-nai', "[m.calc(D('1990-05-10'),D('2026-11-25'),21),m.calc(D('1980-01-01'),D('2026-11-25'),100)]")
    assert (r[0]['age'], r[0]['taxAge'], r[0]['taxOk']) == (36, 34, True)
    assert (r[1]['mil'], r[1]['taxAge'], r[1]['taxOk']) == (72, 40, False)


def test_business_age_bands():
    r = run('eopryeok-gyesangi', "[m.calc(D('2023-11-26'),D('2026-11-25')),m.calc(D('2023-11-25'),D('2026-11-25')),"
            "m.calc(D('2019-11-25'),D('2026-11-25')),m.calc(D('2016-11-25'),D('2026-11-25'))]")
    assert [x['band'] for x in r] == ['under3', 'under7', 'under10', 'over10']   # 제출일에 꽉 차면 '미만'이 아니다
    assert (r[0]['years'], r[0]['months'], r[0]['days']) == (2, 11, 30)
    assert (r[0]['at3'], r[0]['at7']) == ('2026-11-26', '2030-11-26')


def test_guarantee_fee_formula():
    r = run('bojeungryo-gyesangi', '[m.calc(5000,1.0,1,NaN),m.calc(5000,1.2,5,3.5)]')
    assert r[0]['perYear'] == 500000 and r[0]['interest'] is None
    assert (r[1]['perYear'], r[1]['total'], r[1]['firstYear']) == (600000, 3000000, 2350000)


def test_grace_period_schedule():
    r = run('geochi-gyesangi', "[m.calc(7000,3.2,5,2,'principal'),m.calc(7000,3.2,5,2,'annuity'),m.calc(1200,0,1,0,'annuity')]")
    assert (r[0]['graceMonths'], r[0]['payMonths'], r[0]['graceMonthly']) == (24, 36, 186667)
    assert r[0]['first'] == round(70000000 / 36 + 70000000 * 0.032 / 12)
    assert r[0]['first'] > r[0]['last'] and r[1]['first'] == r[1]['last']
    assert r[0]['totalInterest'] < r[1]['totalInterest']        # 전체 이자는 원금균등이 적다
    assert (r[2]['first'], r[2]['totalInterest']) == (1000000, 0)


def test_research_lab_headcount_matches_page_table():
    assert run('yeonguso-yogeon', 'm.REQ') == {'small3': 2, 'small': 3, 'medium': 5, 'mid': 7}
    r = run('yeonguso-yogeon', "[m.judge('small',false,2),m.judge('medium',true,2),m.judge('mid',true,6),m.judge('small',false,0)]")
    assert [(x['need'], x['code']) for x in r] == [(3, 'dept'), (2, 'lab'), (7, 'dept'), (3, 'none')]
    page = (ROOT / 'research-institute.html').read_text(encoding='utf-8')
    for text in ('3명 이상, 창업 후 3년까지는 2명 이상', '5명 이상', '7명 이상'):
        assert text in page


def test_excluded_industry_table():
    rows = run('jeoe-eopjong', 'm.ROWS')
    assert len(rows) == 43 and len({r[0] for r in rows}) == 43
    assert all(r[4] in 'xco' and r[5] in 'xco' for r in rows)
    st = {r[0]: (r[4], r[5]) for r in rows}
    # 두 공고 모두 제외
    for k in ('nightclub', 'realestate-rent', 'insurance', 'law', 'vet', 'crypto', 'fortune', 'casino'):
        assert st[k] == ('x', 'x'), k
    # 두 목록이 갈리는 업종 — 여기서 자주 틀린다
    assert st['pub'] == ('o', 'x')                 # 소진공은 유흥주점만, 중진공은 주점업(5621) 전체
    assert st['construction'] == ('o', 'c')        # 중진공 건설업은 일부 공사업만 예외
    assert st['pharmacy'] == ('x', 'o')            # 약국은 소진공 목록에만 있다
    assert st['realestate-agent'] == ('c', 'x')    # 소진공은 6개월 이상 영업한 중개업 예외
    assert st['medical'] == ('x', 'c')             # 중진공은 사회적경제기업 예외
    assert st['food'] == st['retail'] == st['mfg'] == ('o', 'o')
    assert [r[0] for r in run('jeoe-eopjong', "m.search('주점')")] == ['pub', 'nightclub']
