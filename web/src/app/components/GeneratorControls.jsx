// 발급 조건 입력: 추출 방식, 게임 수, 통계 필터, 발급 버튼.
function GeneratorControls({ mode, onMode, count, onCount, useFilter, onUseFilter, onIssue, issued }) {
  return (
    <div className="controls">
      <div className="field">
        <span className="lbl">추출 방식</span>
        <div className="modes">
          {MODES.map(m => (
            <button key={m.id} id={`mode-${m.id}`} className="mode" aria-pressed={mode === m.id}
                    onClick={() => onMode(m.id)}>
              <span className="dot" />
              <span className="t">{m.title}</span>
              <span className="d">{m.desc}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="field">
        <span className="lbl">게임 수</span>
        <div className="stepper">
          <button id="count-dec" aria-label="게임 수 줄이기" disabled={count <= 1}
                  onClick={() => onCount(count - 1)}>−</button>
          <output className="num" aria-live="polite">{count}</output>
          <button id="count-inc" aria-label="게임 수 늘리기" disabled={count >= MAX_GAMES}
                  onClick={() => onCount(count + 1)}>+</button>
        </div>
      </div>

      <div className="field">
        <label className="toggle">
          <input id="use-filter" type="checkbox" checked={useFilter}
                 onChange={e => onUseFilter(e.target.checked)} />
          통계 필터 적용
        </label>
        <div className="rules" data-off={!useFilter}>
          <span className="chip">합 {FILTER.sum[0]}–{FILTER.sum[1]}</span>
          <span className="chip">홀수 {FILTER.odd[0]}–{FILTER.odd[1]}개</span>
          <span className="chip">연속 {FILTER.maxConsecutive}개 이하</span>
          <span className="chip">구간 {FILTER.minDecades}곳 이상</span>
        </div>
      </div>

      <button id="issue" className="issue" onClick={onIssue}>
        {issued ? "다시 발급" : "로또 번호 발급"}
      </button>
    </div>
  );
}
