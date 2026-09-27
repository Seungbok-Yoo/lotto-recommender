// 화면 전용 상수와 표시 헬퍼. 계산 로직은 lib/ 에 둔다.
const { useState, useMemo } = React;

const DRAWS = toDraws(window.RAW_DRAWS);

/** 구간별 공 색상 — NUMBER_GROUPS 와 순서가 같다. */
const GROUP_COLORS = ["var(--ball-1)", "var(--ball-2)", "var(--ball-3)", "var(--ball-4)", "var(--ball-5)"];
const ballColor = n => GROUP_COLORS[groupIndex(n)];

const MODES = [
  { id: "balanced", title: "균형", desc: "출현 빈도를 완만하게 반영" },
  { id: "hot", title: "핫넘버", desc: "많이 나온 번호 위주" },
  { id: "cold", title: "콜드넘버", desc: "적게 나온 번호 위주" },
  { id: "uniform", title: "완전 무작위", desc: "모든 번호를 같은 확률로" },
];

const PERIODS = [
  { id: "all", label: "전체", size: Infinity },
  { id: "300", label: "최근 300회", size: 300 },
  { id: "100", label: "최근 100회", size: 100 },
];

const MAX_GAMES = 10;

const fmt = n => n.toLocaleString("ko-KR");
/** 0 → A, 1 → B ... (용지의 게임 표기) */
const gameLabel = i => String.fromCharCode(65 + i);
