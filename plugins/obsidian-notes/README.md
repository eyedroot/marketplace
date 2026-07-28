# obsidian-notes

- Obsidian 노트를 오래 살아남는 형태로 작성하는 plugin
- 본문은 마크다운 네이티브로, 도해는 자립형 SVG 파일로 분리해 임베드

## 왜 필요한가

- Obsidian은 읽기 모드에서 노트 안의 `<style>` 태그를 제거함
  - 인라인 SVG가 CSS 변수를 참조하면 값이 무효가 됨
  - SVG 명세상 `fill` 초기값이 검정이라 **도해가 검은 박스로 보임**
  - 카드·배지 같은 클래스 기반 스타일도 전부 사라짐
- 마크다운 파서가 HTML 블록 중간의 빈 줄을 단락 구분으로 해석해 렌더링이 끊김
- 결과적으로 HTML+CSS 문서를 노트에 붙여넣는 방식은 취약함

## 어떻게 해결하는가

- 본문은 마크다운 네이티브
  - 표는 마크다운 표, 강조 박스는 Obsidian 콜아웃, 코드는 코드블록
  - 테마 · 다크모드 · 검색 · 백링크 · 그래프뷰가 전부 따라옴
- 도해는 별도 `.svg` 파일
  - 독립 문서로 로드되므로 파일 안의 `<style>`이 살아남음
  - `@media (prefers-color-scheme: dark)`로 다크모드 자동 대응
  - `![[그림.svg]]`로 임베드, 폭은 `![[그림.svg|800]]`로 조절
- HTML 원본은 `attachments/`에 그대로 두고 링크
  - "완전히 동일한 화면"이 필요할 때의 탈출구

## 포함된 skill

- `obsidian-notes`
  - 적용 상황
    - Obsidian vault에 노트를 만들거나 고칠 때
    - 개념 · 흐름 · 아키텍처를 그림으로 설명해야 할 때
    - 옵시디언에서 그림이 검게 나오거나 스타일이 안 먹을 때
    - HTML 문서를 옵시디언으로 옮길 때
  - 담고 있는 것
    - vault 경로 파악과 첨부 파일 관례
    - Obsidian 콜아웃 · 임베드 · frontmatter 사용법
    - 자립형 SVG의 필수 요소와 도해 레이아웃 세 형태
    - 읽기 모드에서 사라지는 태그와 문법 함정
    - CSS 스니펫이라는 대안과 그 한계

## 번들 스크립트

| 스크립트 | 역할 |
|---|---|
| `svg_scaffold.py` | 자립형 SVG 골격 생성 (테마 변수, 배경, 화살촉, 텍스트 클래스) |
| `extract_svg.py` | HTML의 인라인 SVG를 자립형 파일로 추출 (원본 CSS 변수를 SVG 안으로 이관) |
| `check_note.py` | 노트 검증 — 임베드 링크 실존, SVG 자립성, 강조 문법, frontmatter |

```bash
# 시퀀스 도해 골격 만들기
python scripts/svg_scaffold.py --out attachments/flow.svg --kind sequence \
  --roles "사용자,Claude,인증 서버,API"

# 기존 HTML에서 그림만 뽑아내기
python scripts/extract_svg.py 원본.html --out-dir "<vault>/폴더/attachments" --prefix fig

# 노트 저장 후 검증
python scripts/check_note.py "<vault>/폴더/노트.md"
```

## 참고 문서

- `references/svg-patterns.md`
  - 비교형 · 시퀀스형 · 구조형 도해의 좌표 설계와 예시
  - 검은 박스 · 폰트 · XML 주석 등 자주 겪는 문제
- `references/obsidian-syntax.md`
  - 콜아웃 13종, 임베드 변형, frontmatter 관례
  - 읽기 모드에서 사라지는 태그 목록
  - CSS 스니펫 작성 규칙

## 설치

### Claude Code

```
/plugin marketplace add eyedroot/marketplace
/plugin install obsidian-notes@eyedroot
```

### Codex

```bash
codex plugin marketplace upgrade eyedroot
codex plugin add obsidian-notes@eyedroot
```

- 두 도구가 같은 `.claude-plugin/marketplace.json`과 `skills/` 구조를 읽으므로 별도 변환이 필요 없음
