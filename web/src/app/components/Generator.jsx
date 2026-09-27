// 번호 발급 영역: 조건 상태를 들고, 버튼을 누르면 lib/lotto.js 로 조합을 만든다.
function Generator({ draws, allFreq, nextRound }) {
  const [mode, setMode] = useState("balanced");
  const [count, setCount] = useState(5);
  const [useFilter, setUseFilter] = useState(true);
  const [result, setResult] = useState(null); // { games, mode }
  const [issueNo, setIssueNo] = useState(0);  // 재발급 시 애니메이션을 다시 돌리기 위한 키

  const past = useMemo(() => pastKeys(draws), [draws]);

  function issue() {
    const weights = buildWeights(draws, mode);
    setResult({ games: recommend(weights, count, past, useFilter), mode });
    setIssueNo(k => k + 1);
  }

  const modeTitle = result && MODES.find(m => m.id === result.mode).title;

  return (
    <section className="panel gen" aria-label="번호 발급">
      <GeneratorControls
        mode={mode} onMode={setMode}
        count={count} onCount={c => setCount(Math.min(MAX_GAMES, Math.max(1, c)))}
        useFilter={useFilter} onUseFilter={setUseFilter}
        onIssue={issue} issued={!!result}
      />
      <GameSlip
        key={issueNo}
        games={result && result.games} count={count} modeTitle={modeTitle}
        nextRound={nextRound} allFreq={allFreq} issueNo={issueNo}
      />
    </section>
  );
}
