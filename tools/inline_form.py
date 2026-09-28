# -*- coding: utf-8 -*-
"""자금·재단 상세 페이지 본문 중간에 넣는 인라인 진단 폼.

자금 15장(build_funds)과 재단 18장(build_jaedan), 허브 2장(build_hubs), 4분기 안내(2026-4q-sosangin.html,
정적 — 이 함수 출력을 그대로 붙여 넣었다)가 같은 마크업을 쓰도록 한 곳에서 만든다.
홈(index.html) 폼은 스타일이 홈 <style> 에만 있으므로 다른 페이지로 복사하지 않는다 — 2026-09-28 허브 2장이
홈 폼 HTML 만 복사해 브라우저 기본 모양(19px 입력칸·회색 버튼)으로 PR #7 부터 배포돼 있었다.
문구가 두 빌더에서 갈리면 페이지별 전환율 비교가 무의미해진다.

전송은 기존 assets/conversion.js 와 https://codedaum.pages.dev/api/lead 를 그대로 쓴다.
conversion.js 가 읽는 ID 규약:
  lf-name · lf-phone · lf-consent · lf-website(허니팟) · lf-service(hidden) · applyMsg
  #lf-time .time-opt      통화 희망 시간대
  #lf-biztype .biz-opt    사업자 형태 (이 폼에서 처음 쓴다)
  lf-page                 유입 페이지 (hidden)

사업자 형태와 유입 페이지는 /api/lead 가 화이트리스트로 거르는 최상위 키로는 전달되지
않는다 — 2026-09-28 메일 템플릿 렌더로 확인했다. conversion.js 가 answers_text 와
diagnosis 에 실어 보내므로 알림 메일 본문의 [진단 답변]·[진단 답변 상세]에 찍힌다.
"""
import html

TITLE = '이 자금, 우리 회사도 되는지 무료로 확인'
TITLE_GENERAL = '우리 회사도 되는지 무료로 확인'   # 자금 하나가 아닌 페이지(허브·4분기)
BUTTON = '무료 진단 신청'   # 전 사이트 통일 (규격 4절, 2026-09-28)
BIZ_TYPES = [('개인사업자', '개인사업자'), ('법인사업자', '법인사업자'), ('창업 예정', '예정')]

CSS = (
 '.inline-diag{border-top:2px solid var(--navy,#0E1B33);border-bottom:1px solid var(--line,#E1DED6);'
 'background:var(--paper,#F7F5F0);padding:26px 24px;margin:28px 0}'
 '.inline-diag h2{margin:0 0 6px;padding:0;border:0;font-size:1.18rem;line-height:1.45;color:var(--navy,#0E1B33)}'
 '.inline-diag .sub{margin:0 0 18px;font-size:.92rem;color:#4a5669;line-height:1.6}'
 '.inline-diag .row{display:grid;grid-template-columns:1fr 1fr;gap:14px}'
 '.inline-diag label,.inline-diag .field-label{display:block;font-size:.9rem;font-weight:700;'
 'color:#263951;margin:0 0 7px}'
 '.inline-diag input[type=text],.inline-diag input[type=tel]{width:100%;padding:13px 14px;border-radius:4px;'
 'border:1px solid #aeb9ca;background:#fff;color:#1A2233;font-size:1rem;font-family:inherit;min-height:46px}'
 '.inline-diag input::placeholder{color:#8792a5}'
 '.inline-diag input:focus{outline:2px solid var(--blue,#2B5BE3);border-color:var(--blue,#2B5BE3)}'
 '.inline-diag .opts{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}'
 '.inline-diag .opts button{padding:12px 4px;border-radius:4px;border:1px solid #bdc7d8;background:#fff;'
 'color:#263951;font-size:.88rem;font-weight:600;font-family:inherit;cursor:pointer;min-height:44px}'
 '.inline-diag .opts button[aria-pressed=true]{background:#2454bc;border-color:#2454bc;color:#fff}'
 '.inline-diag .group{margin-top:16px}'
 '.inline-diag .consent{display:flex;align-items:flex-start;gap:9px;margin-top:16px;font-size:.86rem;'
 'line-height:1.6;color:#4a5669;font-weight:400}'
 '.inline-diag .consent input{width:20px;height:20px;flex-shrink:0;margin-top:2px;accent-color:#2454bc}'
 '.inline-diag .consent a{color:#1e44b8;text-decoration:underline}'
 '.inline-diag button[type=submit]{width:100%;margin-top:18px;background:#2454bc;color:#fff;'
 'border:1px solid #2454bc;border-radius:4px;padding:16px;font-size:1.04rem;font-weight:700;'
 'cursor:pointer;font-family:inherit}'
 '.inline-diag button[type=submit]:disabled{opacity:.65;cursor:wait}'
 '.inline-diag .note{margin-top:12px;font-size:.84rem;color:#526077;line-height:1.55}'
 '.inline-diag .apply-msg{margin-top:14px;font-size:.9rem;text-align:center;display:none}'
 '.inline-diag .apply-msg.ok{display:block;color:#126435}'
 '.inline-diag .apply-msg.err{display:block;color:#b32b28}'
 '.inline-diag .apply-fallback{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:14px}'
 '.inline-diag .apply-fallback a{display:flex;align-items:center;justify-content:center;font-weight:700;'
 'font-size:.9rem;border-radius:4px;padding:12px 8px;text-decoration:none}'
 '.inline-diag .apply-fallback .fb-kakao{background:var(--kakao,#FEE500);color:#191600}'
 '.inline-diag .apply-fallback .fb-tel{border:1px solid #aeb9ca;color:#263951}'
 '@media(max-width:680px){.inline-diag{padding:22px 18px;margin:24px 0}'
 '.inline-diag .row{grid-template-columns:1fr;gap:0}.inline-diag .row>div+div{margin-top:16px}'
 '.inline-diag .opts{grid-template-columns:1fr}}'
)


def form_html(page_path, page_label, title=TITLE):
    """page_path·page_label 은 어느 페이지에서 온 신청인지 알림 메일에 남기는 값이다."""
    e = lambda s: html.escape(s, quote=True)
    where = '%s (%s)' % (page_path, page_label)
    biz = ''.join(
        '<button type="button" class="biz-opt" aria-pressed="false">%s</button>' % e(label)
        for label, _ in BIZ_TYPES)
    return (
 '<section id="apply" class="inline-diag" aria-label="무료 진단 예약">\n'
 '  <form id="leadForm" aria-labelledby="inline-diag-title">\n'
 '    <h2 id="inline-diag-title" class="serif">%s</h2>\n' % e(title) +
 '    <p class="sub">연락처를 남겨주시면 사업 조건으로 이 경로가 맞는지 확인해 알려드립니다. '
 '진단은 무료이고, 정책자금은 착수금이 없습니다.</p>\n'
 '    <input type="text" name="website" id="lf-website" tabindex="-1" autocomplete="off" '
 'style="position:absolute;left:-9999px;opacity:0" aria-hidden="true">\n'
 '    <input type="hidden" id="lf-service" name="consultation_service" value="policy">\n'
 '    <input type="hidden" id="lf-page" value="%s">\n' % e(where) +
 '    <p class="field-label" id="lf-biztype-label">사업자 형태</p>\n'
 '    <div class="opts" role="group" aria-labelledby="lf-biztype-label" id="lf-biztype">%s</div>\n' % biz +
 '    <div class="row group">\n'
 '      <div><label for="lf-name">성함 (필수)</label>'
 '<input id="lf-name" name="name" type="text" placeholder="홍길동" required autocomplete="name"></div>\n'
 '      <div><label for="lf-phone">연락처 (필수)</label>'
 '<input id="lf-phone" name="phone" type="tel" placeholder="010-0000-0000" required autocomplete="tel" '
 'inputmode="tel" maxlength="20"></div>\n'
 '    </div>\n'
 '    <div class="group">\n'
 '      <p class="field-label" id="lf-time-label">통화 희망 시간</p>\n'
 '      <div class="opts" role="group" aria-labelledby="lf-time-label" id="lf-time">'
 '<button type="button" class="time-opt" aria-pressed="false">오전 (9~12시)</button>'
 '<button type="button" class="time-opt" aria-pressed="false">오후 (12~6시)</button>'
 '<button type="button" class="time-opt" aria-pressed="false">아무 때나</button></div>\n'
 '    </div>\n'
 '    <label class="consent"><input type="checkbox" id="lf-consent" required> '
 '<span>개인정보 수집·이용에 동의합니다. 상담 목적으로만 사용됩니다. '
 '<a href="/privacy" target="_blank" rel="noopener">개인정보처리방침 보기</a></span></label>\n'
 '    <button type="submit">%s</button>\n' % e(BUTTON) +
 '    <p class="apply-msg" id="applyMsg" role="status" aria-live="polite" tabindex="-1"></p>\n'
 '    <p class="note">서류 첨부는 필요하지 않습니다. 평일 09:00–18:00에 연락드립니다. '
 '승인 여부와 조건은 각 심사 기관이 결정합니다.</p>\n'
 '    <noscript>온라인 신청에는 자바스크립트가 필요합니다. 전화 1666-2425 또는 카톡 상담을 이용해 주세요.</noscript>\n'
 '  </form>\n'
 '</section>\n')
