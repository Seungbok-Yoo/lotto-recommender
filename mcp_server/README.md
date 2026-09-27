# 로또 MCP 서버

`lottery.py` 의 기능을 [MCP(Model Context Protocol)](https://modelcontextprotocol.io) 도구로 공개한다.
Claude 같은 AI 에이전트가 대화 중에 이 도구들을 **스스로 골라 호출**해 당첨 이력을 조회하고 번호를 추천한다.
번호 추출과 통계 계산은 전부 `lottery.py` 가 하므로 AI 가 숫자를 지어내지 않는다.

## 도구

| 도구 | 하는 일 |
|---|---|
| `get_latest_draw` | 최신 회차 당첨 번호, 보유 이력 범위 |
| `get_draw(round_no)` | 특정 회차 당첨 번호 |
| `get_statistics(last_n?)` | 출현 빈도, TOP 10, χ² 균등성 검정, 구간별 통계 (전체 또는 최근 N회) |
| `recommend_numbers(count, mode, include, exclude, use_filter)` | 추천 조합. 고정수·제외수 지정 가능 |
| `analyze_numbers(numbers)` | 내 번호 분석: 필터 규칙별 통과 여부, 과거에 매주 샀다면 등수별 적중 횟수 |
| `update_history` | 동행복권에서 새 회차 받아 갱신 (네트워크) |

## 설치

```powershell
python -m pip install -r mcp_server/requirements.txt
```

## 연결

### Claude Code
저장소 루트의 `.mcp.json` 에 등록되어 있다. 이 폴더에서 Claude Code 를 열면 `lotto` 서버 사용 여부를 묻는다 → 승인.
`/mcp` 로 연결 상태를 확인한다.

### Claude Desktop
`%APPDATA%\Claude\claude_desktop_config.json` 에 추가 (경로는 본인 PC 에 맞게, 역슬래시는 `\\`):

```json
{
  "mcpServers": {
    "lotto": {
      "command": "python",
      "args": ["C:\\Users\\topse\\Desktop\\AI Agent 모음집\\Lottery_Program\\mcp_server\\lotto_mcp.py"]
    }
  }
}
```
저장 후 Claude Desktop 을 완전히 종료했다가 다시 연다.

## 이렇게 물어보면 된다

- "최근 100회 기준으로 많이 나온 번호 알려줘"
- "7번이랑 33번은 꼭 넣고 1, 2, 3번은 빼서 핫넘버 모드로 5게임 추천해줘"
- "3, 14, 22, 31, 38, 43 이 번호 분석해줘. 과거에 매주 샀으면 몇 등 몇 번 됐어?"
- "이번 주 당첨 번호 갱신하고 새 회차 번호 알려줘"

## 테스트

```powershell
python -m unittest discover -s mcp_server -v
```
단위 테스트 + 실제 MCP 클라이언트로 서버를 stdio 로 띄워 도구를 호출하는 통합 테스트. CI(`deploy.yml`)에서도 실행된다.

## 주의

- stdout 은 MCP 프로토콜 전용이다. 서버 코드와 `lottery.py` 에서 stdout 으로 `print` 하면 연결이 깨진다 (진행 메시지는 stderr).
- 이력 파일은 저장소 루트의 `lotto_history.json` 을 그대로 쓴다.
