"""/sinbo 메타의 받은 사례 숫자는 원장에서 생성한다(build_cases META_CASE, 2026-10-01 v2). 손으로 쓴 값이 남지 않게 고정."""
import csv, html, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / 'tools'
sys.path.insert(0, str(TOOLS))
from build_cases import norm_rate  # noqa: E402  빌더와 같은 금리 표기


def _won2(m):
    e, man = divmod(int(m), 10000)
    return ((f"{e}억" + ((" " if man else "") + f"{man:,}만" if man else "")) + "원") if e else f"{man:,}만원"


def test_sinbo_meta_numbers_come_from_ledger():
    s = (ROOT / 'sinbo.html').read_text(encoding='utf-8')
    title = html.unescape(re.search(r'<title>(.*?)</title>', s).group(1))
    og = html.unescape(re.search(r'<meta property="og:title" content="(.*?)"', s).group(1))
    desc = html.unescape(re.search(r'<meta name="description" content="(.*?)"', s).group(1))
    ogd = html.unescape(re.search(r'<meta property="og:description" content="(.*?)"', s).group(1))
    assert title == og and desc == ogd
    assert '실측' not in title + desc
    cid = re.search(r"'sinbo\.html':\('(E\d+)'", (TOOLS / 'build_cases.py').read_text(encoding='utf-8')).group(1)
    row = next(r for r in csv.DictReader(open(ROOT / 'data' / 'cases.source.csv', encoding='utf-8-sig'))
               if r['사례ID'] == cid)
    assert f"받은 사례({_won2(row['실행 금액(만원)'])}·{norm_rate(row['금리']).strip()})" in desc


def test_sinbo_h1_and_answer_lead_with_structure():
    s = (ROOT / 'sinbo.html').read_text(encoding='utf-8')
    h1 = re.sub(r'<[^>]+>', '', re.search(r'<h1[^>]*>(.*?)</h1>', s, re.S).group(1))
    assert h1.startswith('신보 보증서로 은행에서 대출받는 구조')
    assert '<b>짧은 답:</b> 신보 보증서로 은행에서 대출받는 구조입니다.' in s
