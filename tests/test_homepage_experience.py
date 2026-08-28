from html.parser import HTMLParser
from pathlib import Path
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
        parser = HomePageParser()
        parser.feed(index)
        cls.elements = parser.elements
        heading_parser = HeroHeadingParser()
        heading_parser.feed(index)
        cls.hero_heading_lines = heading_parser.lines

    def test_hero_heading_has_three_intentional_lines(self):
        self.assertEqual(
            self.hero_heading_lines,
            ["가능한 자금과", "준비할 순서를", "정확하게 진단합니다."],
        )

    def test_first_screen_exposes_four_concrete_trust_signals(self):
        trust_lists = [
            element
            for element in self.elements
            if element["tag"] == "ul"
            and element["attrs"].get("aria-label") == "비즈니스 메이커 신뢰 지표"
        ]

        self.assertEqual(len(trust_lists), 1)
        trust_text = " ".join(trust_lists[0]["text"].split())
        for signal in ("영업 12년", "연 250개 기업", "착수금·진행비 없음", "전국 비대면"):
            with self.subTest(signal=signal):
                self.assertIn(signal, trust_text)

    def test_reservation_actions_are_visually_distinct_from_kakao_actions(self):
        reservation_actions = [
            element
            for element in self.elements
            if element["tag"] in {"a", "button"}
            and "무료 진단 예약" in " ".join(element["text"].split())
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


if __name__ == "__main__":
    unittest.main()
