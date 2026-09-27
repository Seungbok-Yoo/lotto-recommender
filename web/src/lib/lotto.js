// 번호 추천 로직 — lottery.py 의 build_weights / weighted_sample / passes_filters / recommend 이식.
// React·DOM 에 의존하지 않는 순수 함수만 둔다 (tests/ 에서 단독으로 불러 검증).

const PICK = 6;
const TOTAL_COMBINATIONS = 8145060; // C(45, 6)
const NUMBERS = Array.from({ length: 45 }, (_, i) => i + 1);

// 통계 필터 기준 (실제 당첨 조합의 대부분이 이 범위에 들어온다)
const FILTER = { sum: [100, 175], odd: [2, 4], maxConsecutive: 2, minDecades: 3 };

/** [회차, 번호1..6, 보너스] 배열을 Draw 객체로 바꾼다. */
function toDraws(rows) {
  return rows.map(r => ({ round: r[0], numbers: r.slice(1, 7), bonus: r[7] }));
}

/** 번호별 출현 횟수. 인덱스 = 번호 (0은 사용하지 않음). */
function frequency(draws) {
  const f = Array(46).fill(0);
  for (const d of draws) for (const n of d.numbers) f[n]++;
  return f;
}

/** 최근 회차일수록 크게 치는 지수 감쇠 가중치. */
function recencyWeights(draws, halfLife = 150) {
  const w = Array(46).fill(0);
  if (!draws.length) return w;
  const latest = Math.max(...draws.map(d => d.round));
  for (const d of draws) {
    const k = 0.5 ** ((latest - d.round) / halfLife);
    for (const n of d.numbers) w[n] += k;
  }
  return w;
}

/** 추출 가중치 { 번호: 가중치 }. 전부 양수로 만들어 어떤 번호도 배제되지 않게 한다. */
function buildWeights(draws, mode) {
  const weights = {};
  if (mode === "uniform" || !draws.length) {
    for (const n of NUMBERS) weights[n] = 1;
    return weights;
  }
  const freq = frequency(draws);
  const rec = recencyWeights(draws);
  const expected = draws.length * PICK / 45;
  const recSum = rec.reduce((a, b) => a + b, 0);

  for (const n of NUMBERS) {
    // 전체 빈도와 최근 흐름을 반반 섞어 기대치 대비 비율로 환산
    const overall = expected ? freq[n] / expected : 1;
    const recent = recSum ? rec[n] / (recSum / 45) : 1;
    const score = 0.5 * overall + 0.5 * recent;
    if (mode === "hot") weights[n] = score ** 2;
    else if (mode === "cold") weights[n] = score ? (1 / score) ** 2 : 1;
    else weights[n] = score ** 0.5; // balanced: 편차를 완만하게만 반영
  }
  // 최소 가중치 보장 (0 확률 번호 방지)
  const floor = Math.max(...Object.values(weights)) * 0.05;
  for (const n of NUMBERS) weights[n] = Math.max(weights[n], floor);
  return weights;
}

/** [0, 1) 난수. 브라우저의 암호학적 난수 생성기를 쓴다 (Python SystemRandom 대응). */
function cryptoRandom() {
  const a = new Uint32Array(1);
  crypto.getRandomValues(a);
  return a[0] / 2 ** 32;
}

/** 복원 없이 가중 추출한 6개 번호 (오름차순). */
function weightedSample(weights, rng = cryptoRandom) {
  const pool = new Map(Object.entries(weights).map(([n, w]) => [Number(n), w]));
  const picked = [];
  for (let i = 0; i < PICK; i++) {
    let total = 0;
    for (const w of pool.values()) total += w;
    const r = rng() * total;
    let upto = 0;
    for (const [n, w] of pool) {
      upto += w;
      if (upto >= r) { picked.push(n); pool.delete(n); break; }
    }
  }
  return picked.sort((a, b) => a - b);
}

const sum = nums => nums.reduce((a, b) => a + b, 0);
const oddCount = nums => nums.filter(n => n % 2).length;
/** 1~9, 10번대, 20번대, 30번대, 40번대 중 몇 구간에 걸쳐 있는지. */
const decadeSpread = nums => new Set(nums.map(n => Math.min(Math.floor(n / 10), 4))).size;

function maxConsecutive(nums) {
  let best = 1, run = 1;
  for (let i = 1; i < nums.length; i++) {
    run = nums[i] - nums[i - 1] === 1 ? run + 1 : 1;
    best = Math.max(best, run);
  }
  return best;
}

function passesFilters(nums) {
  const s = sum(nums), o = oddCount(nums);
  return s >= FILTER.sum[0] && s <= FILTER.sum[1]
    && o >= FILTER.odd[0] && o <= FILTER.odd[1]
    && maxConsecutive(nums) <= FILTER.maxConsecutive
    && decadeSpread(nums) >= FILTER.minDecades;
}

/**
 * 필터를 통과하고 서로 겹치지 않으며 과거 1등과 동일하지 않은 조합 count 개.
 * past: "1,2,3,4,5,6" 형식 키의 Set.
 */
function recommend(weights, count, past, useFilter = true, rng = cryptoRandom) {
  const games = [], seen = new Set();
  let attempts = 0;
  while (games.length < count && attempts < count * 20000) {
    attempts++;
    const nums = weightedSample(weights, rng);
    const key = nums.join(",");
    if (seen.has(key) || past.has(key)) continue;
    if (useFilter && !passesFilters(nums)) continue;
    seen.add(key);
    games.push(nums);
  }
  // 필터가 너무 빡빡해 못 채웠다면 필터 없이 보충
  while (games.length < count) {
    const nums = weightedSample(weights, rng);
    const key = nums.join(",");
    if (!seen.has(key)) { seen.add(key); games.push(nums); }
  }
  return games;
}

const pastKeys = draws => new Set(draws.map(d => d.numbers.join(",")));
