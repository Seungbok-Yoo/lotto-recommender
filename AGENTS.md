# AGENTS.md — lotto-recommender 저장소

> 사람과 AI 에이전트가 이 저장소를 고치기 전에 읽는 문서.
> 웹 페이지(`web/`)의 상세 규칙은 **[web/AGENTS.md](web/AGENTS.md)** 에 있다 — `web/` 를 건드리면 반드시 함께 읽는다.

@web/AGENTS.md

## 저장소 구성

| 경로 | 역할 |
|---|---|
| `lottery.py` | 동행복권 당첨 이력 수집 + CLI 번호 추천기 (Python 3.10+, 표준 라이브러리만) |
| `lotto_history.json` | 당첨 이력 데이터 — **웹 빌드의 유일한 데이터 원천**. 커밋 대상 |
| `web/` | 같은 추천 로직의 React 웹 페이지 (소스·빌드·테스트) |
| `.github/workflows/deploy.yml` | push/PR 마다 테스트·빌드, main 은 GitHub Pages 배포 |
| `.github/workflows/update-data.yml` | 매주 일요일 09:00 KST 당첨 이력 갱신 → 커밋 → 배포 호출 |

## 자주 쓰는 명령

```powershell
python lottery.py                # 5게임 추천 (CLI)
python lottery.py --update       # 최신 회차까지 이력 갱신
python web/build.py --test       # 웹 로직 단위 테스트
python web/build.py              # web/dist/ 빌드
```

## 작업 규칙

- **main 에 직접 push 하지 않는다.** 브랜치 → PR → CI(Test & Deploy) 통과 → 사람이 검토 후 병합.
- `lottery.py` 와 `web/src/lib/lotto.js` 는 같은 알고리즘이다. 한쪽을 바꾸면 다른 쪽도 맞춘다.
- `lottery.py` 의 API 부분(`API_URL`, `fetch_draw`)은 비공식 엔드포인트 역분석 결과다 — 근거는 web/AGENTS.md 2장.
- 작업을 마치면 web/AGENTS.md 9장 "AI 작업 이력" 표에 한 줄 추가한다.
