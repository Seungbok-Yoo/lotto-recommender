"""웹 페이지 빌드 / 테스트.

src/ 의 조각(스타일·로직·컴포넌트)과 ../lotto_history.json 을 합쳐
dist/lotto_app.html 한 파일을 만든다. Node.js 없이 Python 만으로 동작한다.

사용 예:
    python web/build.py           # dist/lotto_app.html 생성
    python web/build.py --test    # tests/runner.html 을 Edge 헤드리스로 실행
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
DIST = ROOT / "dist" / "lotto_app.html"
DATA = ROOT.parent / "lotto_history.json"

# 합치는 순서가 곧 의존 순서다 (번들러가 없어 모든 파일이 한 전역 스코프를 공유).
STYLES = ["tokens.css", "base.css", "ball.css", "generator.css", "dashboard.css"]
LIB = ["lotto.js", "stats.js"]                     # 일반 <script>: 순수 로직
APP = [                                            # <script type="text/babel">: 화면
    "constants.js",
    "components/Ball.jsx",
    "components/GeneratorControls.jsx",
    "components/GameSlip.jsx",
    "components/Generator.jsx",
    "components/DistributionChart.jsx",
    "components/StatCards.jsx",
    "components/Dashboard.jsx",
    "App.jsx",                                     # 마지막: 렌더 시작
]

# 테스트용 헤드리스 브라우저: Windows 는 설치 경로, Linux(GitHub Actions) 는 PATH 에서 찾는다.
BROWSER_PATHS = [
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
]
BROWSER_COMMANDS = ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "microsoft-edge"]


def find_browser() -> str | None:
    for path in BROWSER_PATHS:
        if path.exists():
            return str(path)
    for cmd in BROWSER_COMMANDS:
        found = shutil.which(cmd)
        if found:
            return found
    return None


def concat(folder: Path, names: list[str]) -> str:
    parts = []
    for name in names:
        text = (folder / name).read_text(encoding="utf-8").rstrip()
        parts.append(f"/* ---- {name} ---- */\n{text}")
    return "\n\n".join(parts)


def load_rows() -> list[list[int]]:
    """lotto_history.json → [[회차, 번호1..6, 보너스], ...] (회차 오름차순)."""
    draws = json.loads(DATA.read_text(encoding="utf-8"))
    return [[d["round"], *d["numbers"], d["bonus"]] for d in sorted(draws, key=lambda d: d["round"])]


def build() -> Path:
    rows = load_rows()
    if not rows:
        sys.exit(f"{DATA} 에 당첨 이력이 없습니다. 먼저 `python lottery.py --update` 를 실행하세요.")

    parts = {
        "styles": concat(SRC / "styles", STYLES),
        "data": "// [회차, 번호1..6, 보너스] — lotto_history.json 에서 생성\n"
                f"window.RAW_DRAWS = {json.dumps(rows, separators=(',', ':'))};",
        "lib": concat(SRC / "lib", LIB),
        "app": concat(SRC / "app", APP),
    }
    html = (SRC / "index.html").read_text(encoding="utf-8")
    for key, value in parts.items():
        marker = f"/*@{key}*/"
        if marker not in html:
            sys.exit(f"index.html 에 {marker} 자리표시가 없습니다.")
        html = html.replace(marker, value)

    DIST.parent.mkdir(exist_ok=True)
    DIST.write_text(html, encoding="utf-8")
    # GitHub Pages 는 폴더의 index.html 을 첫 화면으로 쓴다
    (DIST.parent / "index.html").write_text(html, encoding="utf-8")
    print(f"빌드 완료: {DIST.relative_to(ROOT.parent)}  "
          f"({len(rows)}회차, 1~{rows[-1][0]}회, {DIST.stat().st_size / 1024:.0f} KB)")
    return DIST


def run_tests() -> int:
    browser = find_browser()
    if browser is None:
        print("Edge/Chrome 을 찾지 못했습니다. web/tests/runner.html 을 브라우저로 직접 여세요.")
        return 1
    runner = (ROOT / "tests" / "runner.html").as_uri()
    cmd = [browser, "--headless=new", "--disable-gpu", "--allow-file-access-from-files", "--dump-dom", runner]
    if sys.platform.startswith("linux"):
        cmd.insert(1, "--no-sandbox")  # CI 컨테이너에서 샌드박스 초기화 실패 방지
    out = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=60).stdout
    lines = [re.sub(r"<[^>]+>", "", m) for m in re.findall(r"<li[^>]*>.*?</li>", out, re.S)]
    summary = re.search(r'<h1 id="summary">(.*?)</h1>', out)
    for line in lines:
        print("  " + line.replace("&amp;", "&").replace("&gt;", ">").replace("&lt;", "<"))
    print(summary.group(1) if summary else "테스트 결과를 읽지 못했습니다.")
    return 0 if summary and summary.group(1).startswith("ALL PASS") else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="로또 웹 페이지 빌드/테스트")
    parser.add_argument("--test", action="store_true", help="단위 테스트 실행")
    args = parser.parse_args()
    if args.test:
        return run_tests()
    build()
    return 0


if __name__ == "__main__":
    sys.exit(main())
