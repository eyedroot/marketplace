#!/usr/bin/env python3
"""한국어 글에서 조여 있는 문장과 어색한 표기를 찾는다.

plain-korean 지침은 두 가지를 다룬다. 공적인 문서의 어휘를 끌어오는 것과 뜻을
한 단어에 몰아넣는 것이다. 이 스크립트는 뒤쪽을 센다. 문장 길이, 한 문장에 담긴
항목 수, 겹쳐 쓴 조사처럼 셀 수 있는 신호를 오류로 본다.

앞쪽인 어휘는 세어도 몇 개밖에 잡히지 않는다. 막을 단어를 외우는 방식으로는
해결되지 않기 때문에, 어휘는 주의로만 알려 주고 판단은 읽는 사람에게 맡긴다.
검사를 통과했다고 해서 글이 자연스러워진 것은 아니다.

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

# 문장이 두 가지 이상을 담고 있는지 보는 눈금
SENTENCE_LENGTH_ERROR = 120
SENTENCE_LENGTH_WARN = 80
COMMA_WARN = 6
CLAUSE_COMMA_MIN = 3    # 나열 도중에 절이 바뀌는지 볼 때의 최소 쉼표 수
CLAUSE_SUBJECT_MIN = 3  # 한 문장에 주어 표지가 몇 개부터 문제인지
JOSA_UI_WARN = 3

# 판단이 어긋났던 자리. 금지어 목록이 아니라 사례이므로 전부 주의로만 알린다.
VOCABULARY = [
    (r"고아", "고아", "참조가 끊긴 항목, 부모 행이 사라진 행", "영어 비유를 그대로 옮김"),
    (r"보장(하|한|할|합|해|했)", "보장하다", "만든다, 없으면 만든다", "원문 동사의 사전 뜻을 고름"),
    (r"진실의\s*원천", "진실의 원천", "기준이 되는 값", "영어 비유를 그대로 옮김"),
    (r"행복\s*경로", "행복 경로", "정상 흐름", "영어 비유를 그대로 옮김"),
    (r"온전성\s*검사", "온전성 검사", "간단히 확인하기", "영어 비유를 그대로 옮김"),
    (r"신설", "신설", "생성, 추가", "공적인 문서의 어휘"),
    (r"상이(하|한|할|합|했)", "상이하다", "다르다", "공적인 문서의 어휘"),
    (r"미비(하|한|할|합|했)", "미비하다", "빠져 있다", "공적인 문서의 어휘"),
    (r"선행(되|돼|하)", "선행되다", "먼저 한다", "공적인 문서의 어휘"),
    (r"기인(하|한|합|했)", "기인하다", "때문에 생긴다", "공적인 문서의 어휘"),
    (r"잔여", "잔여", "남은", "공적인 문서의 어휘"),
    (r"소관", "소관", "맡은 곳", "공적인 문서의 어휘"),
    (r"산출(하|한|할|합|해|했)", "산출하다", "계산한다", "공적인 문서의 어휘"),
    (r"사전에", "사전에", "미리", "공적인 문서의 어휘"),
    (r"에\s*한하여|에\s*한해", "에 한하여", "~만", "공적인 문서의 어휘"),
    (r"수행(하|한|할|합|해|했)", "수행하다", "한다, 실행한다", "습관적으로 붙는 군더더기"),
    (r"진행(하|한|할|합|해|했)", "진행하다", "한다", "습관적으로 붙는 군더더기"),
    (r"도출(하|한|할|합|해|했)", "도출하다", "뽑는다, 구한다", "공적인 문서의 어휘"),
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
SUBJECT_MARKER = re.compile(r"(?<=[가-힣A-Za-z0-9)\]\ufffc])(?:은|는|이|가)(?=\s)")
INLINE_CODE = re.compile(r"`[^`]*`")
FENCE = re.compile(r"^\s*(```|~~~)")
LIST_MARKER = re.compile(r"^\s*(?:[-*+]|\d+\.)\s+")
MARKUP = re.compile(r"\*\*|__|^#+\s*|^>\s*")
ARROW = "→"


GROUP_THRESHOLD = 4  # 같은 항목이 이만큼 반복되면 한 줄로 묶어 보여 준다


class Report:
    """찾은 것을 모은다.

    같은 표기 실수가 수십 번 반복되면 목록이 그것만으로 채워져서 문장 구조
    문제가 묻힌다. 반복되는 항목은 묶어서 한 줄로 보여 준다.
    """

    def __init__(self, quiet=False):
        self.errors = []
        self.warnings = []
        self.quiet = quiet

    def error(self, line_no, msg, group=None):
        self.errors.append((line_no, msg, group))

    def warn(self, line_no, msg, group=None):
        self.warnings.append((line_no, msg, group))

    @staticmethod
    def _emit(found, label, color):
        grouped = {}
        for line_no, msg, group in found:
            grouped.setdefault(group, []).append((line_no, msg))
        singles = []
        for group, rows in grouped.items():
            if group is None or len(rows) < GROUP_THRESHOLD:
                singles.extend(rows)
                continue
            lines = sorted({n for n, _ in rows})
            shown = ", ".join(f"{n}행" for n in lines[:6])
            more = f" 외 {len(lines) - 6}곳" if len(lines) > 6 else ""
            print(f"{color}  {label}{RESET}  묶음  {group} {len(rows)}건 ({shown}{more})")
        for line_no, msg in sorted(singles):
            print(f"{color}  {label}{RESET} {line_no:>4}행  {msg}")
        return len(found)

    def render(self, source, stats):
        self._emit(self.warnings, "주의", YELLOW)
        self._emit(self.errors, "오류", RED)
        if self.errors or self.warnings:
            print()
        if not self.quiet:
            print(f"{DIM}{source}{RESET}")
            print(f"{DIM}  문장 {stats['sentences']}개, 평균 {stats['mean']}자, "
                  f"가장 긴 문장 {stats['longest']}자{RESET}")
        if self.errors:
            print(f"{RED}오류 {len(self.errors)}건{RESET}, 주의 {len(self.warnings)}건")
            print(f"{DIM}어휘가 자연스러운지는 세어 주지 못하니 직접 읽어야 합니다{RESET}")
            return 1
        if self.warnings:
            print(f"{YELLOW}주의 {len(self.warnings)}건{RESET}, 문맥을 보고 판단하세요")
            return 0
        print(f"{GREEN}세어서 걸리는 것은 없습니다{RESET}")
        print(f"{DIM}어휘가 자연스러운지는 세어 주지 못하니 직접 읽어야 합니다{RESET}")
        return 0


def mask_inline_code(line):
    """백틱으로 감싼 부분을 자리 표시 문자로 바꾼다. 어휘와 부호 검사에 쓴다."""
    return INLINE_CODE.sub("￼", line)


def unwrap_inline_code(line):
    """백틱만 떼고 안쪽 글자는 남긴다. 조사 띄어쓰기 검사에 쓴다.

    백틱 자리를 공백으로 바꾸면 `HTML <div>가`처럼 붙여 쓴 조사가 떨어져
    보이므로, 띄어쓰기를 볼 때는 안쪽 글자를 그대로 두어야 한다.
    """
    return line.replace("`", "")


def split_sentences(line):
    body = MARKUP.sub("", LIST_MARKER.sub("", line)).strip()
    if not body:
        return []
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", body) if s.strip()]


def check_sentence_shape(line, line_no, rep, lengths):
    for sentence in split_sentences(line):
        size = len(sentence)
        lengths.append(size)
        head = sentence[:40]
        if size >= SENTENCE_LENGTH_ERROR:
            rep.error(line_no, f"한 문장이 {size}자입니다. 두 가지 이상을 담고 있는지 보고 나누세요: {head}...")
        elif size >= SENTENCE_LENGTH_WARN:
            rep.warn(line_no, f"한 문장이 {size}자입니다: {head}...")

        commas = sentence.count(",")
        subjects = len(SUBJECT_MARKER.findall(sentence))
        if commas >= CLAUSE_COMMA_MIN and subjects >= CLAUSE_SUBJECT_MIN:
            rep.error(line_no, f"나열 도중에 절이 바뀝니다. 주어가 {subjects}개라서 어디까지가 한 묶음인지 "
                               f"읽어서는 알 수 없으니 문장을 나누세요: {head}...")
        elif commas >= COMMA_WARN:
            rep.warn(line_no, f"한 문장에 쉼표가 {commas}개입니다. 한 가지만 말하고 있는지 보세요: {head}...")

        if len(JOSA_UI.findall(sentence)) >= JOSA_UI_WARN:
            rep.warn(line_no, "한 문장에 조사 '의'가 세 번 넘게 나옵니다. 명사를 늘어놓고 있는지 보세요")


def check_vocabulary(line, line_no, rep):
    for pattern, shown, replacement, reason in VOCABULARY:
        if re.search(pattern, line):
            rep.warn(line_no, f"{shown} → {replacement} ({reason})", group=f"{shown} → {replacement}")


def check_punctuation(line, line_no, rep):
    if DOT_OPERATOR in line:
        rep.error(line_no, "점 연산자(U+22C5)가 있습니다. 가운뎃점이 아니라 수학 기호라서 검색에 걸리지 않습니다")
    if MIDDLE_DOT in line:
        rep.error(line_no, "가운뎃점(U+00B7)이 있습니다. 쉼표로 갈아 끼우기만 하면 층이 무너지니 문장을 나누세요",
                  group="가운뎃점. 쉼표로 갈아 끼우지 말고 문장을 나누세요")
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
        rep.error(line_no, f"영문 뒤 조사가 떨어져 있습니다: {chunk.strip()} → {re.sub(r'[ \t]+', '', chunk)}",
                  group="영문 뒤 조사가 떨어져 있습니다")


def check(text, source, quiet=False):
    rep = Report(quiet)
    in_fence = False
    lengths = []
    for line_no, raw in enumerate(text.splitlines(), start=1):
        if FENCE.match(raw):
            in_fence = not in_fence
            continue
        if in_fence or ARROW in raw:
            continue
        line = mask_inline_code(raw)
        if not line.strip():
            continue
        check_sentence_shape(unwrap_inline_code(raw), line_no, rep, lengths)
        check_vocabulary(line, line_no, rep)
        check_punctuation(line, line_no, rep)
        check_spacing(unwrap_inline_code(raw), line_no, rep)
    stats = {
        "sentences": len(lengths),
        "mean": sum(lengths) // len(lengths) if lengths else 0,
        "longest": max(lengths) if lengths else 0,
    }
    return rep.render(source, stats)


def print_rules():
    print(f"{RED}오류{RESET}  문장이 조여 있는 신호")
    print(f"      한 문장 {SENTENCE_LENGTH_ERROR}자 이상")
    print(f"      쉼표 {CLAUSE_COMMA_MIN}개 이상인 문장에 주어 표지가 {CLAUSE_SUBJECT_MIN}개 이상")
    print(f"{RED}오류{RESET}  표기")
    print("      점 연산자(U+22C5), 가운뎃점(U+00B7), 엠대시, 이모지")
    print("      영문 뒤에 떨어진 조사")
    print(f"{YELLOW}주의{RESET}  문장 길이 {SENTENCE_LENGTH_WARN}자 이상, 쉼표 {COMMA_WARN}개 이상, 조사 '의' {JOSA_UI_WARN}회 이상")
    print(f"{YELLOW}주의{RESET}  판단이 어긋났던 어휘 사례")
    for _, shown, replacement, reason in VOCABULARY:
        print(f"      {shown} → {replacement}  {DIM}{reason}{RESET}")
    print()
    print(f"{DIM}어휘는 목록으로 막을 수 없어서 사례만 둔다. 목록에 없어도 같은 기준으로 본다.{RESET}")


def main():
    parser = argparse.ArgumentParser(description="한국어 글에서 조여 있는 문장과 어색한 표기를 찾는다")
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
