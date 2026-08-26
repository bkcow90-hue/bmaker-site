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


class HomepageExperienceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        parser = HomePageParser()
        parser.feed((ROOT / "index.html").read_text(encoding="utf-8"))
        cls.elements = parser.elements

    def test_first_screen_exposes_four_concrete_trust_signals(self):
        trust_lists = [
            element
            for element in self.elements
            if element["tag"] == "ul"
            and element["attrs"].get("aria-label") == "비즈니스 메이커 신뢰 지표"
        ]

        self.assertEqual(len(trust_lists), 1)
        trust_text = " ".join(trust_lists[0]["text"].split())
        for signal in ("영업 12년", "연 250개 기업", "착수금 없음", "전국 비대면"):
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


if __name__ == "__main__":
    unittest.main()
