// 최상위 화면: 헤더 + 번호 발급 + 대시보드.
function App({ draws }) {
  const latest = draws[draws.length - 1];
  const allFreq = useMemo(() => frequency(draws), [draws]);
  return (
    <main className="wrap">
      <header className="top">
        <div>
          <h1>로또 <span className="hl">6/45</span> 번호 발급기</h1>
          <p>1–{latest.round}회 당첨 이력 {fmt(draws.length)}건을 분석해 추천 조합을 만듭니다.</p>
        </div>
        <div className="latest">
          <span className="label">최근 {latest.round}회</span>
          <DrawBalls draw={latest} size="sm" />
        </div>
      </header>
      <Generator draws={draws} allFreq={allFreq} nextRound={latest.round + 1} />
      <Dashboard draws={draws} />
    </main>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App draws={DRAWS} />);
