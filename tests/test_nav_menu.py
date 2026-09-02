"""공통 헤더 메뉴 존재 강제 — 표준 헤더를 쓰는 모든 페이지에 nav-menu가 있어야 한다."""
import glob
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
def test_nav_menu_everywhere():
    for f in glob.glob(str(ROOT/"*.html")):
        name = Path(f).name
        if name in ("index.html", "404.html", "privacy.html"): continue
        h = Path(f).read_text(encoding="utf-8")
        if 'class="nav-actions"' in h:
            assert 'class="nav-menu"' in h, name
