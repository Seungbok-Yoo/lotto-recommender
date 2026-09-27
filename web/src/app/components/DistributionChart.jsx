// 번호 1~45 출현 횟수 막대 차트. 막대에 올리거나 탭하면 값을 보여준다.
const CHART = { W: 900, H: 290, L: 40, R: 14, T: 26, B: 30 };

function DistributionChart({ freq, expected }) {
  const counts = NUMBERS.map(n => freq[n]);
  const peakN = NUMBERS[counts.indexOf(Math.max(...counts))];
  const [active, setActive] = useState(null);
  const shown = active ?? peakN;

  const { W, H, L, R, T, B } = CHART;
  const { step, top } = niceScale(Math.max(...counts) * 1.05);
  const y = v => T + (H - T - B) * (1 - v / top);
  const bw = (W - L - R) / 45;
  const ticks = [];
  for (let v = 0; v <= top + 1e-9; v += step) ticks.push(v);
  const diff = expected ? (freq[shown] / expected - 1) * 100 : 0;

  return (
    <div className="card panel">
      <div className="card-head">
        <h3>전체 출현 분포</h3>
        <span className="readout">
          <b className="num">{shown}번</b> · <b className="num">{fmt(freq[shown])}회</b>
          {" "}(기대 대비 <span className="num">{diff >= 0 ? "+" : ""}{diff.toFixed(1)}%</span>)
        </span>
      </div>
      <div className="chart-scroll">
        <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="번호별 출현 횟수 막대 차트"
             onMouseLeave={() => setActive(null)}>
          {ticks.map(v => (
            <g key={v}>
              <line className="grid-line" x1={L} x2={W - R} y1={y(v)} y2={y(v)} />
              <text className="axis" x={L - 8} y={y(v) + 4} textAnchor="end">{v}</text>
            </g>
          ))}
          {NUMBERS.map((n, i) => {
            const x = L + i * bw;
            const dim = active !== null && active !== n;
            return (
              <g key={n} onMouseEnter={() => setActive(n)} onClick={() => setActive(n)} style={{ cursor: "pointer" }}>
                <rect x={x} y={T} width={bw} height={H - T - B} fill="transparent" />
                <rect x={x + bw * 0.16} y={y(freq[n])} width={bw * 0.68} height={Math.max(y(0) - y(freq[n]), 0)}
                      rx="2" fill={ballColor(n)} opacity={dim ? 0.35 : 1} />
                <text className={`axis-n ${shown === n ? "on" : ""}`} x={x + bw / 2} y={H - B + 16}
                      textAnchor="middle">{n}</text>
              </g>
            );
          })}
          <line className="exp-line" x1={L} x2={W - R} y1={y(expected)} y2={y(expected)} />
          <text className="exp-label" x={W - R} y={y(expected) - 6} textAnchor="end">기대 {expected.toFixed(1)}회</text>
          <text className="val-label" x={L + (shown - 1) * bw + bw / 2} y={y(freq[shown]) - 7}
                textAnchor="middle">{freq[shown]}</text>
        </svg>
      </div>
      <div className="legend">
        {NUMBER_GROUPS.map((g, i) => <span key={g.label}><i style={{ "--c": GROUP_COLORS[i] }} />{g.label}</span>)}
        <span>점선: 번호당 기대 출현 횟수</span>
      </div>
    </div>
  );
}
