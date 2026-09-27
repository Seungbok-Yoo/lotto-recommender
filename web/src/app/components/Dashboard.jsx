// 통계 대시보드: 분석 기간을 고르면 lib/stats.js 로 수치를 계산해 카드들에 나눠 준다.
function Dashboard({ draws }) {
  const [period, setPeriod] = useState("all");
  const size = PERIODS.find(p => p.id === period).size;
  const scoped = useMemo(() => recentDraws(draws, size), [draws, size]);
  const stats = useMemo(() => summarize(scoped), [scoped]);

  return (
    <section className="dash" aria-label="당첨 통계 대시보드">
      <div className="dash-head">
        <div>
          <div className="eyebrow">DASHBOARD</div>
          <h2>당첨 통계</h2>
        </div>
        <div className="seg" role="group" aria-label="분석 기간">
          {PERIODS.map(p => (
            <button key={p.id} id={`period-${p.id}`} aria-pressed={period === p.id}
                    onClick={() => setPeriod(p.id)}>{p.label}</button>
          ))}
        </div>
      </div>

      <SummaryTiles draws={scoped} stats={stats} />
      <DistributionChart freq={stats.freq} expected={stats.expected} />

      <div className="two">
        <RankList title="많이 나온 번호 TOP 10" items={stats.hot} max={stats.maxCount} />
        <RankList title="적게 나온 번호 TOP 10" items={stats.cold} max={stats.maxCount} />
      </div>

      <div className="two">
        <GroupBreakdown groups={stats.groups} uniform={stats.uniform} />
        <RecentDraws draws={draws} />
      </div>
    </section>
  );
}
