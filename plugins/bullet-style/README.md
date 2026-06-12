# bullet-style

- bullet과 indent로 한국어 글을 구조화하는 스타일 plugin
- prose 단락 대신 구조화된 정보 표현을 자동으로 따라가게 만듦

## 핵심 특징

- bullet 중심 구조화
  - 정보 전달성 글은 prose보다 bullet으로
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
  - 한국어 정보 전달 글쓰기 전반에 적용되는 스타일 가이드
  - 적용 영역
    - 노트 / 메모 / 회의록
    - 업무 정리 / 보고서
    - 기술 문서 / 트러블슈팅
    - Confluence / Notion / Obsidian 페이지

## 적용 시점

- 사용해야 할 때
  - 한국어로 정보 전달성 답변 작성
  - 노트, 메모, 회의록 작성
  - 업무 정리, 보고서, 트러블슈팅 문서 작성
  - Confluence / Obsidian / Notion 페이지 작성
- 사용하지 않아도 될 때
  - 단순 잡담
  - 짧은 질문 답변
  - 코드 작성 위주 작업

## SKILL.md 위치

- 경로
  - `skills/bullet-notes/SKILL.md`
- 호환
  - claude-code와 codex 양쪽에서 동일한 SKILL.md를 사용
  - 양쪽 모두 frontmatter는 `name` + `description` 표준 스키마
