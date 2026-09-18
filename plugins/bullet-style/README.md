# bullet-style

- 별도로 보관할 한국어 노트를 bullet과 indent로 구조화하는 스타일 plugin
- 일반 대화의 기본 답변 형식으로 자동 적용하지 않고, 스킬을 명시적으로 호출한 노트 산출물에만 적용

## 핵심 특징

- bullet 중심 구조화
  - 요청된 노트 본문은 prose보다 bullet으로
  - indent depth로 위계 시각화
- 두괄식
  - 핵심 결론을 글머리에 배치
- 간단명료한 명사형 종결 어미
  - "~함", "~임", "~했음"
  - 어미 규칙은 SKILL.md의 "톤과 어미" 섹션에서만 관리
- 의도적으로 피하는 표현
  - 이모지
  - 과도한 동의 / 아첨
  - 작업 소요 시간 추정

## 포함된 skill

- `bullet-notes`
  - 별도 보관용 한국어 노트에 적용되는 스타일 가이드
  - 적용 영역
    - 노트 / 메모 / 회의록
    - 업무 정리 / 보고서
    - 기술 문서 / 트러블슈팅
    - Confluence / Notion / Obsidian 페이지

## 적용 시점

- 사용해야 할 때
  - 사용자가 스킬을 직접 호출해 노트, 메모, 회의록 작성을 요청한 때
  - 별도로 저장할 업무 정리, 보고서, 트러블슈팅 기록을 요청한 때
  - Confluence / Obsidian / Notion에 붙여 넣을 문서 본문을 요청한 때
- 사용하지 않을 때
  - 일반 대화와 질의응답
  - 코드 설명, 추천, 상담, 작업 진행 보고
  - 코드 작성 위주 작업

## SKILL.md 위치

- 경로
  - `skills/bullet-notes/SKILL.md`
- 호환
  - claude-code와 codex 양쪽에서 동일한 SKILL.md를 사용
  - 양쪽 모두 frontmatter는 `name` + `description` 표준 스키마
  - codex에서는 `agents/openai.yaml`로 암묵적 호출을 끄고 명시적 호출만 허용
