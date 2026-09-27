# 로또 번호 발급기 (웹)

`lottery.py` 의 추천 로직을 React 페이지로 옮긴 것. Node.js 없이 Python 만으로 빌드한다.
설계 이유, 지켜야 할 규칙, AI 작업 이력은 [AGENTS.md](AGENTS.md) 에 있다.

## 작업 흐름

```powershell
python lottery.py --update     # 1. 최신 회차까지 lotto_history.json 갱신
python web/build.py --test     # 2. 로직 단위 테스트 (Edge 헤드리스)
python web/build.py            # 3. web/dist/lotto_app.html 생성
```

`dist/` 는 빌드 결과물이므로 직접 고치지 말고 `src/` 를 고친 뒤 다시 빌드한다.

## 구조

| 경로 | 역할 |
|---|---|
| `src/index.html` | 페이지 뼈대. `/*@styles*/` `/*@data*/` `/*@lib*/` `/*@app*/` 자리에 빌드가 내용을 채운다 |
| `src/styles/tokens.css` | 색·글꼴 변수. 테마를 바꿀 땐 이 파일만 고친다 |
| `src/styles/*.css` | 영역별 스타일 (base, ball, generator, dashboard) |
| `src/lib/lotto.js` | 추천 로직 (가중치, 추출, 필터, 추천). React 에 의존하지 않는 순수 함수 |
| `src/lib/stats.js` | 대시보드 통계 계산 (χ², 순위, 구간, 요약) |
| `src/app/constants.js` | 화면용 상수 (모드, 기간, 공 색상)와 표시 헬퍼 |
| `src/app/components/` | 화면 컴포넌트. 한 파일에 한 영역 |
| `src/app/App.jsx` | 최상위 화면 + 렌더 시작 |
| `tests/` | `lib/` 단위 테스트와 브라우저 러너 |
| `build.py` | 조각 + 데이터 → `dist/lotto_app.html`, `--test` 로 테스트 실행 |

## 파일을 추가할 때

번들러가 없어 모든 파일이 하나의 전역 스코프를 공유한다. `import`/`export` 는 쓰지 않고,
새 파일은 `build.py` 의 `STYLES` / `LIB` / `APP` 목록에 **의존 순서대로** 추가한다
(쓰는 쪽보다 앞에). 함수·상수 이름은 파일끼리 겹치지 않게 짓는다.
