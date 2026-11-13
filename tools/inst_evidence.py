"""보증기관 페이지(/sinbo·/gibo)의 받은 사례 블록과 기관 비교 칸을 원장에서 다시 만든다 (2026-11-14).

대표 피드백: "/sinbo 에 실측 1건만 나온다" — 원장에는 신보 78건이 있는데 손으로 쓴 표가 8월 1건에 멈춰 있었다.
build_funds 끝에서 호출한다. 마커(<!-- inst-evidence:start/end -->) 사이만 바꾸므로 여러 번 돌려도 같다.
판정 기준·한도 계산은 쓰지 않는다(누가 받았는지의 분포와 최근 사례만).
"""
import csv, re, statistics
from collections import Counter
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# build_cases._KEYS 와 같은 규칙 — 기관 칸에 먼저 나오는 기관으로 분류한다(페이지 머리의 data-stat 숫자와 맞춘다)
_KEYS = [('소상공인', '소진공'), ('재단', '재단'), ('기술', '기보'), ('신용보증기금', '신보'), ('중소벤처', '중진공'), ('중진공', '중진공')]


def classify(k):
    hits = [(k.find(a), b) for a, b in _KEYS if a in k]
    return min(hits)[1] if hits else '기타'


INST = {
    'sinbo': ('신보', lambda k: classify(k) == '신보'),
    'gibo': ('기보', lambda k: classify(k) == '기보'),
    'jaedan': ('재단', lambda k: classify(k) == '재단'),
}


def rows():
    with open(ROOT / 'data' / 'cases.source.csv', encoding='utf-8-sig') as f:
        return [r for r in csv.DictReader(f) if (r.get('사이트 공개') or '').strip().upper() == 'Y']


def won(m):
    m = int(float(m))
    eok, man = divmod(m, 10000)
    if eok and man: return f'{eok}억 {man:,}만원'
    if eok: return f'{eok}억원'
    return f'{man:,}만원'


def pick(all_rows, key):
    return [r for r in all_rows if INST[key][1](r.get('기관', ''))]


def summary(R):
    amts = [int(float(r['실행 금액(만원)'])) for r in R if r.get('실행 금액(만원)')]
    days = [int(float(r['소요일'])) for r in R if (r.get('소요일') or '').strip()]
    months = sorted(r['실행 연월'] for r in R if r.get('실행 연월'))
    return dict(n=len(R), total=sum(amts), med=int(statistics.median(amts)) if amts else 0,
                days=int(statistics.median(days)) if days else 0,
                lo=min(amts) if amts else 0, hi=max(amts) if amts else 0,
                span=f'{months[0].replace("-", ".")}~{months[-1].replace("-", ".")}' if months else '')


def bars(title, counter, n, top=5):
    items = counter.most_common(top)
    li = ''.join(f'<li><span class="ie-k">{escape(k)}</span><span class="ie-bar"><i style="width:{round(v / n * 100)}%"></i></span><span class="ie-v">{v}건</span></li>' for k, v in items)
    return f'<div class="ie-col"><p class="ie-h">{title}</p><ul class="ie-bars">{li}</ul></div>'


def years_bucket(y):
    try: y = float(y)
    except Exception: return None
    return '3년 미만' if y < 3 else ('3~7년' if y < 7 else '7년 이상')


def block(key):
    short, _ = INST[key]
    R = sorted(pick(rows(), key), key=lambda r: (r['실행 연월'], r['사례ID']), reverse=True)
    if not R: return ''
    s = summary(R)
    stats = (f'<div class="ie-stats"><div><b>{s["n"]}건</b><span>받은 사례</span></div><div><b>{won(s["total"])}</b><span>받은 금액 합계</span></div>'
             f'<div><b>{won(s["med"])}</b><span>건당 보통</span></div><div><b>보통 {s["days"]}일</b><span>첫 상담 → 정산</span></div></div>')
    form = Counter((r.get('사업 형태') or '').strip() or '기타' for r in R)
    yrs = Counter(b for b in (years_bucket(r.get('업력(년)')) for r in R) if b)
    ind = Counter((r.get('업종') or '').strip() for r in R if (r.get('업종') or '').strip())
    who = '<div class="ie-who">' + bars('사업 형태', form, len(R), 3) + bars('업력', yrs, len(R), 3) + bars('많이 받은 업종', ind, len(R), 5) + '</div>'
    recent = ''.join(
        f'<tr><td>{escape(r["실행 연월"])}</td><td>{escape(r["지역(시도)"])} · {escape(r["업종"])}</td><td>{escape(r.get("사업 형태", ""))} · 업력 {escape(r.get("업력(년)", ""))}년</td>'
        f'<td>{won(r["실행 금액(만원)"])}{(" · " + escape(r["금리"])) if r.get("금리") else ""}</td><td><a href="/cases#case-{escape(r["사례ID"], quote=True)}">사례 {escape(r["사례ID"])}</a></td></tr>'
        for r in R[:8])
    return ('<!-- inst-evidence:start -->'
            f'<h2>저희가 받은 {short} 사례 {s["n"]}건</h2>'
            f'<p>공개 원장 {s["span"]} 기준입니다. 기업 수가 아닌 사례 건수이고, 받은 금액은 {won(s["lo"])}부터 {won(s["hi"])}까지였습니다. '
            '과거 사례는 지금 신청할 때의 한도·금리·승인 가능성을 뜻하지 않습니다.</p>'
            + stats + who +
            '<p class="ie-h">최근 받은 사례 8건</p><div class="tablewrap"><table><thead><tr><th>시점</th><th>지역·업종</th><th>사업자</th><th>받은 금액·당시 금리</th><th>근거</th></tr></thead>'
            f'<tbody>{recent}</tbody></table></div>'
            '<!-- inst-evidence:end -->')


def cell(key):
    s = summary(pick(rows(), key))
    return f'{s["n"]}건 · 보통 {won(s["med"])} · {won(s["lo"])}~{won(s["hi"])}'


def apply():
    for key, start_pat in (('sinbo', r'<h2>기록된 신보 실측</h2>.*?</table></div>'), ('gibo', r'<h2>기록된 기보 실측</h2>.*?</table></div>')):
        p = ROOT / f'{key}.html'
        h = p.read_text(encoding='utf-8')
        new = block(key)
        if '<!-- inst-evidence:start -->' in h:
            h = re.sub(r'<!-- inst-evidence:start -->.*?<!-- inst-evidence:end -->', lambda _: new, h, flags=re.S)
        else:
            h, n = re.subn(start_pat, lambda _: new, h, count=1, flags=re.S)
            if not n: raise SystemExit(f'{p.name}: 받은 사례 블록 위치를 찾지 못했습니다')
        # 비교 표 칸: 재단·신보·기보 건수를 원장에서
        h = re.sub(r'<tr><td><b>(?:실측 기록|받은 사례)</b></td>.*?</tr>',
                   lambda _: f'<tr><td><b>받은 사례</b></td><td>{cell("jaedan")}</td><td>{cell("sinbo")}</td><td>{cell("gibo")}</td></tr>', h, count=1, flags=re.S)
        p.write_text(h, encoding='utf-8')
    p = ROOT / 'bojeung.html'
    h = p.read_text(encoding='utf-8')
    h = h.replace('<th>실측 기록</th>', '<th>받은 사례</th>')
    for label, key in (('지역 신용보증재단</b> (17개 시도)', 'jaedan'), ('기술보증기금</b>', 'gibo'), ('신용보증기금</b>', 'sinbo')):
        h = re.sub(r'(<tr><td><b>' + re.escape(label) + r'</td><td>[^<]*</td><td>)[^<]*(</td>)', lambda m: m.group(1) + cell(key) + m.group(2), h, count=1)
    p.write_text(h, encoding='utf-8')


if __name__ == '__main__':
    apply(); print('[기관 사례 블록 OK]', {k: summary(pick(rows(), k))['n'] for k in INST})
