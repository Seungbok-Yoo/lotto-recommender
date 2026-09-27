// 발급 결과 용지: 게임별 번호와 지표, 복사 버튼, 당첨 확률 안내.
// games 가 null 이면 빈 공 자리를 count 줄 보여준다.
function GameSlip({ games, count, modeTitle, nextRound, allFreq, issueNo }) {
  const [copied, setCopied] = useState(false);
  const rows = games || Array.from({ length: count }, () => null);
  const n = rows.length;

  async function copy() {
    const text = games.map((g, i) => `${gameLabel(i)}  ${g.join(" ")}`).join("\n");
    try { await navigator.clipboard.writeText(text); setCopied(true); }
    catch { setCopied(false); }
  }

  return (
    <div className="slip">
      <div className="slip-head">
        <h2>{games ? `추천 번호 · ${modeTitle}` : `${nextRound}회차 추천 번호`}</h2>
        {games && (
          <button id="copy" className="ghost" onClick={copy}>{copied ? "복사됨" : "번호 복사"}</button>
        )}
      </div>

      <div className="games">
        {rows.map((g, i) => (
          <GameRow key={`${issueNo}-${i}`} index={i} nums={g} allFreq={allFreq} />
        ))}
      </div>

      <div className="odds">
        <span>1등 당첨 확률 <strong className="num">1 / {fmt(TOTAL_COMBINATIONS)}</strong>
          {" "}· {n}게임 구매 시 약 <strong className="num">1 / {fmt(Math.floor(TOTAL_COMBINATIONS / n))}</strong></span>
        <span>로또 추첨은 매회 독립 사건입니다. 과거 빈도는 다음 회차 확률을 바꾸지 않으며, 이 분석은 조합을 고를 때 참고하는 자료입니다.</span>
      </div>
    </div>
  );
}

function GameRow({ index, nums, allFreq }) {
  return (
    <div className="game">
      <span className="tag">{gameLabel(index)}</span>
      <div className="balls">
        {nums ? nums.map((num, j) => <Ball key={num} n={num} pop delay={index * 60 + j * 70} />)
              : Array.from({ length: PICK }, (_, j) => <EmptyBall key={j} />)}
      </div>
      <div className="meta">
        {nums ? (
          <>
            <span>합 <b className="num">{sum(nums)}</b></span>
            <span>홀{oddCount(nums)} : 짝{PICK - oddCount(nums)}</span>
            <span>구간 <b>{decadeSpread(nums)}</b>곳</span>
            <span>누적 출현 <b className="num">{fmt(nums.reduce((a, x) => a + allFreq[x], 0))}</b>회</span>
          </>
        ) : <span>번호 발급을 누르면 여기에 번호가 채워집니다.</span>}
      </div>
    </div>
  );
}
