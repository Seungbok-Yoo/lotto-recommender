# AGENTS.md — 로또 번호 발급기 (웹) 유지보수 컨텍스트

> 사람과 AI 에이전트가 이 폴더를 고치기 전에 읽는 문서.
> 빠른 사용법은 [README.md](README.md), 여기는 **왜 이렇게 되어 있는지, 무엇을 깨면 안 되는지**를 적는다.
> 마지막 갱신: 2026-09-27

---

## 1. 한눈에 보기

| 항목 | 내용 |
|---|---|
| 무엇 | 로또 6/45 당첨 이력(1~1243회)을 분석해 추천 번호를 발급하고 통계 대시보드를 보여주는 한 페이지 React 앱 |
| 원본 로직 | 상위 폴더의 `lottery.py` (Python CLI). 웹은 그 로직을 JS 로 **이식**한 것 |
| 스택 | React 18.3.1 (UMD, CDN) + Babel standalone 7.24.7 (브라우저에서 JSX 변환) + 순수 CSS |
| 빌드 | `python web/build.py` → `web/dist/lotto_app.html` 한 파일 (데이터 내장, 약 67KB) |
| 테스트 | `python web/build.py --test` → Edge 헤드리스로 `tests/runner.html` 실행 |
| 저장소 | https://github.com/Seungbok-Yoo/lotto-recommender (public). CI: `.github/workflows/deploy.yml` |
| 배포 | GitHub Pages https://seungbok-yoo.github.io/lotto-recommender/ (main push 시 자동) + claude.ai Artifact 사본(비공개): https://claude.ai/artifact/Kecv9kyucpc7s5GXuir6rt |
| 데이터 갱신 | `update-data.yml` 매주 일요일 09:00 KST. GitHub 서버에서도 API 접속 확인됨 (2026-09-27) |
| UI 언어 | 한국어 |

### 환경 제약 (설계를 결정한 조건)
- **Node.js 가 없다.** npm/Vite/Jest 를 쓸 수 없어 Python 빌드 + 브라우저 테스트로 대신한다.
- **Windows + PowerShell 5.1.** `&&` 불가, 한글 경로(`AI Agent 모음집`) 포함.
- **Artifact 샌드박스(CSP)**: 스크립트는 cdnjs / jsdelivr 등 허용 CDN 에서만, `fetch` 로 외부 사이트 호출 불가.
  → 페이지가 동행복권 API 를 직접 부를 수 없어서 **데이터를 빌드 때 HTML 에 내장**한다.

---

## 2. 데이터 흐름

```
동행복권 API ──(python lottery.py --update)──▶ lotto_history.json   ← 데이터의 유일한 원천
                                                     │
web/src/** (스타일·로직·컴포넌트) ──┐                 │
                                    ├─(python web/build.py)─▶ web/dist/lotto_app.html
                                    │                           │
                                    └───────────────────────────┴─▶ Artifact 배포 / 브라우저로 열기
```

### 동행복권 API (공식 문서 없음 — 2026-09-27 결과 페이지 분석으로 확인)
- 현재: `GET https://www.dhlottery.co.kr/lt645/selectPstLt645InfoNew.do?srchLtEpsd={회차}`
  - 요청 회차 **주변 10개 회차**를 `data.list[]` 로 반환 (예: 1100 → 1095~1104, 1 → 1~10)
  - 필드: `ltEpsd`(회차), `tm1WnNo`~`tm6WnNo`(번호), `bnsWnNo`(보너스), `ltRflYmd`(추첨일)
  - 미추첨 회차: `data.list` 가 빈 배열 / POST 는 500 에러
  - 헤더 `Referer`, `X-Requested-With` 를 붙여 브라우저 요청처럼 보낸다
- 폐기됨: `common.do?method=getLottoNumber&drwNo=` → 302 로 메인 페이지 리다이렉트 (2025년 사이트 개편)
- 사이트가 또 개편되면 `lottery.py` 가 "JSON 대신 페이지를 반환" 오류를 낸다. 그때는
  `https://www.dhlottery.co.kr/lt645/result` 페이지 HTML 에서 `*.do` 호출을 찾아 새 엔드포인트를 확인한다.

---

## 3. 디렉터리 맵과 책임

```
web/
├─ AGENTS.md                이 문서 (루트 CLAUDE.md → 루트 AGENTS.md → 이 파일 순으로 가져온다)
├─ README.md                사람용 빠른 안내
├─ build.py                 빌드 + 테스트 실행기. 파일 합치는 순서(STYLES/LIB/APP)가 여기 있다
├─ src/
│  ├─ index.html            뼈대. /*@styles*/ /*@data*/ /*@lib*/ /*@app*/ 자리표시 4개
│  ├─ styles/
│  │  ├─ tokens.css         색·글꼴 변수 (테마는 여기만)
│  │  ├─ base.css           배경, 레이아웃, 헤더, 공용 클래스
│  │  ├─ ball.css           로또 공
│  │  ├─ generator.css      발급 패널
│  │  └─ dashboard.css      대시보드
│  ├─ lib/                  ★ 순수 로직 — React/DOM 사용 금지, 테스트 대상
│  │  ├─ lotto.js           추천 알고리즘 (lottery.py 이식)
│  │  └─ stats.js           대시보드 통계
│  └─ app/                  화면 — 계산은 lib/ 함수를 불러서만 한다
│     ├─ constants.js       DRAWS, 모드·기간 목록, 공 색상, fmt/gameLabel
│     ├─ components/*.jsx   한 파일 = 한 화면 영역
│     └─ App.jsx            최상위 + ReactDOM 렌더 (반드시 마지막)
├─ tests/
│  ├─ lotto.test.js         lib/ 단위 테스트 (시드 난수로 재현 가능)
│  └─ runner.html           src/lib 원본을 직접 로드하는 미니 테스트 러너
└─ dist/                    빌드 산출물 (lotto_app.html + Pages 용 index.html) — 직접 수정 금지, git 제외
```

### 컴포넌트 트리
```
App
├─ header (DrawBalls: 최근 회차)
├─ Generator                상태: mode, count, useFilter, result, issueNo
│  ├─ GeneratorControls     입력만 (상태 없음, 콜백으로 올림)
│  └─ GameSlip → GameRow    결과 표시, 복사 상태만 보유
└─ Dashboard                상태: period → summarize(recentDraws(...))
   ├─ SummaryTiles
   ├─ DistributionChart     상태: active(마우스 올린 번호)
   ├─ RankList ×2           많이/적게 나온 TOP 10
   ├─ GroupBreakdown
   └─ RecentDraws
```

---

## 4. 깨면 안 되는 규칙 (불변식)

1. **전역 스코프 공유.** 번들러가 없어 모든 파일이 한 스코프에서 이어 붙여진다.
   - `import` / `export` / `require` 금지.
   - 최상위 이름(함수·상수)은 **파일 간에 유일**해야 한다. 추가 전 `Grep` 으로 중복 확인.
   - 새 파일은 `build.py` 의 `STYLES` / `LIB` / `APP` 목록에 **쓰는 쪽보다 앞에** 넣는다.
   - `lib/` 는 일반 `<script>`, `app/` 은 `<script type="text/babel">` 로 들어간다. JSX 는 `app/` 에만.
2. **`lib/` 는 순수해야 한다.** React, DOM, `window.RAW_DRAWS` 를 참조하지 않는다
   (예외: `cryptoRandom` 의 `crypto`). 난수는 `rng` 인자로 주입 가능하게 유지한다 — 테스트가 의존한다.
3. **Python 과 JS 로직은 중복이다.** `lottery.py` 와 `src/lib/lotto.js` 는 같은 알고리즘이다.
   가중치 공식, `FILTER` 기준(합 100–175, 홀 2–4, 연속 ≤2, 구간 ≥3), half_life=150, floor 5%,
   재시도 한도(count×20000) 중 하나를 바꾸면 **양쪽 다** 바꾸고 테스트를 고친다.
4. **`dist/` 는 산출물.** 고칠 일이 있으면 `src/` 를 고치고 다시 빌드한다.
5. **데이터 원천은 `lotto_history.json` 하나.** HTML 에 번호를 손으로 넣지 않는다.
   형식: `[{"round": 1, "numbers": [6개, 오름차순], "bonus": n}, ...]`
6. **색은 `tokens.css` 변수로만.** 다른 CSS·JSX 에 hex 를 새로 쓰지 않는다
   (현재 예외: 형광 초록 glow 의 `rgba(57,255,136,…)` 몇 곳, 공 텍스트 `#fff`).
   공 색상 `--ball-1..5` 는 동행복권 실물 구간 색이므로 테마와 무관하게 유지한다.
7. **어두운 배경 + 형광 초록(#39FF88) 단일 테마는 사용자 결정이다.** 라이트 테마를 되살리지 않는다 (요청이 있을 때만).
8. **책임 있는 안내 문구 유지.** "로또 추첨은 매회 독립 사건…" 문구와 1등 확률 표시는 지우지 않는다.
   추천이 당첨 확률을 높인다고 암시하는 문구를 추가하지 않는다 (χ² 검정상 번호 간 차이는 우연 범위).
9. **CDN 버전 고정.** `index.html` 의 React/Babel URL 은 정확한 버전으로 둔다. 허용 호스트: cdnjs, jsdelivr, unpkg.

---

## 5. 작업별 레시피

| 하고 싶은 일 | 고칠 곳 | 확인 |
|---|---|---|
| 최신 회차 반영 | `python lottery.py --update` → `python web/build.py` | 헤더의 "최근 N회" |
| 테마·색 변경 | `src/styles/tokens.css` | 빌드 후 화면 |
| 필터 기준 변경 | `lib/lotto.js` 의 `FILTER` **+** `lottery.py` 상수 **+** 테스트 | `--test` |
| 추천 알고리즘 변경 | `lib/lotto.js` **+** `lottery.py` | `--test` 에 케이스 추가 |
| 대시보드 수치 추가 | `lib/stats.js` 의 `summarize` → 카드 컴포넌트 | `--test` + 렌더 확인 |
| 새 화면 영역 | `app/components/새파일.jsx` + `build.py` APP 목록 + 필요 시 CSS | 렌더 확인 |
| 발급 모드 추가 | `lib/lotto.js` `buildWeights` 분기 + `app/constants.js` `MODES` (+ `lottery.py` choices) | `--test` |
| 재배포 | PR 을 main 에 병합하면 Pages 자동 배포. Artifact 사본은 같은 URL 로 다시 publish | Actions 탭, Pages 주소 |

---

## 6. 검증 방법

```powershell
python web/build.py --test    # 단위 테스트 16개, "ALL PASS 16/16" 이어야 함
python web/build.py           # 빌드
```

렌더 스모크 테스트 (컴포넌트 연결 확인, 네트워크 필요 — CDN 로드):
```powershell
$uri = ([System.Uri](Resolve-Path "web\dist\lotto_app.html").Path).AbsoluteUri
$out = & "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --headless=new --disable-gpu --virtual-time-budget=15000 --dump-dom $uri | Out-String
'로또 번호 발급','당첨 통계','전체 출현 분포','최근 당첨 번호' | % { "$_ : $($out.Contains($_))" }
```
Edge 콘솔의 `fallback_task_provider` 오류 로그는 무시해도 된다 (Edge 자체 로그).

CI: 모든 push·PR 에서 `deploy.yml` 이 Ubuntu + headless Chrome 으로 `--test` 와 빌드를 돌린다.
테스트가 실패하면 배포되지 않는다. `build.py` 는 Windows 에선 Edge 경로, Linux 에선 PATH 의 Chrome 을 쓴다.

자동화되지 않은 것: 발급 버튼 클릭 동작, 애니메이션, 복사 버튼, 모바일 레이아웃 → 사람이 브라우저에서 확인.

---

## 7. 알려진 한계 / 다음 후보

- 데이터가 빌드 시점(1243회)에 고정 — 매주 수동 갱신 + 재빌드 필요.
- Babel standalone(약 3MB)을 브라우저에서 돌려 첫 로딩이 느리다. Node 도입 시 사전 컴파일로 해결.
- 발급 이력 저장, 고정수/제외수, 필터 기준 조정 UI 없음.
- 45개 막대 차트는 모바일에서 가로 스크롤.
- Python·JS 로직 중복 (규칙 3). Node 도입 후에도 남는 구조적 부채.

**Node.js 도입 시 이전 경로:** Vite + React 프로젝트 생성 → `lib/*.js` 에 `export`, 컴포넌트에 `import` 추가 →
`window.RAW_DRAWS` 대신 JSON import 또는 개발 서버 프록시로 API 직접 조회 → 테스트는 Vitest 로 이동.

---

## 8. 결정 기록 (왜 이렇게 했나)

| 결정 | 이유 | 대안과 기각 사유 |
|---|---|---|
| 한 파일 HTML 로 빌드 | Artifact 배포, 더블클릭 실행, `file://` 에서 동작 | 다중 파일 — `file://` 에서 Babel 이 외부 JSX 를 못 읽음 |
| Python 빌드 스크립트 | Node 없음, 프로젝트가 이미 Python | npm 스크립트 — 설치 불가 |
| 브라우저 내 Babel | JSX 가독성 유지 (사용자가 "React" 를 요청) | `React.createElement` 직접 작성 — 가독성 저하 |
| 데이터 내장 | Artifact CSP 가 외부 fetch 차단 | 실시간 조회 — 불가 |
| `crypto.getRandomValues` | Python `SystemRandom` 과 동등한 난수 품질 | `Math.random` — 예측 가능 |
| Edge 헤드리스 테스트 | Node 없이 JS 를 실행할 유일한 수단 | Jest — 설치 불가 |
| 다크 + 형광 초록 단일 테마 | 사용자 요청 ("로또 느낌") | 라이트/다크 전환 — 요청으로 제거 |

---

## 9. AI 작업 이력 (Provenance)

이 폴더의 코드는 **전부 AI 에이전트(Claude Code, 모델 Claude Opus 5.5)가 작성**했다.
사람(사용자)은 요구사항과 방향을 정했고, 코드 작성·조사·검증은 AI 가 수행했다.
사람이 코드를 한 줄씩 검토한 기록은 없다 — 수정 전에 이 점을 감안할 것.

| 날짜 | 사람의 요청 | AI 가 한 일 | AI 가 검증한 방법 |
|---|---|---|---|
| 2026-09-27 | "JSON 대신 페이지 반환" 오류 원인과 해결 | API 직접 호출·리다이렉트 추적·IP 국가 확인으로 원인 규명(차단 아님, 엔드포인트 폐기), 결과 페이지 HTML 분석으로 새 API 발견, `lottery.py` 의 `API_URL`·헤더·`fetch_draw`·오류 문구 수정 | 실제 실행으로 1~1243회 수집 성공 (약 13초) |
| 2026-09-27 | React 로 구현, 발급 버튼 + 출현 분포 대시보드 | Node 부재 확인 후 Artifact 한 페이지 방식 결정, 추천 로직 JS 이식, UI/대시보드 설계·구현 | 이 단계에선 브라우저 실행 검증 없음 (사후 아래 단계에서 확인) |
| 2026-09-27 | 어두운 배경 + 형광 초록 | 토큰 교체, glow·강조 적용 | 없음 (시각 확인은 사용자) |
| 2026-09-27 | 장단점 평가 | 자기 산출물 비판적 평가 | — |
| 2026-09-27 | 구조별로 분리해 유지보수 쉽게 | `web/` 구조 설계, 파일 분리, `lib/` 순수 함수화(`stats.js` 신설, `rng` 주입), `build.py`, 테스트 16개, README | 단위 테스트 16/16 통과, Edge 헤드리스 렌더로 전 섹션 표시 확인 |
| 2026-09-27 | 유지보수 컨텍스트 문서 | 이 `AGENTS.md` / `CLAUDE.md` 작성 | — |
| 2026-09-27 | GitHub 에 직접 연결 | Git·GitHub CLI 설치, `.gitignore`, 루트 `AGENTS.md`/`CLAUDE.md`/`README.md`, `build.py` Linux 브라우저 탐색·`index.html` 출력, `deploy.yml`·`update-data.yml` 작성, public 저장소 생성·push, Pages 활성화 (저장소 공개 여부·이름은 사람이 결정, GitHub 로그인은 사람이 수행) | CI 첫 실행 성공(테스트·빌드·배포), Pages 주소 HTTP 200 + 1243회 데이터 포함 확인 |
| 2026-09-27 | (AI 발견) 갱신 실패가 조용히 무시되는 문제 | `lottery.py --update` 실패 시 종료 코드 1 — PR #1 | 로컬 종료 코드 0, PR 브랜치에서 `update-data.yml` 실행 성공 → GitHub 서버에서 API 접속 가능 확인 |
| 2026-09-28 | 프로그램에 AI Agent 가 개입하도록 — MCP 서버화 | `mcp_server/lotto_mcp.py` (도구 6개: 최신/회차 조회, 통계, 추천(고정수·제외수), 내 번호 분석, 이력 갱신), `lottery.recommend` 에 `fixed`·`use_filter` 추가 및 보충 루프 무한 반복 방지, `.mcp.json`, CI 에 MCP 테스트 추가 | 단위 9개 + MCP stdio 프로토콜 통합 테스트 1개 통과, 기존 CLI 출력 확인. Claude Desktop 실연결은 미확인 |

**AI 가 판단으로 정한 것 (사람이 명시하지 않음 — 바꿔도 되는 부분):**
글꼴(Black Han Sans / IBM Plex Sans KR / IBM Plex Mono), 레이아웃, 게임 수 상한 10, 대시보드 구성
(요약 타일·TOP10·구간별·최근 8회·χ²), 분석 기간 3종, 공 애니메이션, 폴더 구조와 파일 경계, 테스트 케이스 선정.

**사람이 정한 것 (함부로 바꾸지 말 것):** React 사용, 발급 버튼 방식, 출현 분포 대시보드, 다크 + 형광 초록 테마,
구조 분리 방침.

**AI 도 확인하지 못한 것:** `lottery.py` 의 원래 작성자·작성 경위 (이 기록 이전부터 존재),
동행복권 신규 API 의 안정성(비공식), 실제 기기에서의 모바일 표시, 클립보드 복사 동작.

---

## 10. AI 에이전트 작업 지침

- 시작 전: 이 문서 → `build.py` 의 파일 순서 → 고칠 파일 순으로 읽는다.
- 변경 후 반드시 `python web/build.py --test` 와 `python web/build.py` 를 실행하고 결과를 보고한다.
  렌더에 영향이 있으면 6장의 스모크 테스트도 돌린다.
- 로직을 바꾸면 `lottery.py` 와의 동기화 여부를 명시한다 (규칙 3).
- 새 최상위 이름을 만들기 전 `src/` 전체에서 중복을 검색한다 (규칙 1).
- Artifact 재배포 시 기존 URL 을 유지한다.
- 작업을 끝내면 9장 표에 한 줄 추가한다 (날짜, 요청, 한 일, 검증 방법). 검증 못 했으면 "없음"이라고 쓴다.
- PowerShell 5.1: `&&` 대신 `;` 또는 `if ($?) {}`. 파일 쓰기는 `-Encoding utf8`.
