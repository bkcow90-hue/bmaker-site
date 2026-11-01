"""Service-specific conversion copy; program facts and search metadata stay in page builders."""
from html import escape

STYLESHEET = '<link rel="stylesheet" href="/assets/service-consulting.css">'

SERVICES = {
    'sosangin': {
        'label': '준비 상담',   # 허브 히어로 라벨 — 키워드 반복은 title·h1·첫 문장에만(2026-11-02)
        'checks': ['소진공·지역재단 중 검토할 경로', '업종·업력·기존 대출에 맞는 조건', '매출 자료와 신청 서류 준비 순서'],
        'heading': '자금 이름을 찾는 일부터, 내 사업에 맞게 준비하는 일까지.',
        'works': [
            ('여러 공고 중 검토할 경로를 좁힙니다', '사업장 지역, 업종과 업력, 자금 용도를 듣고 소진공·지역재단·지자체 경로의 요건을 비교합니다.', '상담 전 정리할 정보', '사업장 소재지 · 개업 시점 · 필요한 자금의 용도'),
            ('흩어진 사업 자료를 신청 기준에 맞춥니다', '매출 증빙과 기존 대출 내역, 사업계획서에 적을 내용을 함께 살펴보고 빠진 자료와 확인할 숫자를 정리합니다.', '함께 검토할 자료', '매출 증빙 · 기존 대출·보증 내역 · 자금 사용 계획'),
            ('추가 요청에 무엇을 준비할지 안내합니다', '신청 과정에서 보완을 요청받으면 요청 내용과 기존 제출 자료를 대조해 준비할 사항을 안내합니다.', '진행 중 확인할 사항', '추가 요청 서류 · 자료 간 차이 · 기관에 확인할 질문'),
        ],
    },
    'jungsogieop': {
        'label': '준비 상담',
        'checks': ['중진공·신보·기보 검토 순서', '운전·시설자금과 재무 자료의 연결', '사업계획서와 심사 보완 준비'],
        'heading': '자금 계획과 재무 자료가 같은 이야기를 하도록 준비합니다.',
        'works': [
            ('자금의 용도부터 기관을 비교합니다', '운전자금인지 시설자금인지, 필요한 시점과 기존 차입 현황은 어떤지 확인하고 중진공·신보·기보의 검토 순서를 정리합니다.', '처음 확인할 내용', '자금 용도 · 필요한 시점 · 현재 차입·보증 현황'),
            ('사업계획서의 설명과 숫자를 대조합니다', '사업 계획, 매출 자료와 재무제표를 함께 보며 근거가 필요한 항목과 추가로 정리할 자료를 짚습니다.', '함께 검토할 자료', '재무제표 · 매출 자료 · 투자·시설 계획 · 사업계획서'),
            ('심사 과정의 보완 준비를 돕습니다', '추가 자료 요청을 항목별로 정리하고 회사가 설명해야 할 내용과 확인 근거를 준비하도록 돕습니다.', '진행 중 준비할 내용', '추가 자료 목록 · 수치의 근거 · 사업 현황 설명'),
        ],
    },
    'bojeung': {
        'label': '보증서 대출 준비 상담',
        'checks': ['신보·기보·지역재단 비교', '기존 보증과 신규 자금 용도', '보증심사와 은행 접수 준비'],
        'heading': '보증기관 선택부터 은행 접수 준비까지, 연결해서 살펴봅니다.',
        'works': [
            ('기업 상황에 맞는 보증 경로를 검토합니다', '사업 규모와 업종, 기술·매출 자료, 기존 보증 이용 내역을 바탕으로 신보·기보·지역재단에서 확인할 조건을 정리합니다.', '처음 확인할 내용', '사업 규모 · 업종 · 기술·매출 현황 · 기존 보증'),
            ('보증심사에 설명할 자료를 정리합니다', '필요 자금의 용도와 사업 현황이 서류에 일관되게 드러나도록 자료를 대조하고 보완할 부분을 확인합니다.', '함께 준비할 자료', '자금 사용 계획 · 매출·재무 자료 · 기존 채무 내역'),
            ('보증 이후의 진행 단계도 안내합니다', '보증약정과 은행 접수에서 확인할 절차, 추가 요청 자료를 정리해 다음 단계의 준비를 돕습니다.', '구분해서 확인할 항목', '보증약정 · 은행 요청 자료 · 보증료와 대출이자'),
        ],
    },
    'certification': {
        'label': '기업인증·연구소 준비 상담',
        'checks': ['인증이 필요한 목적과 적용 요건', '현재 인력·공간·사업 자료', '신청 준비와 취득 후 관리 범위'],
        'heading': '인증 이름보다, 우리 회사에 필요한 이유와 준비할 요건부터.',
        'works': [
            ('자금 계획과 인증 목적을 함께 봅니다', '정책자금·보증 검토, 거래처 요구 등 인증을 알아보는 이유를 듣고 어떤 요건과 활용 조건을 확인해야 하는지 정리합니다.', '먼저 정할 내용', '인증 목적 · 검토 중인 자금·보증 · 거래처 요구 사항'),
            ('지금 갖춘 요건과 보완할 자료를 나눕니다', '인증 종류에 따라 사업 자료, 연구 인력과 공간 등 필요한 항목을 살피고 신청 전에 준비할 사항을 안내합니다.', '함께 확인할 자료', '사업 현황 · 인력·공간 자료 · 기존 인증과 신청 이력'),
            ('신청과 취득 후 관리까지 범위를 정합니다', '신청 자료와 심사 대응, 취득 후 관리에서 어떤 업무를 맡길지 구분합니다. 전문 검토가 필요한 사항은 해당 분야 협업 범위를 안내합니다.', '상담에서 정리할 사항', '신청 준비 · 보완 대응 · 취득 후 확인할 관리 항목'),
        ],
    },
}


def region_config(region, name):
    return {
        'label': f'{region} 사업장 재단 대출 준비 상담',
        'checks': [f'{name} 공고의 신청 조건', '사업장 소재지와 기존 보증 내역', '지역 상품에 맞춘 신청 서류'],
        'heading': f'{region} 사업장이라면, 지역 공고와 내 사업 조건을 함께 확인합니다.',
        'works': [
            ('지역 공고에서 확인할 조건을 정리합니다', f'{name}의 상품별 안내와 사업장 소재지를 함께 살펴보고 대상·제외 조건과 신청 경로를 확인합니다.', '처음 확인할 내용', '사업장 소재지 · 업종 · 개업 시점 · 자금 용도'),
            ('기존 보증과 준비 자료를 함께 살핍니다', '이용 중인 보증·대출과 매출 자료를 듣고, 공고에서 추가로 확인할 사항과 신청 전에 준비할 서류를 정리합니다.', '함께 검토할 자료', '매출 증빙 · 기존 보증·대출 내역 · 사업장 관련 서류'),
        ],
    }


def hero_content(h1_html, lead_html, cfg, service='policy'):
    """h1/lead are existing trusted page markup; configuration strings are escaped."""
    checks = ''.join(f'<li>{escape(item)}</li>' for item in cfg['checks'])
    return f'''<div class="sc-hero-grid"><div>
    <p class="sc-label">비즈니스 메이커 · {escape(cfg['label'])}</p>
    {h1_html}
    <div class="sc-lead">{lead_html}</div>
  </div><aside class="sc-consult" aria-label="상담에서 확인할 내용">
    <h2>상담에서 함께 확인합니다</h2><ul>{checks}</ul>
    <a class="btn sc-apply" id="heroCta" href="#apply" data-cta-location="hero" data-consultation-service="{service}">무료 진단 신청</a>
    <p class="sc-small">비즈니스 메이커 상담 신청 · 처음에는 서류 첨부 없이</p>
  </aside></div>
  <nav class="sc-jumps" aria-label="페이지 안내"><a href="#sc-service">맡길 수 있는 업무</a><a href="#sc-guide">상세 안내와 근거</a><a href="/#about">담당자 소개</a></nav>'''


def service_content(cfg):
    rows = ''.join(f'''<div class="sc-work"><div><h3>{escape(title)}</h3><p>{escape(body)}</p></div>
    <p class="sc-answer"><b>{escape(label)}</b>{escape(answer)}</p></div>'''
        for title, body, label, answer in cfg['works'])
    return f'''<section class="sc-service" id="sc-service" aria-labelledby="sc-service-title">
    <h2 id="sc-service-title" class="serif">{escape(cfg['heading'])}</h2>{rows}
    <div class="sc-team"><p><b>전담 상담팀이 듣고, 대표가 주요 검토와 진행 관리에 참여합니다.</b></p>
    <p>사업 현황을 바탕으로 검토할 조건과 준비할 자료를 정리합니다. 업무의 범위와 진행 방식은 상담에서 안내합니다.</p>
    <p><a href="/#about">대표와 협업 체계 확인</a> · <a href="/consulting">컨설팅 업무 안내</a> · <a href="/cases">공개 사례와 근거 보기</a></p></div>
    </section>'''
