# with-codex

- Claude(1차) → Codex(2차) 듀얼 에이전트 검증을 한 줄 명령으로 묶은 워크플로우 plugin
- `/with-codex <프롬프트>` 한 번이면 1차 작업과 Codex 교차 검증까지 자동 분기
- `openai-codex` 마켓플레이스의 `/codex:rescue`, `/codex:review`를 이미 설치한 환경에서 사용

## 포함된 command

- `/with-codex`
  - 1차 — Claude가 사용자 프롬프트를 평소대로 수행
  - 분기 A — 진행 중 막히거나 애매하면 `/codex:rescue`로 추가 조사 위임
  - 분기 B — 1차가 매끄럽게 끝나면 `/codex:review`로 독립 검수 후 의견 합의
  - 분기 C — Claude와 Codex 결론을 비교하여 합치/이견을 명시적으로 보고
  - 옵션 — `--rescue-only`, `--review-only`로 한쪽만 실행 가능

## 전제 조건

- Claude Code에 [openai-codex 플러그인](https://github.com/openai/codex)이 설치되어 있어야 함
  - `/codex:rescue`, `/codex:review` 명령이 동작하는 상태여야 함
- Codex CLI 인증 완료 (필요 시 `/codex:setup` 실행)

## 설치

```bash
/plugin marketplace add eyedroot/eyedroot-marketplace
/plugin install with-codex@eyedroot
```

## 사용 예시

```
/with-codex 이 마이그레이션 스크립트의 다운타임 위험을 검토해줘
/with-codex --review-only 방금 푸시한 PR을 교차 검수해줘
/with-codex --rescue-only 이 NullPointerException 원인을 못 찾겠어
```

## 라이선스

- MIT
