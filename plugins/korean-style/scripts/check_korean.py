#!/usr/bin/env python3
"""한국어 문서에서 어색한 어휘와 표기를 찾는다.

plain-korean 출력 스타일이 막으려는 항목을 기계적으로 확인한다. 영어를 그대로
옮긴 어휘, 공문서에서 쓰는 한자어, 가운뎃점과 점 연산자, 엠대시, 영문 뒤에
떨어진 조사, 이모지를 찾아낸다.

검사에서 빼는 자리
    화살표가 있는 줄   고치기 전후를 함께 보여 주는 예시로 본다
    백틱으로 감싼 부분  코드이거나 단어 자체를 가리키는 자리로 본다
    코드 블록 전체

사용법:
    python check_korean.py 문서.md
    python check_korean.py 문서.md --quiet
    echo "테이블 4개 신설" | python check_korean.py -
    python check_korean.py --rules
"""

import argparse
import re
import sys
from pathlib import Path

RESET, RED, YELLOW, GREEN, DIM = "\033[0m", "\033[31m", "\033[33m", "\033[32m", "\033[2m"

# (정규식, 걸리는 말, 바꿀 말, 이유)
LITERAL_TRANSLATIONS = [
    (r"고아", "고아", "참조가 끊긴 항목, 부모 행이 사라진 행", "orphan을 그대로 옮긴 말"),
    (r"보장(하|한|할|합|해|했)", "보장하다", "만든다, 없으면 만든다", "ensure를 그대로 옮긴 말"),
    (r"진실의\s*원천", "진실의 원천", "기준이 되는 값", "source of truth를 그대로 옮긴 말"),
    (r"행복\s*경로", "행복 경로", "정상 흐름", "happy path를 그대로 옮긴 말"),
    (r"온전성\s*검사", "온전성 검사", "간단히 확인하기", "sanity check를 그대로 옮긴 말"),
    (r"최선\s*노력", "최선 노력", "되는 만큼만 처리하는 방식", "best effort를 그대로 옮긴 말"),
]

INVENTED_LABELS = [
    (r"전\s*트랙", "전 트랙", "모든 요금제에서, 어디서나", "제품이 쓰지 않는 라벨"),
    (r"전\s*구간", "전 구간", "처음부터 끝까지", "제품이 쓰지 않는 라벨"),
]

OFFICIALESE = [
    (r"신설", "신설", "생성, 추가", "공문서 문체"),
    (r"상이(하|한|할|합|했)", "상이하다", "다르다", "공문서 문체"),
    (r"미비(하|한|할|합|했)", "미비하다", "빠져 있다", "공문서 문체"),
    (r"선행(되|돼|하)", "선행되다", "먼저 한다", "공문서 문체"),
    (r"기인(하|한|합|했)", "기인하다", "때문에 생긴다", "공문서 문체"),
    (r"잔여", "잔여", "남은", "공문서 문체"),
    (r"산출(하|한|할|합|해|했)", "산출하다", "계산한다", "공문서 문체"),
    (r"사전에", "사전에", "미리", "공문서 문체"),
    (r"에\s*한하여|에\s*한해", "에 한하여", "~만", "공문서 문체"),
    (r"수행(하|한|할|합|해|했)", "수행하다", "한다, 실행한다", "습관적으로 붙는 군더더기"),
    (r"진행(하|한|할|합|해|했)", "진행하다", "한다", "습관적으로 붙는 군더더기"),
    (r"도출(하|한|할|합|해|했)", "도출하다", "뽑는다, 구한다", "공문서 문체"),
]

PARTICLES = [
    "입니다", "이므로", "이며", "이고", "이라", "에서", "에게", "부터", "까지",
    "으로", "이다", "은", "는", "이", "가", "을", "를", "와", "과", "의", "에", "로", "도",
]
PARTICLE_SPACING = re.compile(
    r"(?:[A-Za-z_][A-Za-z0-9_.\-]*|\)|\])[ \t]+(" + "|".join(PARTICLES) + r")(?=[\s,.;:!?)\]}」』\"']|$)"
)

DOT_OPERATOR = "⋅"
MIDDLE_DOT = "·"
EM_DASHES = ("—", "―")
EMOJI = re.compile("[\U0001F000-\U0001FAFF]|️")
DINGBAT = re.compile("[☀-➿]")
JOSA_UI = re.compile(r"의(?=[\s,)])")
INLINE_CODE = re.compile(r"`[^`]*`")
FENCE = re.compile(r"^\s*(```|~~~)")
ARROW = "→"


class Report:
    def __init__(self, quiet=False):
        self.errors = []
        self.warnings = []
        self.quiet = quiet

    def error(self, line_no, msg):
        self.errors.append((line_no, msg))

    def warn(self, line_no, msg):
        self.warnings.append((line_no, msg))

    def render(self, source, checked_lines, skipped_lines):
        for line_no, msg in sorted(self.warnings):
            print(f"{YELLOW}  주의{RESET} {line_no:>4}행  {msg}")
        for line_no, msg in sorted(self.errors):
            print(f"{RED}  오류{RESET} {line_no:>4}행  {msg}")
        if self.errors or self.warnings:
            print()
        if not self.quiet:
            print(f"{DIM}{source}: {checked_lines}행 검사, {skipped_lines}행 건너뜀{RESET}")
        if self.errors:
            print(f"{RED}오류 {len(self.errors)}건{RESET}, 주의 {len(self.warnings)}건")
            return 1
        if self.warnings:
            print(f"{YELLOW}주의 {len(self.warnings)}건{RESET}, 문맥을 보고 판단하세요")
            return 0
        print(f"{GREEN}걸리는 표현이 없습니다{RESET}")
        return 0


def mask_inline_code(line):
    """백틱으로 감싼 부분을 자리 표시 문자로 바꾼다. 어휘와 부호 검사에 쓴다."""
    return INLINE_CODE.sub("\ufffc", line)


def unwrap_inline_code(line):
    """백틱만 떼고 안쪽 글자는 남긴다. 조사 띄어쓰기 검사에 쓴다.

    백틱 자리를 공백으로 바꾸면 `HTML <div>가`처럼 붙여 쓴 조사가 떨어져
    보이므로, 띄어쓰기를 볼 때는 안쪽 글자를 그대로 두어야 한다.
    """
    return line.replace("`", "")


def check_vocabulary(line, line_no, rep):
    for pattern, shown, replacement, reason in LITERAL_TRANSLATIONS + INVENTED_LABELS:
        if re.search(pattern, line):
            rep.error(line_no, f"{shown} → {replacement} ({reason})")
    for pattern, shown, replacement, reason in OFFICIALESE:
        if re.search(pattern, line):
            rep.warn(line_no, f"{shown} → {replacement} ({reason})")


def check_punctuation(line, line_no, rep):
    if DOT_OPERATOR in line:
        rep.error(line_no, "점 연산자(U+22C5)가 있습니다. 가운뎃점이 아니라 수학 기호라서 검색에 걸리지 않습니다. 쉼표로 바꾸세요")
    if MIDDLE_DOT in line:
        rep.error(line_no, "가운뎃점(U+00B7)이 있습니다. 쉼표나 빗금으로 바꾸세요")
    for dash in EM_DASHES:
        if dash in line:
            rep.error(line_no, "엠대시가 있습니다. 콜론이나 접속사로 바꾸세요")
            break
    if EMOJI.search(line):
        rep.error(line_no, "이모지가 있습니다")
    elif DINGBAT.search(line):
        rep.warn(line_no, "기호 문자가 있습니다. 이모지로 보이면 빼세요")


def check_spacing(line, line_no, rep):
    for match in PARTICLE_SPACING.finditer(line):
        chunk = match.group(0)
        fixed = re.sub(r"[ \t]+", "", chunk)
        rep.error(line_no, f"영문 뒤 조사가 떨어져 있습니다: {chunk.strip()} → {fixed}")


def check_ui_density(line, line_no, rep):
    for sentence in re.split(r"(?<=[.!?])\s+", line):
        if len(JOSA_UI.findall(sentence)) >= 3:
            rep.warn(line_no, "한 문장에 조사 '의'가 세 번 넘게 나옵니다. 명사를 늘어놓고 있는지 확인하세요")


def check(text, source, quiet=False):
    rep = Report(quiet)
    in_fence = False
    checked = 0
    skipped = 0
    for line_no, raw in enumerate(text.splitlines(), start=1):
        if FENCE.match(raw):
            in_fence = not in_fence
            skipped += 1
            continue
        if in_fence or ARROW in raw:
            skipped += 1
            continue
        line = mask_inline_code(raw)
        if not line.strip():
            continue
        checked += 1
        check_vocabulary(line, line_no, rep)
        check_punctuation(line, line_no, rep)
        check_spacing(unwrap_inline_code(raw), line_no, rep)
        check_ui_density(line, line_no, rep)
    return rep.render(source, checked, skipped)


def print_rules():
    print(f"{RED}오류{RESET}  영어를 그대로 옮긴 말")
    for _, shown, replacement, reason in LITERAL_TRANSLATIONS:
        print(f"      {shown} → {replacement}  {DIM}{reason}{RESET}")
    print(f"{RED}오류{RESET}  제품이 쓰지 않는 라벨")
    for _, shown, replacement, reason in INVENTED_LABELS:
        print(f"      {shown} → {replacement}  {DIM}{reason}{RESET}")
    print(f"{YELLOW}주의{RESET}  공문서에서 쓰는 한자어")
    for _, shown, replacement, reason in OFFICIALESE:
        print(f"      {shown} → {replacement}  {DIM}{reason}{RESET}")
    print(f"{RED}오류{RESET}  표기")
    print("      점 연산자(U+22C5), 가운뎃점(U+00B7), 엠대시, 이모지")
    print("      영문 뒤에 떨어진 조사")


def main():
    parser = argparse.ArgumentParser(description="한국어 문서에서 어색한 어휘와 표기를 찾는다")
    parser.add_argument("path", nargs="?", help="검사할 파일. -를 주면 표준 입력을 읽는다")
    parser.add_argument("--quiet", action="store_true", help="요약 줄을 줄인다")
    parser.add_argument("--rules", action="store_true", help="검사 항목을 보여 준다")
    args = parser.parse_args()

    if args.rules:
        print_rules()
        return 0
    if not args.path:
        parser.error("검사할 파일을 주거나 --rules를 쓰세요")
    if args.path == "-":
        return check(sys.stdin.read(), "표준 입력", args.quiet)

    target = Path(args.path)
    if not target.is_file():
        print(f"{RED}오류{RESET} 파일이 없습니다: {target}")
        return 1
    return check(target.read_text(encoding="utf-8"), str(target), args.quiet)


if __name__ == "__main__":
    sys.exit(main())
