"""내비 항목이 전 페이지에서 같은지 — 기준은 index.html.

빌더가 페이지를 만들 때 header 를 서로 복사하므로, 한 곳만 고치고 체인을 안 돌리면
셸이 갈라진다(실제로 marketing.html 계열 11장이 옛 메뉴로 남아 있던 적이 있다).
검사 대상은 glob 으로 모은다 — 파일 목록을 손으로 적으면 새 페이지가 빠진다.
404·privacy 는 내비를 일부러 줄여 두었으므로 제외한다.
"""
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SKIP = {'404.html', 'privacy.html'}
BASE = 'index.html'

NAV = re.compile(r'<nav\b[^>]*>(.*?)</nav>', re.S)
LINK = re.compile(r'<a\b[^>]*?href="([^"]*)"[^>]*>(.*?)</a>', re.S)
TAG = re.compile(r'<[^>]+>')


def pages():
    found = sorted(ROOT.glob('*.html')) + sorted(ROOT.glob('industry/*.html'))
    return [p for p in found if p.name not in SKIP]


def nav_items(path):
    """페이지의 주 내비 항목 [(href, 표시 문구), ...]."""
    html = path.read_text(encoding='utf-8')
    navs = NAV.findall(html)
    assert navs, f'{path.name}: <nav> 가 없습니다'
    return [(href, TAG.sub('', text).strip()) for href, text in LINK.findall(navs[0])]


BASELINE = nav_items(ROOT / BASE)


def test_baseline_is_not_empty():
    assert len(BASELINE) >= 5, f'{BASE} 내비 항목이 {len(BASELINE)}개 — 기준으로 쓸 수 없습니다'


def test_pages_collected():
    names = {p.name for p in pages()}
    assert BASE in names
    assert not (names & SKIP)
    assert len(names) > 40, f'검사 대상이 {len(names)}개뿐 — glob 확인'


@pytest.mark.parametrize('path', pages(), ids=lambda p: p.relative_to(ROOT).as_posix())
def test_nav_matches_index(path):
    """순서·문구·href 까지 index.html 과 같아야 한다."""
    items = nav_items(path)
    if items == BASELINE:
        return
    missing = [i for i in BASELINE if i not in items]
    extra = [i for i in items if i not in BASELINE]
    order = items != BASELINE and not missing and not extra
    raise AssertionError(
        f'{path.relative_to(ROOT).as_posix()} 내비가 {BASE} 와 다릅니다\n'
        f'  빠짐: {missing or "없음"}\n'
        f'  추가: {extra or "없음"}\n'
        f'  {"순서만 다름" if order else ""}\n'
        f'  기준({len(BASELINE)}): {BASELINE}\n'
        f'  실제({len(items)}): {items}')
