// 대시보드의 작은 카드들: 요약 타일, 순위 목록, 구간별 출현, 최근 당첨 번호.

function SummaryTiles({ draws, stats }) {
  const first = draws[0].round, last = draws[draws.length - 1].round;
  return (
    <div className="tiles">
      <div className="panel tile">
        <span className="eyebrow">분석 회차</span>
        <span className="v num">{fmt(draws.length)}회</span>
        <span className="s">{first}–{last}회</span>
      </div>
      <div className="panel tile">
        <span className="eyebrow">번호당 기대 출현</span>
        <span className="v num">{stats.expected.toFixed(1)}회</span>
        <span className="s">회차 수 × 6 ÷ 45</span>
      </div>
      <div className="panel tile">
        <span className="eyebrow">당첨 조합 평균</span>
        <span className="v num">합 {stats.avgSum.toFixed(0)}</span>
        <span className="s">홀수 평균 {stats.avgOdd.toFixed(2)}개 · 필터 통과 {stats.filterPassRate.toFixed(0)}%</span>
      </div>
      <div className="panel tile">
        <span className="eyebrow">균등성 검정 (χ², df=44)</span>
        <span className="v num">{stats.chi2.toFixed(1)}</span>
        <span className={`pill ${stats.uniform ? "good" : "warn"}`}>{stats.uniform ? "편향 없음" : "편향 의심"}</span>
      </div>
    </div>
  );
}

function RankList({ title, items, max }) {
  return (
    <div className="card panel">
      <h3>{title}</h3>
      <ol className="rank">
        {items.map(([n, c]) => (
          <li key={n}>
            <Ball n={n} size="sm" />
            <div className="bar-track"><div className="bar-fill" style={{ width: `${(c / max) * 100}%`, "--c": ballColor(n) }} /></div>
            <span className="cnt num">{fmt(c)}회</span>
          </li>
        ))}
      </ol>
    </div>
  );
}

function GroupBreakdown({ groups, uniform }) {
  const max = Math.max(...groups.map(g => g.perNumber));
  return (
    <div className="card panel">
      <h3>구간별 출현 (번호 1개당 평균)</h3>
      <div className="groups">
        {groups.map((g, i) => (
          <div className="group" key={g.label}>
            <span className="num">{g.label}</span>
            <div className="bar-track"><div className="bar-fill" style={{ width: `${(g.perNumber / max) * 100}%`, "--c": GROUP_COLORS[i] }} /></div>
            <span className="cnt num">{g.perNumber.toFixed(1)}회 · 계 {fmt(g.count)}</span>
          </div>
        ))}
      </div>
      <p className="note">
        {uniform
          ? `χ² 값이 임계값 ${CHI2_CRITICAL_DF44}보다 작아, 번호별 출현 차이는 우연히 생길 수 있는 범위입니다.`
          : `χ² 값이 임계값 ${CHI2_CRITICAL_DF44}를 넘습니다. 분석 기간이 짧으면 이런 편차가 쉽게 생깁니다.`}
      </p>
    </div>
  );
}

function RecentDraws({ draws, limit = 8 }) {
  const recent = draws.slice(-limit).reverse();
  return (
    <div className="card panel">
      <h3>최근 당첨 번호</h3>
      <div className="draws">
        {recent.map(d => (
          <div className="draw" key={d.round}>
            <span className="r num">{d.round}회</span>
            <DrawBalls draw={d} size="xs" />
          </div>
        ))}
      </div>
    </div>
  );
}
