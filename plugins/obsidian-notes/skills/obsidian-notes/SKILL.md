---
name: obsidian-notes
description: Obsidian 노트를 마크다운 네이티브로 작성하고, 도해가 필요하면 자립형 SVG 파일로 만들어 임베드하는 방법. Obsidian vault에 노트를 만들거나 고칠 때, 개념·흐름·아키텍처를 그림으로 설명해야 할 때, 옵시디언에서 그림이 검게 나오거나 스타일이 안 먹을 때, HTML 문서를 옵시디언으로 옮길 때 사용. "옵시디언에 정리해줘", "노트로 만들어줘", "다이어그램 넣어줘", "그림으로 설명해줘", "vault에 저장", "옵시디언에서 안 보여" 같은 요청에 반드시 적용. 옵시디언은 노트 안의 style 태그를 제거하므로 HTML+CSS를 그대로 붙여넣으면 깨진다 — 이 스킬이 그 함정을 피하는 방법을 담고 있으니, 옵시디언 노트를 다룰 때는 먼저 읽을 것.
---

# Obsidian 노트 작성

Obsidian에서 오래 살아남는 노트를 만드는 방법. 핵심 판단은 **본문은 마크다운 네이티브로, 그림은 자립형 SVG 파일로 분리**하는 것임.

## 왜 이 방식인가

Obsidian은 노트 안의 HTML을 읽기 모드에서 렌더링하지만, `<style>`과 `<script>` 태그는 **보안상 제거함**. 이 사실 하나에서 대부분의 실패가 파생됨.

- 인라인 SVG에 `fill="var(--accent)"`를 쓰면 → CSS 변수가 정의되지 않음 → 값이 무효 → SVG 명세상 `fill` 초기값인 **검정**으로 칠해짐 → 도해가 검은 박스로 보임
- 카드·배지·간격 같은 클래스 기반 스타일이 전부 사라져 평문처럼 보임
- 마크다운 파서가 HTML 블록 중간의 **빈 줄**을 단락 구분으로 해석해 그 뒤부터 렌더링이 깨짐

그래서 HTML+CSS 문서를 노트에 그대로 붙여넣는 방식은 취약함. 반면 마크다운 네이티브는 테마·다크모드·검색·백링크·그래프뷰가 전부 공짜로 따라오고, SVG를 별도 파일로 두면 그 파일은 독립 문서로 로드되어 **내부 `<style>`이 살아남음**.

## 작업 순서

1. 노트의 성격을 정함 — 개념 설명, 절차 기록, 회의 정리, 조사 결과 등
2. 본문을 마크다운으로 작성 (아래 "마크다운 작성" 참고)
3. 그림이 필요한 자리를 표시하고, 각 도해를 자립형 SVG 파일로 만듦 (아래 "SVG 도해" 참고)
4. `scripts/check_note.py`로 검증 — 임베드 링크 실존, SVG 자립성, 강조 문법을 한 번에 확인
5. 사용자에게 읽기 모드에서 확인을 요청

## vault 경로 파악

노트를 쓰기 전에 vault 위치를 확인함. Obsidian MCP가 붙어 있으면 `list_directory`로 폴더 구조를 보고 기존 노트 하나를 읽어 관례(frontmatter 필드, 폴더 규칙, 첨부 위치)를 파악함. MCP가 없으면 iCloud 기본 경로를 확인함.

```bash
ls ~/Library/Mobile\ Documents/iCloud~md~obsidian/Documents/
find ~ -maxdepth 4 -type d -name ".obsidian" 2>/dev/null
```

첨부 파일은 대상 노트와 같은 폴더의 `attachments/`에 둠. 이미 다른 이름을 쓰고 있으면 그것을 따름.

파일을 직접 쓸 때는 Obsidian MCP의 `write_note`보다 파일시스템 쓰기가 편할 때가 많음. 특히 본문이 길면 MCP 파라미터로 넘기는 비용이 큼. 단 `write_note`를 쓸 때는 frontmatter를 본문에 섞지 말고 **전용 파라미터로 전달**해야 함. 본문에 YAML을 직접 넣으면 문자열로 저장되어 태그·속성이 인식되지 않음.

## 마크다운 작성

Obsidian 고유 문법을 적극 활용함. 일반 마크다운보다 표현력이 좋고, 테마가 알아서 꾸며줌.

### 콜아웃

강조 박스는 HTML `<div>`가 아니라 콜아웃으로 씀. 접을 수도 있고(`> [!info]-`) 테마 색이 자동 적용됨.

```markdown
> [!info] 이 문서
> 배경과 목적을 적음

> [!warning] 주의
> 함정이나 제약을 적음

> [!danger] 현황
> 위험 수준의 사실을 적음

> [!tip] 용어 주의
> 헷갈리기 쉬운 개념을 짚음
```

쓸 수 있는 종류: `note` `abstract` `info` `todo` `tip` `success` `question` `warning` `failure` `danger` `bug` `example` `quote`

### 링크와 임베드

- 노트 간 연결: `[[노트 제목]]` — 백링크와 그래프뷰가 자동으로 잡힘
- 첨부 파일 열기: `[브라우저에서 열기](attachments/원본.html)`
- 이미지·SVG 삽입: `![[그림.svg]]`, 폭 지정은 `![[그림.svg|800]]`

### frontmatter

기존 노트의 필드 구성을 따름. 새로 정할 때는 이 정도가 실용적임.

```yaml
---
title: 문서 제목
status: draft        # draft / reference / archived
created: 2026-07-28
tags:
  - 프로젝트명
  - 티켓번호
---
```

### 구두점으로 끝나는 강조

CommonMark는 닫는 `**`가 "우측 플랭킹"일 때만 강조로 인정함. 이 조건이 깨지는 경우가 하나 있는데, **닫는 기호 직전이 구두점이고 직후에 문자가 바로 붙을 때**임. 괄호로 원어를 병기하는 한국어 문서에서 자주 걸림.

```markdown
정상: **권한 범위** 는 …          닫기 직전이 문자
정상: **강조**입니다               닫기 직전이 문자 — 조사가 붙어도 괜찮음
깨짐: **권한 범위(scope)**는 …     닫기 직전이 ')' + 뒤에 '는'
깨짐: **끝났습니다.**그리고         닫기 직전이 '.' + 뒤에 '그'
```

고치는 방법은 두 가지임. 닫는 기호 뒤에 공백을 넣거나(`**권한 범위(scope)** 는`), 조사를 강조 안으로 넣음(`**권한 범위(scope)는**`).

조사가 문자 뒤에 붙는 흔한 경우는 문제가 없으니 모든 강조에 공백을 넣을 필요는 없음. `check_note.py`가 실제로 깨지는 자리만 골라냄.

### 표

비교·매핑·용어 사전은 표가 가장 잘 읽힘. HTML `<table>`을 쓸 이유가 없음.

```markdown
| 항목 | 현재 | 목표 |
|---|---|---|
| 토큰 만료 | 없음 | 1시간 |
```

## SVG 도해

도해를 만들 때의 핵심은 **SVG 파일이 혼자서도 완결되게** 만드는 것임. 노트가 스타일을 제공해 주지 않는다는 전제로 작성함.

### 자립형 SVG의 필수 요소

```svg
<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 400" width="900" height="400">
<style>
svg{--ink:#14202e;--paper:#eef1f2;--card:#f8fafa;--rule:#cdd6d8;--accent:#0f6e6a}
@media (prefers-color-scheme:dark){svg{--ink:#dfe6e8;--paper:#0e1620;--card:#16212c;--rule:#2c3b47;--accent:#52b8af}}
text{font-family:ui-monospace,"SF Mono",Menlo,monospace}
.lbl{font-size:12.5px;fill:var(--ink)}
</style>
<rect x="0" y="0" width="900" height="400" fill="var(--card)"/>
<!-- 도해 내용 -->
</svg>
```

빠뜨리기 쉬운 것들:

- **`xmlns` 선언** — 독립 파일로 로드되므로 없으면 렌더링 자체가 안 됨
- **배경 `rect`** — SVG는 기본이 투명이라 노트 배경이 그대로 비침. 도해 영역을 구분하려면 배경을 깔아야 함
- **`font-family` 지정** — SVG 안의 `<text>`는 문서 폰트를 물려받지 않음. 웹폰트는 못 쓰므로 시스템 폰트 스택을 씀
- **다크 대응** — `@media (prefers-color-scheme: dark)`로 변수만 덮어씀. OS 테마를 따라가므로 대부분 Obsidian 테마와 일치함
- **`marker` id** — 화살촉 등은 파일마다 정의됨. 파일이 분리되어 있으면 id 충돌이 없어 짧은 이름을 써도 됨

색을 하드코딩하지 않고 변수로 두는 이유는 다크 대응 때문임. 라이트에서 잘 보이는 색이 다크에서 눈을 찌르는 경우가 많아, 두 벌을 따로 정하는 편이 안전함.

### 도해 레이아웃

세 가지 형태로 대부분 해결됨. 좌표 계산과 구체적인 패턴은 `references/svg-patterns.md`에 정리해 둠 — 도해를 실제로 그리기 직전에 읽으면 시간을 아낄 수 있음.

- **비교형** — 좌우로 나눠 "지금"과 "목표", "문제"와 "해결"을 대조
- **시퀀스형** — 참여자별 세로 생명선에 번호 붙은 화살표. 절차 설명에 가장 많이 쓰임
- **구조형** — 경계 박스와 구성 요소, 그 사이의 관계

참여자가 여러 명인 도해는 **참여자마다 색을 부여**하면 따라 읽기가 쉬워짐. 같은 참여자가 보내는 화살표와 그 참여자의 박스를 같은 색으로 묶는 방식임.

### 생성과 검증

`scripts/svg_scaffold.py`가 자립형 SVG의 골격(변수 정의, 다크 오버라이드, 배경, 화살촉 마커)을 만들어 줌. 도해 내용만 채우면 됨.

```bash
python scripts/svg_scaffold.py --out attachments/flow.svg --width 900 --height 500 --kind sequence
```

작성 후에는 검증 스크립트로 실수를 잡음. 임베드 링크가 실제 파일과 맞는지, SVG가 자립적인지, 강조 문법에 문제가 없는지를 한 번에 확인함.

```bash
python scripts/check_note.py "<vault>/폴더/노트.md"
```

## HTML 원본이 있을 때

이미 만들어진 HTML 문서를 옵시디언으로 옮기는 상황이라면, 원본을 그대로 붙여넣지 말고 이렇게 나눔.

- **본문** → 마크다운으로 다시 씀. 표는 마크다운 표, 강조 박스는 콜아웃, 코드는 코드블록으로 옮김
- **그림** → SVG를 파일로 추출하고 자립형으로 만든 뒤 `![[...]]`로 임베드
- **원본 HTML** → `attachments/`에 그대로 두고 노트 상단에서 링크함. "완전히 동일한 화면"이 필요할 때의 탈출구가 됨

원본에서 SVG를 뽑을 때는 CSS 변수 참조를 그대로 살릴 수 있음. 원본의 변수 정의를 SVG 내부 `<style>`로 옮겨 넣으면 `fill="var(--accent)"` 같은 속성을 고칠 필요가 없음. `scripts/extract_svg.py`가 이 작업을 함.

```bash
python scripts/extract_svg.py 원본.html --out-dir "<vault>/폴더/attachments" --prefix fig
```

## CSS 스니펫이라는 대안

HTML 구조를 꼭 유지해야 한다면 Obsidian 내장 기능인 CSS 스니펫을 쓸 수 있음. `<vault>/.obsidian/snippets/이름.css`에 CSS를 두고 설정 > 외관 > CSS 스니펫에서 켜는 방식임. 플러그인 설치가 필요 없음.

다만 다음 이유로 기본 선택으로 삼지 않음.

- 사용자가 토글을 켜야 하고, 끄면 다시 깨짐
- 스니펫이 동기화되지 않은 기기에서는 무효
- 선택자를 특정 클래스 안으로 한정하지 않으면 다른 노트까지 영향을 받음

그래도 쓸 때는 **모든 규칙을 컨테이너 클래스 안에 넣고**, 다크 모드는 `prefers-color-scheme`이 아니라 Obsidian이 붙이는 `body.theme-dark`를 기준으로 작성함. 그러지 않으면 OS는 라이트인데 Obsidian은 다크인 조합에서 어긋남.

```css
.my-guide { --ink: #14202e; }
body.theme-dark .my-guide { --ink: #dfe6e8; }
.my-guide h2 { font-size: 24px; }
```

`.html` 파일을 옵시디언 탭에서 직접 열려면 HTML Reader 계열 플러그인이 필요함. 사용자가 플러그인 설치를 원하지 않는 상황이 흔하므로, 먼저 마크다운 네이티브를 제안하고 이 방법은 선택지로만 언급함.

## 참고 파일

- `references/svg-patterns.md` — 비교형·시퀀스형·구조형 도해의 좌표 설계와 예시. 도해를 그리기 직전에 읽음
- `references/obsidian-syntax.md` — 콜아웃 종류, 임베드 변형, frontmatter 관례, 자주 걸리는 문법 함정
- `scripts/svg_scaffold.py` — 자립형 SVG 골격 생성
- `scripts/extract_svg.py` — HTML에서 SVG를 자립형 파일로 추출
- `scripts/check_note.py` — 노트와 SVG 검증
