"""로또 6/45 번호 추천기.

동행복권 당첨 이력을 내려받아 번호별 출현 빈도를 분석하고,
가중 확률 추출 + 통계 필터를 거쳐 추천 조합을 만든다.

사용 예:
    python lotto_recommender.py                 # 5게임 추천
    python lotto_recommender.py -n 10           # 10게임 추천
    python lotto_recommender.py --mode cold     # 덜 나온 번호 위주
    python lotto_recommender.py --stats         # 통계만 출력
    python lotto_recommender.py --update        # 최신 회차까지 이력 갱신
"""

from __future__ import annotations

import argparse
import http.cookiejar
import json
import math
import random
import ssl
import sys
import urllib.error
import urllib.request
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

NUMBERS = range(1, 46)
PICK = 6
TOTAL_COMBINATIONS = math.comb(45, 6)  # 8,145,060

CACHE_PATH = Path(__file__).with_name("lotto_history.json")
# 2025년 사이트 개편으로 구 API(common.do?method=getLottoNumber)는 메인으로 리다이렉트된다.
# 신규 API는 요청 회차 주변 10개 회차를 한 번에 돌려준다.
API_URL = "https://www.dhlottery.co.kr/lt645/selectPstLt645InfoNew.do?srchLtEpsd={round}"
API_REFERER = "https://www.dhlottery.co.kr/lt645/result"
TIMEOUT = 5

# 통계 필터 기준 (실제 당첨 조합의 대부분이 이 범위에 들어온다)
SUM_RANGE = (100, 175)
ODD_RANGE = (2, 4)
MAX_CONSECUTIVE = 2
MIN_DECADE_SPREAD = 3  # 1~9, 10s, 20s, 30s, 40s 구간 중 최소 몇 개에 걸쳐야 하는지


@dataclass
class Draw:
    round: int
    numbers: list[int]
    bonus: int


# --------------------------------------------------------------------------
# 이력 수집
# --------------------------------------------------------------------------

INSECURE = False  # --insecure 로만 켜짐. 사내망 프록시로 검증이 막힐 때의 탈출구.
_ctx: ssl.SSLContext | None = None


def _context() -> ssl.SSLContext:
    """OS 인증서 저장소(truststore) → certifi → 기본 순으로 검증 컨텍스트를 만든다.

    사내망 TLS 검사 프록시 환경에서는 프록시 CA가 OS 저장소에만 있으므로
    truststore가 가장 확실하다 (`pip install truststore`).
    """
    global _ctx
    if _ctx is not None:
        return _ctx

    if INSECURE:
        _ctx = ssl._create_unverified_context()
        return _ctx

    try:
        import truststore
        _ctx = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        return _ctx
    except ImportError:
        pass

    try:
        import certifi
        _ctx = ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        _ctx = ssl.create_default_context()
    return _ctx


_opener: urllib.request.OpenerDirector | None = None
LAST_ERROR: str | None = None  # 마지막 실패 사유 (사용자 안내용)

USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")


def _get_opener() -> urllib.request.OpenerDirector:
    global _opener
    if _opener is None:
        _opener = urllib.request.build_opener(
            urllib.request.HTTPSHandler(context=_context()),
            urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()),
        )
        _opener.addheaders = [
            ("User-Agent", USER_AGENT),
            ("Referer", API_REFERER),
            ("X-Requested-With", "XMLHttpRequest"),
        ]
    return _opener


_prefetched: dict[int, Draw] = {}  # API가 함께 돌려준 주변 회차


def fetch_draw(round_no: int) -> Draw | None:
    """동행복권 API에서 한 회차를 가져온다. 미추첨/실패 시 None."""
    global LAST_ERROR
    if round_no in _prefetched:
        return _prefetched.pop(round_no)
    try:
        with _get_opener().open(API_URL.format(round=round_no), timeout=TIMEOUT) as res:
            body = res.read().decode("utf-8", "replace")
            final_url = res.url
    except urllib.error.URLError as e:
        reason = getattr(e, "reason", e)
        if isinstance(reason, ssl.SSLError):
            LAST_ERROR = (f"SSL 인증서 검증 실패 ({reason}).\n"
                          "  → `pip install truststore` 후 재시도하거나, "
                          "부득이한 경우 --insecure 를 쓰세요.")
        else:
            LAST_ERROR = f"네트워크 연결 실패 ({reason})"
        return None
    except (TimeoutError, OSError) as e:
        LAST_ERROR = f"네트워크 오류 ({e})"
        return None

    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        # API가 메인/에러 페이지로 리다이렉트된 경우 (API 주소 변경, 해외 IP 차단 등)
        LAST_ERROR = (f"조회 API가 JSON 대신 페이지를 반환했습니다 (→ {final_url}).\n"
                      "  → 동행복권 API 주소가 바뀌었거나 이 네트워크의 접속이 차단된 것으로 보입니다. "
                      "API_URL 을 확인하거나,\n"
                      "     lotto_history.json 에 이력을 직접 넣어 쓰세요 "
                      "(형식: [{\"round\":1,\"numbers\":[..6개..],\"bonus\":n}, ...]).")
        return None

    for item in (data.get("data") or {}).get("list") or []:
        draw = Draw(
            round=int(item["ltEpsd"]),
            numbers=sorted(int(item[f"tm{i}WnNo"]) for i in range(1, 7)),
            bonus=int(item["bnsWnNo"]),
        )
        _prefetched[draw.round] = draw

    LAST_ERROR = None  # 목록에 없으면 아직 추첨되지 않은 회차 — 정상적인 종료 조건
    return _prefetched.pop(round_no, None)


def load_cache() -> list[Draw]:
    if not CACHE_PATH.exists():
        return []
    raw = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    return [Draw(d["round"], d["numbers"], d["bonus"]) for d in raw]


def save_cache(draws: list[Draw]) -> None:
    payload = [{"round": d.round, "numbers": d.numbers, "bonus": d.bonus} for d in draws]
    CACHE_PATH.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def update_history(draws: list[Draw], quiet: bool = False) -> list[Draw]:
    """캐시 이후 회차를 이어서 받아온다. 연속 3회 실패하면 최신 회차로 보고 중단."""
    known = {d.round for d in draws}
    next_round = (max(known) + 1) if known else 1
    misses = 0
    added = 0

    while misses < 3:
        draw = fetch_draw(next_round)
        if draw is None:
            misses += 1
        else:
            draws.append(draw)
            added += 1
            misses = 0
            if not quiet and added % 100 == 0:
                print(f"  ... {draw.round}회차까지 수집", file=sys.stderr)
        next_round += 1

    if added:
        draws.sort(key=lambda d: d.round)
        save_cache(draws)
        if not quiet:
            print(f"이력 {added}회차 갱신 (총 {len(draws)}회차)", file=sys.stderr)
    return draws


def ensure_history(quiet: bool = False) -> list[Draw]:
    draws = load_cache()
    if not draws:
        if not quiet:
            print("당첨 이력을 내려받는 중입니다 (최초 1회, 수 분 소요)...", file=sys.stderr)
        draws = update_history(draws, quiet)
    return draws


# --------------------------------------------------------------------------
# 통계 분석
# --------------------------------------------------------------------------

def frequency(draws: list[Draw]) -> Counter:
    counter = Counter()
    for d in draws:
        counter.update(d.numbers)
    return counter


def recency_weights(draws: list[Draw], half_life: int = 150) -> dict[int, float]:
    """최근 회차일수록 크게 치는 지수 감쇠 가중치."""
    weights = {n: 0.0 for n in NUMBERS}
    if not draws:
        return weights
    latest = max(d.round for d in draws)
    for d in draws:
        w = 0.5 ** ((latest - d.round) / half_life)
        for n in d.numbers:
            weights[n] += w
    return weights


def build_weights(draws: list[Draw], mode: str) -> dict[int, float]:
    """추출 가중치. 전부 양수로 만들어 어떤 번호도 배제되지 않게 한다."""
    if mode == "uniform" or not draws:
        return {n: 1.0 for n in NUMBERS}

    freq = frequency(draws)
    rec = recency_weights(draws)
    expected = len(draws) * PICK / 45  # 번호당 기대 출현 횟수

    weights = {}
    for n in NUMBERS:
        # 전체 빈도와 최근 흐름을 반반 섞어 기대치 대비 비율로 환산
        overall = freq[n] / expected if expected else 1.0
        recent = rec[n] / (sum(rec.values()) / 45) if sum(rec.values()) else 1.0
        score = 0.5 * overall + 0.5 * recent

        if mode == "hot":
            weights[n] = score ** 2
        elif mode == "cold":
            weights[n] = (1 / score) ** 2 if score else 1.0
        else:  # balanced: 편차를 완만하게만 반영
            weights[n] = score ** 0.5

    # 최소 가중치 보장 (0 확률 번호 방지)
    floor = max(weights.values()) * 0.05
    return {n: max(w, floor) for n, w in weights.items()}


# --------------------------------------------------------------------------
# 조합 생성
# --------------------------------------------------------------------------

def weighted_sample(weights: dict[int, float], rng: random.Random, k: int = PICK) -> list[int]:
    """복원 없이 가중 추출 (k개)."""
    pool = dict(weights)
    picked = []
    for _ in range(k):
        total = sum(pool.values())
        r = rng.uniform(0, total)
        upto = 0.0
        for n, w in pool.items():
            upto += w
            if upto >= r:
                picked.append(n)
                del pool[n]
                break
    return sorted(picked)


def max_consecutive(nums: list[int]) -> int:
    best = run = 1
    for prev, cur in zip(nums, nums[1:]):
        run = run + 1 if cur - prev == 1 else 1
        best = max(best, run)
    return best


def decade_spread(nums: list[int]) -> int:
    return len({min(n // 10, 4) for n in nums})


def passes_filters(nums: list[int]) -> bool:
    if not SUM_RANGE[0] <= sum(nums) <= SUM_RANGE[1]:
        return False
    odds = sum(1 for n in nums if n % 2)
    if not ODD_RANGE[0] <= odds <= ODD_RANGE[1]:
        return False
    if max_consecutive(nums) > MAX_CONSECUTIVE:
        return False
    if decade_spread(nums) < MIN_DECADE_SPREAD:
        return False
    return True


def recommend(
    weights: dict[int, float],
    count: int,
    past: set[tuple[int, ...]],
    rng: random.Random,
    fixed: tuple[int, ...] = (),
    use_filter: bool = True,
) -> list[list[int]]:
    """필터를 통과하고 서로 겹치지 않으며 과거 1등과 동일하지 않은 조합들.

    fixed: 모든 게임에 반드시 넣을 번호 (나머지 6-len(fixed)개만 가중 추출).
    제외수는 호출 전에 weights 에서 빼서 넘긴다.
    """
    pool = {n: w for n, w in weights.items() if n not in fixed}
    k = PICK - len(fixed)

    def draw() -> list[int]:
        return sorted([*fixed, *weighted_sample(pool, rng, k)])

    games: list[list[int]] = []
    seen: set[tuple[int, ...]] = set()
    attempts = 0
    max_attempts = count * 20000

    while len(games) < count and attempts < max_attempts:
        attempts += 1
        nums = draw()
        key = tuple(nums)
        if key in seen or key in past:
            continue
        if use_filter and not passes_filters(nums):
            continue
        seen.add(key)
        games.append(nums)

    # 필터가 너무 빡빡해 못 채웠다면 필터 없이 보충 (가능한 조합 수보다 많이 요청하면 있는 만큼만)
    attempts = 0
    while len(games) < count and attempts < max_attempts:
        attempts += 1
        nums = draw()
        key = tuple(nums)
        if key not in seen:
            seen.add(key)
            games.append(nums)

    return games


# --------------------------------------------------------------------------
# 출력
# --------------------------------------------------------------------------

def print_stats(draws: list[Draw]) -> None:
    if not draws:
        print("분석할 이력이 없습니다.")
        return

    freq = frequency(draws)
    expected = len(draws) * PICK / 45
    latest = max(draws, key=lambda d: d.round)

    print(f"\n[ 당첨 이력 통계 ]  1 ~ {latest.round}회차 (총 {len(draws)}회)")
    print(f"최근 회차: {latest.round}회  {latest.numbers} + 보너스 {latest.bonus}")
    print(f"번호당 기대 출현 횟수: {expected:.1f}회\n")

    hot = freq.most_common(10)
    cold = freq.most_common()[-10:]
    print("  많이 나온 번호:  " + ", ".join(f"{n}({c}회)" for n, c in hot))
    print("  적게 나온 번호:  " + ", ".join(f"{n}({c}회)" for n, c in reversed(cold)))

    print("\n  전체 출현 분포")
    peak = max(freq.values())
    for start in range(1, 46, 5):
        row = []
        for n in range(start, min(start + 5, 46)):
            bar = "█" * round(freq[n] / peak * 18)
            row.append(f"{n:2d} {freq[n]:4d} {bar:<18}")
        print("    " + " | ".join(row))

    # 카이제곱 적합도 검정: 번호가 균등하게 나오는지
    chi2 = sum((freq[n] - expected) ** 2 / expected for n in NUMBERS)
    print(f"\n  균등성 검정 (카이제곱, df=44): χ² = {chi2:.1f}  (기대값 44 ± 9.4)")
    if chi2 < 60.5:  # p=0.05 임계값
        print("  → 유의미한 편향 없음. 모든 번호가 통계적으로 동일한 확률입니다.")
    else:
        print("  → 관측된 편향이 우연 범위를 벗어납니다 (표본 수 확인 필요).")


def print_games(games: list[list[int]], draws: list[Draw], mode: str) -> None:
    freq = frequency(draws)
    mode_label = {
        "balanced": "균형 (빈도 완만 반영)",
        "hot": "핫넘버 (많이 나온 번호 위주)",
        "cold": "콜드넘버 (적게 나온 번호 위주)",
        "uniform": "완전 무작위 (균등 확률)",
    }[mode]

    print(f"\n[ 추천 번호 ]  모드: {mode_label}")
    print("-" * 62)
    for i, nums in enumerate(games, 1):
        body = "  ".join(f"{n:2d}" for n in nums)
        odds = sum(1 for n in nums if n % 2)
        print(f"  {chr(64 + i) if i <= 26 else i}게임   {body}")
        print(f"          합 {sum(nums):3d} · 홀{odds}:짝{6 - odds} · "
              f"구간 {decade_spread(nums)}개 · 누적출현 {sum(freq[n] for n in nums)}회")
    print("-" * 62)
    print(f"  1등 당첨 확률: 1 / {TOTAL_COMBINATIONS:,}  "
          f"({1 / TOTAL_COMBINATIONS * 100:.7f}%)")
    print(f"  {len(games)}게임 구매 시: 약 1 / {TOTAL_COMBINATIONS // len(games):,}")
    print("\n  ※ 로또 추첨은 매회 독립 사건입니다. 과거 빈도는 다음 회차 확률을")
    print("     바꾸지 않으며, 위 분석은 조합 선택의 참고 자료일 뿐입니다.")


# --------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="로또 6/45 번호 추천기",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-n", "--count", type=int, default=5, help="추천 게임 수 (기본 5)")
    parser.add_argument("-m", "--mode", default="balanced",
                        choices=["balanced", "hot", "cold", "uniform"],
                        help="추출 방식 (기본 balanced)")
    parser.add_argument("--stats", action="store_true", help="통계만 출력")
    parser.add_argument("--update", action="store_true", help="최신 회차까지 이력 갱신")
    parser.add_argument("--no-filter", action="store_true", help="통계 필터 해제")
    parser.add_argument("--seed", type=int, help="난수 시드 (재현용)")
    parser.add_argument("--insecure", action="store_true",
                        help="SSL 인증서 검증 생략 (사내망에서 검증이 막힐 때만)")
    args = parser.parse_args()

    if args.insecure:
        globals()["INSECURE"] = True
        print("주의: SSL 인증서 검증을 생략합니다.", file=sys.stderr)

    if args.count < 1:
        parser.error("게임 수는 1 이상이어야 합니다.")

    draws = ensure_history()
    if args.update:
        draws = update_history(draws)
        # 기존 이력이 있으면 아래의 "이력 없음" 안내가 뜨지 않으므로 여기서 실패를 알린다 (CI 가 감지하도록 종료 코드 1)
        if LAST_ERROR:
            print(f"이력 갱신 실패: {LAST_ERROR}", file=sys.stderr)
            return 1

    if not draws:
        print("당첨 이력을 가져오지 못했습니다. 균등 확률로 추천합니다.", file=sys.stderr)
        if LAST_ERROR:
            print(f"  사유: {LAST_ERROR}", file=sys.stderr)
        print(file=sys.stderr)

    if args.stats:
        print_stats(draws)
        return 0

    if args.no_filter:
        global SUM_RANGE, ODD_RANGE, MAX_CONSECUTIVE, MIN_DECADE_SPREAD
        SUM_RANGE, ODD_RANGE, MAX_CONSECUTIVE, MIN_DECADE_SPREAD = (0, 999), (0, 6), 6, 1

    rng = random.Random(args.seed) if args.seed is not None else random.SystemRandom()
    weights = build_weights(draws, args.mode)
    past = {tuple(d.numbers) for d in draws}

    print_stats(draws)
    print_games(recommend(weights, args.count, past, rng), draws, args.mode)
    return 0


if __name__ == "__main__":
    sys.exit(main())