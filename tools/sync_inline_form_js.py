# -*- coding: utf-8 -*-
"""인라인 진단 폼의 마크업·CSS 를 assets/conversion.js 에 옮겨 적는다.

정본은 tools/inline_form.py 다. 폼이 없는 페이지(33장)에 conversion.js 가 '페이지 끝 간편 신청 폼'을 붙일 때
이 사본을 쓴다 — 빌더가 만든 인라인 폼(76장)과 한 글자도 다르면 안 되기 때문이다
(문구가 갈리면 페이지별 전환율 비교가 무의미해지고, CSS 를 빠뜨리면 2026-09-28 허브 2장처럼
브라우저 기본 모양으로 배포된다).

build_lastmod.py 가 자산 해시를 찍기 **전에** sync() 를 부른다. 손으로 고치지 않는다.
검사: tests/test_apply_everywhere.py
"""
import json
import re
from pathlib import Path

import inline_form

ROOT = Path(__file__).resolve().parents[1]
JS = ROOT / 'assets' / 'conversion.js'
PATH_TOKEN, LABEL_TOKEN = '__PATH__', '__LABEL__'
BLOCK = re.compile(r'/\* @inline-form:start[\s\S]*?/\* @inline-form:end \*/')


def render():
    """conversion.js 에 들어갈 구간(LF 줄바꿈)."""
    form = inline_form.form_html(PATH_TOKEN, LABEL_TOKEN, inline_form.TITLE_GENERAL)
    return '\n'.join([
        '/* @inline-form:start — tools/sync_inline_form_js.py 가 tools/inline_form.py 에서 만든다. 손으로 고치지 않는다. */',
        '  const INLINE_FORM_HTML = %s;' % json.dumps(form, ensure_ascii=False),
        '  const INLINE_FORM_CSS = %s;' % json.dumps(inline_form.CSS, ensure_ascii=False),
        '  /* @inline-form:end */',
    ])


def replace(js):
    """js 안의 구간을 최신으로 바꾼 문자열. 파일의 줄바꿈(CRLF/LF)을 그대로 따른다."""
    if not BLOCK.search(js):
        raise SystemExit('assets/conversion.js 에 /* @inline-form:start … @inline-form:end */ 구간이 없습니다')
    eol = '\r\n' if '\r\n' in js else '\n'
    block = render().replace('\n', eol)
    return BLOCK.sub(lambda m: block, js, count=1)


def sync():
    """바뀌었으면 쓰고 True. 같으면 파일을 건드리지 않는다(churn 0)."""
    js = JS.read_bytes().decode('utf-8')   # read_text 는 CRLF 를 LF 로 바꿔 읽는다 — 줄바꿈을 지키려고 바이트로
    new = replace(js)
    if new == js:
        return False
    JS.write_bytes(new.encode('utf-8'))
    return True


if __name__ == '__main__':
    print('conversion.js 인라인 폼 구간:', '갱신' if sync() else '변경 없음')
