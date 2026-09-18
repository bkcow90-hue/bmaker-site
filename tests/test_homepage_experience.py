from html.parser import HTMLParser
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


class HomePageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.elements = []

    def handle_starttag(self, tag, attrs):
        element = {"tag": tag, "attrs": dict(attrs), "text": ""}
        self.stack.append(element)
        self.elements.append(element)

    def handle_startendtag(self, tag, attrs):
        self.elements.append({"tag": tag, "attrs": dict(attrs), "text": ""})

    def handle_data(self, data):
        for element in self.stack:
            element["text"] += data

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index]["tag"] == tag:
                del self.stack[index:]
                break


class HeroHeadingParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self._inside_heading = False
        self.lines = [""]

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "h1" and "serif" in attributes.get("class", "").split():
            self._inside_heading = True
        elif tag == "br" and self._inside_heading:
            self.lines.append("")

    def handle_data(self, data):
        if self._inside_heading:
            self.lines[-1] += data

    def handle_endtag(self, tag):
        if tag == "h1" and self._inside_heading:
            self._inside_heading = False
            self.lines = [" ".join(line.split()) for line in self.lines]


class HomepageExperienceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        cls.source = index
        parser = HomePageParser()
        parser.feed(index)
        cls.elements = parser.elements
        heading_parser = HeroHeadingParser()
        heading_parser.feed(index)
        cls.hero_heading_lines = heading_parser.lines

    def test_hero_heading_has_three_intentional_lines(self):
        lines = self.hero_heading_lines
        self.assertEqual(len(lines), 3)
        self.assertRegex(lines[0], r"^사장님 [\d,]+분이,$")
        self.assertRegex(lines[1], r"^정책자금 [\d,]+억을$")
        self.assertEqual(lines[2], "받았습니다.")

    def test_hero_says_one_thing_with_a_single_reservation_button(self):
        """히어로 = 라벨 + H1 + 서브 1문장 + 버튼 1개. 카톡·안내문·칩·사례 카드는 히어로 밖으로."""
        hero = re.search(r'<section class="hero">.*?</section>', self.source, re.S).group(0)
        self.assertIn('<span class="eyebrow">정책자금 컨설팅, 비즈니스 메이커</span>', hero)
        self.assertEqual(hero.count("<h1"), 1)
        leads = re.findall(r'<p class="lead">(.*?)</p>', hero)
        self.assertEqual(leads, ["우리 회사도 되는지, 무료로 먼저 봐드립니다."])
        actions = re.findall(r'<(?:a|button)[\s>].*?</(?:a|button)>', hero, re.S)
        self.assertEqual(len(actions), 1, actions)
        self.assertIn('href="#apply"', actions[0])
        self.assertIn(">무료 진단 예약하기 →<", actions[0])
        self.assertNotIn("btn-kakao", actions[0])
        for gone in ("pf.kakao.com", "hero-note", "어떤 서비스가 필요한지", "home-recent", "home-proof", "신뢰 지표"):
            with self.subTest(gone=gone):
                self.assertNotIn(gone, hero)
        self.assertIn('src="assets/hero-consult.webp"', hero)

    def test_trust_signals_sit_in_a_strip_right_below_the_hero(self):
        trust_lists = [
            element
            for element in self.elements
            if element["tag"] == "ul"
            and element["attrs"].get("aria-label") == "비즈니스 메이커 신뢰 지표"
        ]

        self.assertEqual(len(trust_lists), 1)
        trust_text = " ".join(trust_lists[0]["text"].split())
        for signal in ("받은 사례", "영업 12년", "착수금·진행비용 없음", "전국 무료 상담"):
            with self.subTest(signal=signal):
                self.assertIn(signal, trust_text)
        # 히어로 바로 다음 섹션이 신뢰 스트립이어야 첫 화면 다음 시선에 걸린다
        after_hero = self.source.split('<section class="hero">', 1)[1].split("</section>", 1)[1]
        self.assertTrue(after_hero.lstrip().startswith('<section class="trust-strip"'), after_hero[:80])

    def test_recent_cases_are_an_independent_section_after_the_hero(self):
        """GEO 1차 소스 데이터 — 삭제 금지, 위치만 히어로 다음으로."""
        src = self.source
        recent = re.search(r'<section class="recent" id="recent"[^>]*>.*?</section>', src, re.S)
        self.assertIsNotNone(recent)
        self.assertIn(">최근에 받은 사례</h2>", recent.group(0))
        self.assertRegex(recent.group(0), r"<!-- home-recent:start -->(<li>.+?</li>){3}<!-- home-recent:end -->")
        self.assertEqual(src.count("<!-- home-recent:start -->"), 1)
        self.assertLess(src.index('<section class="trust-strip"'), recent.start())
        self.assertLess(recent.start(), src.index('<section class="why"'))

    def test_home_has_exactly_one_h1(self):
        self.assertEqual(len([e for e in self.elements if e["tag"] == "h1"]), 1)

    def test_hero_cta_is_addressable_for_the_sticky_bar_rule(self):
        """고정바 노출 규칙의 실제 동작은 tests/test_sticky_cta.py(브라우저)에서 검증한다.
        여기서는 그 규칙이 붙을 자리(히어로 CTA 의 id)만 고정한다."""
        hero = re.search(r'<section class="hero">.*?</section>', self.source, re.S).group(0)
        self.assertIn('id="heroCta"', hero)
        self.assertEqual(self.source.count('id="heroCta"'), 1)

    def test_reservation_actions_are_visually_distinct_from_kakao_actions(self):
        reservation_actions = [
            element
            for element in self.elements
            if element["tag"] in {"a", "button"}
            and any(k in " ".join(element["text"].split()) for k in ("상담 신청", "진단 예약"))
        ]

        self.assertGreaterEqual(len(reservation_actions), 3)
        for action in reservation_actions:
            classes = action["attrs"].get("class", "").split()
            with self.subTest(tag=action["tag"], classes=classes):
                self.assertNotIn("btn-kakao", classes)

    def test_case_results_are_announced_as_a_static_list(self):
        case_lists = [
            element
            for element in self.elements
            if "case-marquee" in element["attrs"].get("class", "").split()
        ]

        self.assertEqual(len(case_lists), 1)
        self.assertEqual(case_lists[0]["attrs"].get("aria-label"), "승인사례 목록")

    def test_news_hides_instagram_while_guidebook_event_remains_visible(self):
        instagram_grid = next(
            element
            for element in self.elements
            if element["attrs"].get("id") == "instaGrid"
        )
        instagram_more = next(
            element
            for element in self.elements
            if "media-more" in element["attrs"].get("class", "").split()
        )
        guidebook_event = next(
            element
            for element in self.elements
            if "event-banner" in element["attrs"].get("class", "").split()
        )

        self.assertIn("hidden", instagram_grid["attrs"])
        self.assertIn("hidden", instagram_more["attrs"])
        self.assertNotIn("hidden", guidebook_event["attrs"])


class ScrollRevealTests(unittest.TestCase):
    """스크롤 리빌은 conversion.js 가 CSS 까지 주입해 정적 페이지도 덮는다.
    홈의 기존 .reveal/.on 구현과 섞이면 이중 적용이 되므로 네임스페이스를 분리한다."""

    def test_scroll_reveal_is_injected_scoped_and_excludes_interactive_surfaces(self):
        js = (ROOT / "assets/conversion.js").read_text(encoding="utf-8")
        home = (ROOT / "index.html").read_text(encoding="utf-8")

        # CSS 단일 출처: 스크립트가 주입하고 페이지 <style> 에는 없다
        self.assertIn(".rv{opacity:0", js)
        self.assertIn(".rv-in{opacity:1", js)
        self.assertIn("data-rv", js)
        self.assertNotIn(".rv{opacity:0", home)

        # 모션 저감 설정 존중
        self.assertIn("(prefers-reduced-motion: reduce)", js)
        self.assertIn("@media(prefers-reduced-motion:reduce){.rv{", js)

        # 제외 대상 — 히어로·폼·CTA·고정바, 그리고 홈의 기존 .reveal
        exclude = js.split("var EXCLUDE")[1].split(";")[0]
        for selector in (".hero", "#leadForm", ".cta-inline", ".sticky-cta", ".reveal"):
            with self.subTest(selector=selector):
                self.assertIn(selector, exclude)

        # 큰 표는 행 단위가 아니라 컨테이너 단위로 등장
        self.assertIn("rows.length <= 20", js)

        # 홈의 기존 구현은 그대로 남아 있어야 한다 (이중 적용 방지의 반대편 확인)
        self.assertIn(".reveal{opacity:0", home)
        self.assertIn("classList.add('on')", home)

if __name__ == "__main__":
    unittest.main()
