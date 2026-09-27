// lib/lotto.js, lib/stats.js 단위 테스트. runner.html 이 test/eq/ok 를 제공한다.

// 재현 가능한 시드 난수 (mulberry32)
function seeded(seed) {
  return function () {
    seed |= 0; seed = (seed + 0x6D2B79F5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** 번호 nums 에 큰 가중치, 나머지는 거의 0. */
function forced(nums) {
  const w = {};
  for (const n of NUMBERS) w[n] = nums.includes(n) ? 1e9 : 1e-9;
  return w;
}

const SAMPLE = toDraws([
  [1, 10, 23, 29, 33, 37, 40, 16],
  [2, 9, 13, 21, 25, 32, 42, 2],
  [3, 11, 16, 19, 21, 27, 31, 30],
  [4, 14, 27, 30, 31, 40, 42, 2],
]);

test("toDraws: 행을 회차·번호·보너스로 나눈다", () => {
  eq(SAMPLE[0], { round: 1, numbers: [10, 23, 29, 33, 37, 40], bonus: 16 });
});

test("frequency: 번호별 출현 횟수 (보너스 제외)", () => {
  const f = frequency(SAMPLE);
  eq([f[21], f[27], f[31], f[42], f[2], f[16]], [2, 2, 2, 2, 0, 1]);
  eq(f.reduce((a, b) => a + b, 0), 24);
});

test("buildWeights: uniform 이면 모두 1", () => {
  const w = buildWeights(SAMPLE, "uniform");
  ok(NUMBERS.every(n => w[n] === 1));
});

test("buildWeights: hot 은 많이 나온 번호, cold 는 적게 나온 번호에 큰 가중치", () => {
  const hot = buildWeights(SAMPLE, "hot");
  const cold = buildWeights(SAMPLE, "cold");
  ok(hot[42] > hot[1], "hot: 42(2회) > 1(0회)");
  ok(cold[1] > cold[42], "cold: 1(0회) > 42(2회)");
});

test("buildWeights: 모든 가중치가 양수이고 최대값의 5% 이상", () => {
  for (const mode of ["balanced", "hot", "cold"]) {
    const w = buildWeights(SAMPLE, mode);
    const max = Math.max(...Object.values(w));
    ok(NUMBERS.every(n => w[n] > 0 && w[n] >= max * 0.05 - 1e-12), mode);
  }
});

test("weightedSample: 1~45 사이 서로 다른 6개, 오름차순", () => {
  const rng = seeded(1);
  const w = buildWeights(SAMPLE, "balanced");
  for (let i = 0; i < 500; i++) {
    const s = weightedSample(w, rng);
    ok(s.length === 6 && new Set(s).size === 6, "6개 중복 없음");
    ok(s.every(n => n >= 1 && n <= 45), "범위");
    ok(s.every((n, j) => j === 0 || s[j - 1] < n), "오름차순");
  }
});

test("weightedSample: 가중치가 몰린 번호를 뽑는다", () => {
  eq(weightedSample(forced([5, 12, 19, 26, 33, 40]), seeded(2)), [5, 12, 19, 26, 33, 40]);
});

test("maxConsecutive / decadeSpread", () => {
  eq(maxConsecutive([1, 2, 3, 10, 11, 20]), 3);
  eq(maxConsecutive([1, 3, 5, 7, 9, 11]), 1);
  eq(decadeSpread([1, 9, 10, 40, 41, 45]), 3);
  eq(decadeSpread([3, 14, 22, 31, 38, 43]), 5);
});

test("passesFilters: 기준 안/밖 조합", () => {
  ok(passesFilters([3, 14, 22, 31, 38, 43]), "합 151, 홀3, 연속1, 구간5");
  ok(!passesFilters([1, 2, 3, 4, 5, 6]), "합 21 — 범위 밖");
  ok(!passesFilters([11, 13, 15, 17, 29, 31]), "홀수 6개");
  ok(!passesFilters([20, 21, 22, 30, 35, 40]), "3연속");
});

test("recommend: 요청 수만큼, 중복 없이, 필터 통과", () => {
  const games = recommend(buildWeights(SAMPLE, "balanced"), 10, new Set(), true, seeded(3));
  eq(games.length, 10);
  eq(new Set(games.map(g => g.join(","))).size, 10);
  ok(games.every(passesFilters));
});

test("recommend: 과거 1등 조합은 제외한다", () => {
  // 1~7 에서만 뽑히게 하면 가능한 조합은 7개. 그중 하나를 과거 당첨으로 둔다.
  const past = new Set(["1,2,3,4,5,6"]);
  const games = recommend(forced([1, 2, 3, 4, 5, 6, 7]), 6, past, false, seeded(4));
  eq(games.length, 6);
  ok(!games.some(g => g.join(",") === "1,2,3,4,5,6"));
});

test("recommend: 필터를 만족할 수 없으면 필터 없이 채운다", () => {
  const games = recommend(forced([1, 2, 3, 4, 5, 6]), 1, new Set(), true, seeded(5));
  eq(games, [[1, 2, 3, 4, 5, 6]]);
});

test("stats: chiSquare 는 완전 균등이면 0", () => {
  const f = Array(46).fill(10);
  eq(chiSquare(f, 10), 0);
});

test("stats: rankByCount 는 횟수 내림차순, 동률이면 작은 번호 먼저", () => {
  const top = rankByCount(frequency(SAMPLE)).slice(0, 4).map(([n]) => n);
  eq(top, [21, 27, 31, 40]);
});

test("stats: recentDraws / summarize", () => {
  eq(recentDraws(SAMPLE, 2).map(d => d.round), [3, 4]);
  eq(recentDraws(SAMPLE, Infinity).length, 4);
  const s = summarize(SAMPLE);
  eq(s.expected, 4 * 6 / 45);
  eq(s.groups.reduce((a, g) => a + g.count, 0), 24);
  eq(s.hot.length, 10);
});

test("stats: niceScale 은 max 를 덮는 보기 좋은 눈금", () => {
  eq(niceScale(195.3), { step: 50, top: 200 });
  eq(niceScale(38), { step: 10, top: 40 });
});
