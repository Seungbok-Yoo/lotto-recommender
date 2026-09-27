"""MCP 서버 테스트. 네트워크를 쓰지 않는다 (update_history 제외).

    python -m unittest discover -s mcp_server -v
"""

from __future__ import annotations

import asyncio
import json
import random
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import lotto_mcp as srv  # noqa: E402
from lotto_mcp import lt  # noqa: E402


class RecommendCoreTest(unittest.TestCase):
    """lottery.recommend 에 추가한 fixed / use_filter 인자."""

    def setUp(self):
        self.rng = random.Random(42)
        self.weights = {n: 1.0 for n in lt.NUMBERS}

    def test_default_behavior_unchanged(self):
        games = lt.recommend(self.weights, 5, set(), self.rng)
        self.assertEqual(len(games), 5)
        self.assertTrue(all(lt.passes_filters(g) for g in games))

    def test_fixed_numbers_in_every_game(self):
        games = lt.recommend(self.weights, 10, set(), self.rng, fixed=(7, 33))
        self.assertTrue(all({7, 33} <= set(g) and len(set(g)) == 6 for g in games))

    def test_use_filter_false_allows_any(self):
        w = {n: (1e9 if n <= 6 else 1e-9) for n in lt.NUMBERS}
        self.assertEqual(lt.recommend(w, 1, set(), self.rng, use_filter=False), [[1, 2, 3, 4, 5, 6]])

    def test_impossible_count_terminates(self):
        # 고정 5개 + 후보 2개 → 가능한 조합 2개뿐. 무한 루프 없이 있는 만큼만.
        w = {n: 1.0 for n in (1, 2, 3, 4, 5, 6, 7)}
        games = lt.recommend(w, 5, set(), self.rng, fixed=(1, 2, 3, 4, 5), use_filter=False)
        self.assertEqual(sorted(games), [[1, 2, 3, 4, 5, 6], [1, 2, 3, 4, 5, 7]])


class ToolTest(unittest.TestCase):
    """도구 함수를 직접 호출 (실제 lotto_history.json 사용)."""

    def test_latest_and_get_draw(self):
        latest = srv.get_latest_draw()
        self.assertEqual(srv.get_draw(latest["round"])["numbers"], latest["numbers"])
        self.assertEqual(srv.get_draw(1), {"round": 1, "numbers": [10, 23, 29, 33, 37, 40], "bonus": 16})
        with self.assertRaises(ValueError):
            srv.get_draw(999999)

    def test_statistics(self):
        s = srv.get_statistics()
        self.assertEqual(sum(s["frequency"].values()), srv.get_latest_draw()["total_draws"] * 6)
        self.assertEqual(len(s["most_frequent"]), 10)
        recent = srv.get_statistics(last_n=100)
        self.assertEqual(sum(recent["frequency"].values()), 600)

    def test_recommend_include_exclude(self):
        r = srv.recommend_numbers(count=8, include=[7], exclude=[1, 2, 3], mode="hot")
        self.assertEqual(len(r["games"]), 8)
        for g in r["games"]:
            self.assertIn(7, g["numbers"])
            self.assertFalse({1, 2, 3} & set(g["numbers"]))
            self.assertTrue(g["passes_filter"])
        self.assertIn("disclaimer", r)

    def test_recommend_validation(self):
        for kwargs in [dict(count=0), dict(count=21), dict(include=[1, 2, 3, 4, 5, 6]),
                       dict(include=[5], exclude=[5]), dict(include=[46]), dict(exclude=[3, 3])]:
            with self.subTest(**kwargs), self.assertRaises(ValueError):
                srv.recommend_numbers(**kwargs)

    def test_analyze_numbers(self):
        first = srv.get_draw(1)["numbers"]
        a = srv.analyze_numbers(first)
        self.assertGreaterEqual(a["past_results_if_played_every_round"]["1등(6개)"], 1)
        self.assertEqual(a["best_match"]["count"], 6)
        bad = srv.analyze_numbers([1, 2, 3, 4, 5, 6])
        self.assertFalse(bad["filter"]["passes"])
        with self.assertRaises(ValueError):
            srv.analyze_numbers([1, 2, 3])


class ProtocolTest(unittest.TestCase):
    """실제 MCP 클라이언트로 서버를 stdio 로 띄워 호출한다 (Claude 가 연결하는 방식과 동일)."""

    def test_list_and_call_tools(self):
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        async def run():
            params = StdioServerParameters(command=sys.executable, args=[str(HERE / "lotto_mcp.py")])
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    tools = {t.name for t in (await session.list_tools()).tools}
                    result = await session.call_tool("recommend_numbers", {"count": 3, "include": [45]})
                    return tools, result

        tools, result = asyncio.run(run())
        self.assertEqual(tools, {"get_latest_draw", "get_draw", "get_statistics",
                                 "recommend_numbers", "analyze_numbers", "update_history"})
        self.assertFalse(result.isError)
        payload = result.structuredContent or json.loads(result.content[0].text)
        payload = payload.get("result", payload)
        self.assertEqual(len(payload["games"]), 3)
        self.assertTrue(all(45 in g["numbers"] for g in payload["games"]))


if __name__ == "__main__":
    unittest.main()
