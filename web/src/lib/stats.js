// 대시보드 통계 계산 — 화면 표시와 분리된 순수 함수. lotto.js 의 함수에 의존한다.

const CHI2_CRITICAL_DF44 = 60.5; // 자유도 44, 유의수준 0.05 임계값

/** 번호 구간 (동행복권 공 색상 기준). */
const NUMBER_GROUPS = [
  { label: "1–10", from: 1, to: 10 },
  { label: "11–20", from: 11, to: 20 },
  { label: "21–30", from: 21, to: 30 },
  { label: "31–40", from: 31, to: 40 },
  { label: "41–45", from: 41, to: 45 },
];

/** 번호가 속한 구간 인덱스 (0~4). */
const groupIndex = n => NUMBER_GROUPS.findIndex(g => n >= g.from && n <= g.to);

/** 최근 size 회차만 남긴다. size 가 Infinity 면 전체. */
function recentDraws(draws, size) {
  return size === Infinity ? draws : draws.slice(-size);
}

/** 카이제곱 적합도: 번호가 균등하게 나오는지. */
function chiSquare(freq, expected) {
  return NUMBERS.reduce((a, n) => a + (freq[n] - expected) ** 2 / expected, 0);
}

/** [번호, 횟수] 를 많이 나온 순으로 (동률이면 작은 번호 먼저). */
function rankByCount(freq) {
  return NUMBERS.map(n => [n, freq[n]]).sort((a, b) => b[1] - a[1] || a[0] - b[0]);
}

/** 대시보드에 필요한 수치를 한 번에 계산한다. */
function summarize(draws) {
  const freq = frequency(draws);
  const expected = draws.length * PICK / 45;
  const chi2 = chiSquare(freq, expected);
  const ranked = rankByCount(freq);

  const groups = NUMBER_GROUPS.map(g => {
    let count = 0;
    for (let n = g.from; n <= g.to; n++) count += freq[n];
    return { ...g, count, perNumber: count / (g.to - g.from + 1) };
  });

  return {
    freq,
    expected,
    chi2,
    uniform: chi2 < CHI2_CRITICAL_DF44,
    hot: ranked.slice(0, 10),
    cold: ranked.slice(-10).reverse(),
    maxCount: ranked[0][1],
    avgSum: draws.reduce((a, d) => a + sum(d.numbers), 0) / draws.length,
    avgOdd: draws.reduce((a, d) => a + oddCount(d.numbers), 0) / draws.length,
    filterPassRate: draws.filter(d => passesFilters(d.numbers)).length / draws.length * 100,
    groups,
  };
}

/** 차트 눈금: max 를 덮는 보기 좋은 간격과 상한. */
function niceScale(max, ticks = 4) {
  const raw = max / ticks;
  const mag = 10 ** Math.floor(Math.log10(raw));
  const step = [1, 2, 2.5, 5, 10].find(m => m * mag >= raw) * mag;
  return { step, top: Math.ceil(max / step) * step };
}
