"""로또 6/45 MCP 서버.

lottery.py 의 검증된 함수를 MCP 도구로 공개한다. AI 는 도구를 골라 호출만 하고,
번호 추출·통계 계산은 전부 lottery.py 가 한다 (AI 가 숫자를 지어내지 않게).

실행 (stdio):
    python mcp_server/lotto_mcp.py

stdout 은 MCP 프로토콜 전용이므로 이 파일과 lottery.py 는 stdout 에 print 하지 않는다
(lottery.py 의 진행 메시지는 stderr 로 나간다).
"""

from __future__ import annotations

import random
import sys
from pathlib import Path
from typing import Literal

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import lottery as lt  # noqa: E402
from mcp.server.fastmcp import FastMCP  # noqa: E402

DISCLAIMER = ("로또 추첨은 매회 독립 사건이다. 과거 빈도는 다음 회차 확률을 바꾸지 않으며, "
              "추천은 조합 선택의 참고 자료일 뿐 당첨 확률을 높이지 않는다.")
CHI2_CRITICAL_DF44 = 60.5
MAX_GAMES = 20

Mode = Literal["balanced", "hot", "cold", "uniform"]

server = FastMCP(
    "lotto",
    instructions=(
        "한국 로또 6/45 당첨 이력(동행복권) 조회·통계·번호 추천 도구. "
        "번호나 통계를 직접 만들지 말고 반드시 도구 결과를 근거로 답할 것. "
        "추천 결과를 전할 때는 disclaimer 내용을 함께 알릴 것."
    ),
)


# --------------------------------------------------------------------------
# 내부 헬퍼
# --------------------------------------------------------------------------

def _draws() -> list[lt.Draw]:
    draws = lt.load_cache()
    if not draws:
        raise ValueError("당첨 이력이 없습니다. update_history 도구를 먼저 실행하세요.")
    return sorted(draws, key=lambda d: d.round)


def _draw_dict(d: lt.Draw) -> dict:
    return {"round": d.round, "numbers": d.numbers, "bonus": d.bonus}


def _validate_numbers(nums: list[int], name: str) -> list[int]:
    if any(not isinstance(n, int) or not 1 <= n <= 45 for n in nums):
        raise ValueError(f"{name}: 번호는 1~45 정수여야 합니다. 받은 값: {nums}")
    if len(set(nums)) != len(nums):
        raise ValueError(f"{name}: 중복된 번호가 있습니다. 받은 값: {nums}")
    return sorted(nums)


def _filter_report(nums: list[int]) -> dict:
    """lottery.passes_filters 와 같은 기준으로, 어떤 규칙을 통과/실패했는지 풀어서 보여준다."""
    s, odd = sum(nums), sum(1 for n in nums if n % 2)
    checks = {
        f"합 {lt.SUM_RANGE[0]}~{lt.SUM_RANGE[1]}": lt.SUM_RANGE[0] <= s <= lt.SUM_RANGE[1],
        f"홀수 {lt.ODD_RANGE[0]}~{lt.ODD_RANGE[1]}개": lt.ODD_RANGE[0] <= odd <= lt.ODD_RANGE[1],
        f"연속 {lt.MAX_CONSECUTIVE}개 이하": lt.max_consecutive(nums) <= lt.MAX_CONSECUTIVE,
        f"구간 {lt.MIN_DECADE_SPREAD}곳 이상": lt.decade_spread(nums) >= lt.MIN_DECADE_SPREAD,
    }
    return {"passes": all(checks.values()), "rules": checks}


def _metrics(nums: list[int], freq) -> dict:
    odd = sum(1 for n in nums if n % 2)
    return {
        "sum": sum(nums),
        "odd_even": f"{odd}:{lt.PICK - odd}",
        "decade_spread": lt.decade_spread(nums),
        "max_consecutive": lt.max_consecutive(nums),
        "cumulative_appearances": sum(freq[n] for n in nums),
    }


# --------------------------------------------------------------------------
# 도구
# --------------------------------------------------------------------------

@server.tool()
def get_latest_draw() -> dict:
    """가장 최근 회차의 당첨 번호와 보유 이력 범위를 반환한다."""
    draws = _draws()
    return {**_draw_dict(draws[-1]), "history_range": f"1~{draws[-1].round}회", "total_draws": len(draws)}


@server.tool()
def get_draw(round_no: int) -> dict:
    """특정 회차의 당첨 번호 6개와 보너스 번호를 반환한다."""
    for d in _draws():
        if d.round == round_no:
            return _draw_dict(d)
    raise ValueError(f"{round_no}회차 기록이 없습니다. 최신 회차가 아니라면 update_history 를 실행하세요.")


@server.tool()
def get_statistics(last_n: int | None = None) -> dict:
    """번호별 출현 통계. last_n 을 주면 최근 N회만 분석한다 (없으면 전체).

    반환: 번호별 출현 횟수, 많이/적게 나온 TOP 10, 번호당 기대 출현 횟수,
    카이제곱 균등성 검정, 당첨 조합 평균 합·홀수 개수, 번호 구간별 출현.
    """
    draws = _draws()
    if last_n is not None:
        if last_n < 1:
            raise ValueError("last_n 은 1 이상이어야 합니다.")
        draws = draws[-last_n:]

    freq = lt.frequency(draws)
    expected = len(draws) * lt.PICK / 45
    chi2 = sum((freq[n] - expected) ** 2 / expected for n in lt.NUMBERS)
    ranked = sorted(lt.NUMBERS, key=lambda n: (-freq[n], n))
    groups = [(1, 10), (11, 20), (21, 30), (31, 40), (41, 45)]

    return {
        "rounds": f"{draws[0].round}~{draws[-1].round}회 ({len(draws)}회)",
        "expected_per_number": round(expected, 2),
        "frequency": {n: freq[n] for n in lt.NUMBERS},
        "most_frequent": [{"number": n, "count": freq[n]} for n in ranked[:10]],
        "least_frequent": [{"number": n, "count": freq[n]} for n in reversed(ranked[-10:])],
        "chi_square": {
            "value": round(chi2, 2), "df": 44, "critical_0_05": CHI2_CRITICAL_DF44,
            "verdict": "편향 없음 (우연 범위)" if chi2 < CHI2_CRITICAL_DF44 else "편향 의심 (표본 크기 확인 필요)",
        },
        "winning_combo_avg": {
            "sum": round(sum(sum(d.numbers) for d in draws) / len(draws), 1),
            "odd_count": round(sum(sum(n % 2 for n in d.numbers) for d in draws) / len(draws), 2),
        },
        "by_range": [
            {"range": f"{a}-{b}", "total": sum(freq[n] for n in range(a, b + 1)),
             "per_number": round(sum(freq[n] for n in range(a, b + 1)) / (b - a + 1), 1)}
            for a, b in groups
        ],
    }


@server.tool()
def recommend_numbers(
    count: int = 5,
    mode: Mode = "balanced",
    include: list[int] | None = None,
    exclude: list[int] | None = None,
    use_filter: bool = True,
) -> dict:
    """당첨 이력 기반 가중 추출로 추천 조합을 만든다.

    count: 게임 수 (1~20)
    mode: balanced(빈도 완만 반영) | hot(많이 나온 번호 위주) | cold(적게 나온 번호 위주) | uniform(완전 무작위)
    include: 모든 게임에 반드시 넣을 번호 (최대 5개)
    exclude: 절대 넣지 않을 번호
    use_filter: 통계 필터(합 100~175, 홀수 2~4개, 연속 2개 이하, 구간 3곳 이상) 적용 여부
    과거 1등 조합과 같은 조합, 게임끼리 중복되는 조합은 나오지 않는다.
    """
    include = _validate_numbers(include or [], "include")
    exclude = _validate_numbers(exclude or [], "exclude")
    if not 1 <= count <= MAX_GAMES:
        raise ValueError(f"count 는 1~{MAX_GAMES} 사이여야 합니다.")
    if len(include) > lt.PICK - 1:
        raise ValueError("include 는 최대 5개까지입니다.")
    if set(include) & set(exclude):
        raise ValueError(f"include 와 exclude 에 같은 번호가 있습니다: {sorted(set(include) & set(exclude))}")
    if 45 - len(exclude) - len(include) < lt.PICK - len(include):
        raise ValueError("exclude 가 너무 많아 6개를 채울 수 없습니다.")

    draws = _draws()
    weights = {n: w for n, w in lt.build_weights(draws, mode).items() if n not in exclude}
    past = {tuple(d.numbers) for d in draws}
    games = lt.recommend(weights, count, past, random.SystemRandom(),
                         fixed=tuple(include), use_filter=use_filter)
    freq = lt.frequency(draws)

    return {
        "mode": mode,
        "based_on": f"1~{draws[-1].round}회 당첨 이력",
        "for_round": draws[-1].round + 1,
        "games": [{"game": chr(65 + i), "numbers": g, **_metrics(g, freq),
                   "passes_filter": lt.passes_filters(g)} for i, g in enumerate(games)],
        "note": None if len(games) == count else f"조건을 만족하는 조합이 {len(games)}개뿐입니다.",
        "jackpot_odds": f"1 / {lt.TOTAL_COMBINATIONS:,} (게임당)",
        "disclaimer": DISCLAIMER,
    }


@server.tool()
def analyze_numbers(numbers: list[int]) -> dict:
    """사용자가 고른 6개 번호를 분석한다: 합·홀짝·구간·연속, 통계 필터 통과 여부(규칙별),
    누적 출현, 과거 당첨 번호와 가장 많이 겹친 회차들과 등수별 적중 횟수."""
    nums = _validate_numbers(numbers, "numbers")
    if len(nums) != lt.PICK:
        raise ValueError(f"번호는 정확히 6개여야 합니다. 받은 개수: {len(nums)}")

    draws = _draws()
    chosen = set(nums)
    hits = {"1등(6개)": 0, "2등(5개+보너스)": 0, "3등(5개)": 0, "4등(4개)": 0, "5등(3개)": 0}
    best: list[dict] = []
    best_match = 0
    for d in draws:
        m = len(chosen & set(d.numbers))
        bonus = d.bonus in chosen
        if m == 6:
            hits["1등(6개)"] += 1
        elif m == 5 and bonus:
            hits["2등(5개+보너스)"] += 1
        elif m == 5:
            hits["3등(5개)"] += 1
        elif m == 4:
            hits["4등(4개)"] += 1
        elif m == 3:
            hits["5등(3개)"] += 1
        if m > best_match:
            best_match, best = m, []
        if m == best_match:
            best.append({"round": d.round, "numbers": d.numbers, "matched": sorted(chosen & set(d.numbers))})

    return {
        "numbers": nums,
        **_metrics(nums, lt.frequency(draws)),
        "filter": _filter_report(nums),
        "past_results_if_played_every_round": hits,
        "best_match": {"count": best_match, "rounds": best[-5:], "total_rounds_with_best": len(best)},
        "disclaimer": DISCLAIMER,
    }


@server.tool()
def update_history() -> dict:
    """동행복권에서 새 회차를 받아 lotto_history.json 을 갱신한다 (네트워크 사용, 새 회차가 없으면 변화 없음)."""
    before = lt.load_cache()
    after = lt.update_history(list(before), quiet=True)
    if lt.LAST_ERROR:
        raise RuntimeError(f"갱신 실패: {lt.LAST_ERROR}")
    latest = max(after, key=lambda d: d.round)
    return {"added": len(after) - len(before), "latest": _draw_dict(latest), "total_draws": len(after)}


if __name__ == "__main__":
    server.run()
