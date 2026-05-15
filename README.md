# eyedroot-marketplace

- 비즈([@eyedroot](https://github.com/eyedroot))의 personal plugin marketplace
- 글쓰기 스타일, 업무 자동화 등 개인용 plugin / skill 모음
- **claude-code**와 **codex** 양쪽에서 동작하도록 SKILL.md 표준 포맷으로 작성

## 포함된 plugin

- `bullet-style`
  - bullet과 indent로 한국어 글을 구조화하는 스타일 plugin
  - 포함 skill
    - `bullet-notes`
      - bullet 중심 구조화
      - 두괄식
      - 친근한 대화체 어미

## 설치

### Claude Code

- 원격 마켓플레이스로 등록 (GitHub push 후 가능)
  ```bash
  /plugin marketplace add eyedroot/eyedroot-marketplace
  /plugin install bullet-style@eyedroot
  ```
- 로컬 경로로 등록 (개발 / 테스트용)
  ```bash
  /plugin marketplace add /path/to/eyedroot-marketplace
  ```

### Codex CLI

- codex는 두 경로에서 SKILL.md를 탐색해요
  - `~/.codex/skills/`
    - 전역 (모든 codex 세션에서 적용)
  - `<project>/.agents/skills/`
    - 프로젝트 단위 (해당 repo에서만 적용)
- 마켓플레이스 내부 skill을 그대로 심볼릭 링크하면 양쪽에서 같은 파일을 공유할 수 있어요

#### 전역 설치

```bash
git clone https://github.com/eyedroot/eyedroot-marketplace.git
cd eyedroot-marketplace

mkdir -p ~/.codex/skills
ln -s "$(pwd)/plugins/bullet-style/skills/bullet-notes" ~/.codex/skills/bullet-notes
```

#### 프로젝트 단위 설치

```bash
cd <your-project>
mkdir -p .agents/skills
ln -s /path/to/eyedroot-marketplace/plugins/bullet-style/skills/bullet-notes .agents/skills/bullet-notes
```

## 디렉토리 구조

```
eyedroot-marketplace/
├── .claude-plugin/
│   └── marketplace.json              # 마켓플레이스 메타데이터
├── README.md
└── plugins/
    └── bullet-style/
        ├── .claude-plugin/
        │   └── plugin.json           # plugin 메타데이터
        ├── README.md
        └── skills/
            └── bullet-notes/
                └── SKILL.md          # claude-code / codex 공용 skill 정의
```

## 호환성 노트

- SKILL.md frontmatter 스키마
  - 필수 필드
    - `name`
    - `description`
  - claude-code와 codex가 동일 스키마 사용
    - 양쪽 전용 필드는 현재 시점 기준 없음
  - 결과적으로 같은 SKILL.md 파일을 양쪽에서 그대로 재사용 가능
- 자동 설치 범위
  - claude-code
    - 마켓플레이스 명령어로 자동 설치
  - codex
    - 수동 심볼릭 링크 필요 (위 설치 안내 참조)

## 참고

- claude-code 마켓플레이스 문서
  - https://code.claude.com/docs/en/plugin-marketplaces
- claude-code plugin 레퍼런스
  - https://code.claude.com/docs/en/plugins-reference
- codex Agent Skills 문서
  - https://developers.openai.com/codex/skills

## 라이선스

- MIT

> 자기다운 도구가 결국 가장 자주 손에 잡히는 법이라, 이 마켓플레이스는 비즈 본인을 위한 도구함이에요.
