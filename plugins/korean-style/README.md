# korean-style

- 한국 개발자가 실제로 쓰는 단어와 문장으로 한국어를 출력하게 만드는 output style plugin
- 영어 직역, 공문서 문체, 지나친 압축을 막음

## 왜 만들었나

- 뜻은 맞는데 평소에 안 쓰는 단어가 섞여서 읽다가 한 번씩 멈추게 되는 문제
- 실제로 걸렸던 자리
  - 전 트랙 기능이라 → 모든 요금제에서 쓰는 기능이라
  - 채널 1개를 보장하고 → 채널 1개를 만들고
  - 고아 항목 → 참조가 끊긴 항목
  - 테이블 4개 신설 → 테이블 4개 생성
  - 생성·조회·수정·삭제 → 생성, 조회, 수정, 삭제
  - collections 는 → collections는
- 난이도를 낮추라는 지침으로는 안 고쳐짐
  - "쉽게 써 달라"는 문장마다 확인할 방법이 없어서 몇 턴 지나면 원래대로 돌아감
  - 어려운 단어가 문제가 아니라 안 쓰는 단어가 문제라서 난이도 축과 어긋남
- 그래서 판단 기준을 하나로 고정함
  - **"이 단어를 옆자리 동료에게 말로 설명할 때 그대로 쓰겠는가"**
  - 단어를 고르는 순간마다 적용되고, 지켰는지 눈으로 확인됨

## 포함된 output style

- `plain-korean`
  - 판단 기준 한 줄과 고쳐 쓸 표현 쌍으로 구성
  - 다루는 범위
    - 영어 기술 문서 직역 (orphan, ensure, source of truth, happy path)
    - 공문서 한자어 (`신설`, `상이`, `미비`, `선행`, `잔여`, `산출`)
    - 없는 말 만들기 (`전 트랙`, `전 구간`)
    - 명사 나열 대신 조사와 어미 붙이기
    - 문장 부호 (가운뎃점, 점 연산자, 엠대시)
    - 영문 뒤 조사 붙여쓰기
  - `keep-coding-instructions: true`
    - Claude Code의 코딩 지침은 그대로 유지됨
  - 적용하지 않는 자리
    - 코드, 변수명, 함수명
    - 코드 주석, 커밋 메시지, 로그 문자열
    - 인용, 오류 메시지, 명령어, 설정 키, 파일 경로

## 포함된 검사 도구

- `scripts/check_korean.py`
  - 스타일이 막으려는 항목을 파일에서 기계적으로 찾아냄
  - 지침은 확률적으로 새지만 스크립트는 걸리면 무조건 걸림
- 사용법
  ```bash
  python3 scripts/check_korean.py 문서.md
  python3 scripts/check_korean.py 문서.md --quiet
  echo "테이블 4개 신설" | python3 scripts/check_korean.py -
  python3 scripts/check_korean.py --rules
  ```
- 판정 등급
  - 오류
    - 영어 직역, 없는 라벨, 금지 문자, 영문 뒤 떨어진 조사
    - 문맥과 관계없이 고쳐야 하는 항목
  - 주의
    - 공문서 한자어, 한 문장에 겹친 조사 `의`
    - 문맥에 따라 그대로 두어도 되는 항목
- 검사에서 빼는 자리
  - 화살표가 들어간 줄
    - 고치기 전후를 함께 보여 주는 예시로 봄
  - 백틱으로 감싼 부분
    - 코드이거나 단어 자체를 가리키는 자리로 봄
    - 조사 띄어쓰기를 볼 때는 백틱만 떼고 안쪽 글자는 남김
  - 코드 블록 전체
- 종료 코드
  - 오류가 있으면 `1`
  - 주의만 있거나 깨끗하면 `0`
  - 훅이나 CI에 걸 때 이 값을 보면 됨

## 문자 두 가지를 구분함

- 가운뎃점 `·` U+00B7
  - 한글 맞춤법의 정식 문장 부호
  - 신문과 공문서에서 쓰는 부호라서 개발 문서에서는 문체가 튐
  - 쉼표나 빗금으로 바꿈
- 점 연산자 `⋅` U+22C5
  - 가운뎃점처럼 보이지만 수학 기호
  - 검색에 걸리지 않고 폰트에 따라 위치가 어긋남
  - 어떤 경우에도 쓰지 않음
- 이미 쓴 문서에서 찾기
  ```bash
  grep -rnP '\x{22C5}' <문서 경로>
  ```

## 설치

- Claude Code
  ```bash
  /plugin marketplace add eyedroot/eyedroot-marketplace
  /plugin install korean-style@eyedroot
  /output-style
  ```
- `/output-style`에서 `plain-korean`을 고르면 적용됨
- `~/.claude/settings.json`에 직접 적을 수도 있음
  ```json
  { "outputStyle": "korean-style:plain-korean" }
  ```

## 호환성

- output style은 Claude Code 기능이라 codex CLI에는 적용되지 않음
- codex에도 같은 규칙을 걸려면 `~/.agents/AGENTS.md`에 옮겨 적어야 함
- 검사 스크립트는 python3만 있으면 어디서든 돌아감

## 어휘 목록을 늘리는 방법

- 실제로 다시 나온 표현만 추가함
  - 짐작으로 넣은 항목은 확인이 안 되고 목록만 길어짐
- 두 곳을 같이 고침
  - `output-styles/plain-korean.md`의 예시 쌍
  - `scripts/check_korean.py`의 `LITERAL_TRANSLATIONS` 또는 `OFFICIALESE`
- 항목 수는 스무 개 안쪽으로 유지
  - 목록이 길어지면 한 번에 확인이 안 되어서, 적어 두어도 그냥 지나가게 됨
