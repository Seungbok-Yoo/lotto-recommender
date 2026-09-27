# lotto-recommender

로또 6/45 당첨 이력(1회~)을 분석해 추천 번호를 발급하는 도구.
Python CLI 와, 같은 로직을 옮긴 React 웹 페이지(통계 대시보드 포함)로 되어 있다.

## 사용

```bash
python lottery.py                  # 5게임 추천
python lottery.py -n 10 --mode hot # 10게임, 많이 나온 번호 위주
python lottery.py --stats          # 통계만
python lottery.py --update         # 최신 회차까지 이력 갱신
```

웹 페이지: `python web/build.py` 후 `web/dist/index.html` 을 브라우저로 연다. main 브랜치는 GitHub Pages 로 자동 배포된다.

AI 에이전트 연동: [mcp_server/](mcp_server/README.md) 의 MCP 서버를 Claude Code·Claude Desktop 에 연결하면,
대화로 "7번 넣고 핫넘버로 5게임 추천해줘", "이 번호 분석해줘" 처럼 요청할 수 있다.

## 문서

- [web/README.md](web/README.md) — 웹 빌드·구조 요약
- [AGENTS.md](AGENTS.md), [web/AGENTS.md](web/AGENTS.md) — 유지보수 컨텍스트 (설계 이유, 규칙, AI 작업 이력)

## 참고

- 당첨 데이터는 동행복권 사이트의 비공식 API 에서 가져온다. 사이트 개편 시 동작이 멈출 수 있다.
- 로또 추첨은 매회 독립 사건이다. 과거 빈도는 다음 회차 확률을 바꾸지 않으며, 이 도구는 조합 선택의 참고 자료일 뿐이다.
- 이 저장소의 코드는 AI 에이전트(Claude Code)가 작성했다. 자세한 이력은 web/AGENTS.md 9장.
