// 로또 공 하나. size: "" | "sm" | "xs", pop: 등장 애니메이션 여부.
function Ball({ n, size = "", pop = false, delay = 0 }) {
  return (
    <span className={`ball ${size} ${pop ? "pop" : ""}`}
          style={{ "--c": ballColor(n), animationDelay: `${delay}ms` }}>{n}</span>
  );
}

function EmptyBall() {
  return <span className="ball empty" />;
}

// 당첨 번호 6개 + 보너스.
function DrawBalls({ draw, size }) {
  return (
    <div className="balls" style={{ gap: 6, alignItems: "center" }}>
      {draw.numbers.map(n => <Ball key={n} n={n} size={size} />)}
      <span className="plus">+</span>
      <Ball n={draw.bonus} size={size} />
    </div>
  );
}
