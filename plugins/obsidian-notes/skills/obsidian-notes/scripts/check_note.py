#!/usr/bin/env python3
"""Obsidian 노트와 임베드된 SVG를 검증한다.

옵시디언은 노트 안의 <style> 태그를 제거하므로, 인라인 SVG가 CSS 변수를
참조하면 값이 무효가 되어 검은 박스로 보인다. 이 스크립트는 그런 실수와
자주 걸리는 문법 함정을 노트 저장 후 한 번에 잡아낸다.

사용법:
    python check_note.py "<vault>/폴더/노트.md"
    python check_note.py "<vault>/폴더/노트.md" --quiet   # 문제만 출력
"""

import argparse
import re
import sys
from pathlib import Path

RESET, RED, YELLOW, GREEN, DIM = "\033[0m", "\033[31m", "\033[33m", "\033[32m", "\033[2m"


class Report:
    def __init__(self, quiet=False):
        self.errors = []
        self.warnings = []
        self.oks = []
        self.quiet = quiet

    def error(self, msg):
        self.errors.append(msg)

    def warn(self, msg):
        self.warnings.append(msg)

    def ok(self, msg):
        self.oks.append(msg)

    def render(self):
        if not self.quiet:
            for m in self.oks:
                print(f"{GREEN}  OK{RESET}   {m}")
        for m in self.warnings:
            print(f"{YELLOW}  주의{RESET} {m}")
        for m in self.errors:
            print(f"{RED}  오류{RESET} {m}")
        print()
        if self.errors:
            print(f"{RED}오류 {len(self.errors)}건{RESET}, 주의 {len(self.warnings)}건")
            return 1
        if self.warnings:
            print(f"{YELLOW}주의 {len(self.warnings)}건{RESET} — 확인 후 넘어가도 됩니다")
            return 0
        print(f"{GREEN}문제 없음{RESET}")
        return 0


def check_inline_svg(text, rep):
    """노트 본문에 인라인 SVG가 있으면 경고한다 (style 태그가 제거되어 깨짐)."""
    if re.search(r"<svg\b", text):
        rep.error(
            "본문에 인라인 <svg>가 있습니다. 옵시디언은 노트의 <style>을 제거하므로 "
            "CSS 변수를 쓰는 SVG는 검게 보입니다. 별도 .svg 파일로 분리해 ![[...]]로 임베드하세요."
        )
    if re.search(r"<style\b", text):
        rep.error(
            "본문에 <style> 블록이 있습니다. 읽기 모드에서 제거되어 무효입니다. "
            "마크다운 네이티브로 옮기거나 .obsidian/snippets/ 로 이동하세요."
        )


def check_embeds(text, note_path, rep):
    """![[...]] 임베드 대상이 실제로 존재하는지 확인한다."""
    embeds = re.findall(r"!\[\[([^\]|]+?)(?:\|[^\]]*)?\]\]", text)
    if not embeds:
        return []
    note_dir = note_path.parent
    # vault 루트를 찾아 전역 탐색도 시도 (옵시디언은 vault 어디에 있든 파일명으로 해석)
    vault_root = note_dir
    for parent in [note_dir, *note_dir.parents]:
        if (parent / ".obsidian").is_dir():
            vault_root = parent
            break

    found = []
    for target in embeds:
        target = target.strip()
        candidates = [
            note_dir / target,
            note_dir / "attachments" / target,
            note_dir / "Attachments" / target,
        ]
        hit = next((c for c in candidates if c.is_file()), None)
        if hit is None and vault_root != note_dir:
            matches = list(vault_root.rglob(Path(target).name))
            hit = matches[0] if matches else None
        if hit:
            rep.ok(f"임베드 대상 존재: {target}")
            found.append(hit)
        else:
            rep.error(f"임베드 대상을 찾을 수 없음: {target}")
    return found


def check_svg_file(path, rep):
    """SVG가 자립적인지 확인한다: xmlns, 변수 정의, 다크 대응, 폰트."""
    try:
        raw = path.read_text(encoding="utf-8")
    except Exception as e:
        rep.error(f"{path.name} 읽기 실패: {e}")
        return

    # 주석 안의 예시 코드가 실제 참조로 잡히지 않게 걷어낸다
    s = re.sub(r"<!--.*?-->", "", raw, flags=re.S)
    name = path.name

    if "xmlns=" not in s:
        rep.error(f"{name}: xmlns 선언이 없습니다. 독립 파일로는 렌더링되지 않습니다.")

    used = set(re.findall(r"var\((--[a-z0-9-]+)\)", s))
    defined = set(re.findall(r"(--[a-z0-9-]+)\s*:", s))
    missing = used - defined
    if missing:
        rep.error(
            f"{name}: 정의되지 않은 CSS 변수 {sorted(missing)} — "
            "SVG 내부 <style>에 정의하세요. 없으면 fill이 검정으로 칠해집니다."
        )
    elif used:
        rep.ok(f"{name}: 변수 {len(used)}개 모두 자체 정의됨")

    if used and "prefers-color-scheme" not in s:
        rep.warn(f"{name}: 다크 모드 오버라이드가 없습니다. 어두운 테마에서 대비가 떨어질 수 있습니다.")

    if re.search(r"<text\b", s) and "font-family" not in s:
        rep.warn(f"{name}: <text>가 있으나 font-family 지정이 없습니다. SVG는 문서 폰트를 물려받지 않습니다.")

    if "viewBox" not in s:
        rep.warn(f"{name}: viewBox가 없어 크기 조절이 부자연스러울 수 있습니다.")

    # 화살촉 마커 참조 무결성
    marker_ids = set(re.findall(r'<marker[^>]*\bid="([^"]+)"', s))
    marker_refs = set(re.findall(r"url\(#([^)]+)\)", s))
    dangling = marker_refs - marker_ids - set(re.findall(r'\bid="([^"]+)"', s))
    if dangling:
        rep.error(f"{name}: 정의되지 않은 참조 url(#...) {sorted(dangling)}")


#  닫는 ** 가 유효하려면 우측 플랭킹(right-flanking)이어야 한다.
#  직전이 구두점이고 직후가 문자면 플랭킹이 성립하지 않아 강조가 적용되지 않는다.
#  예: **범위(scope)**는  → 깨짐 (직전 ')')
#      **범위**는          → 정상 (직전 '위')
EMPHASIS_BREAK = re.compile(r"\*\*[^*\n]*[.,!?;:)\]}\"'’”]\*\*(?=[0-9A-Za-z가-힣])")


def check_emphasis(text, rep):
    """구두점으로 끝나는 강조 뒤에 문자가 붙어 렌더링이 깨지는 자리를 찾는다."""
    body = re.sub(r"```.*?```", "", text, flags=re.S)  # 코드블록 제외
    hits = []
    for m in EMPHASIS_BREAK.finditer(body):
        line_no = body[: m.start()].count("\n") + 1
        hits.append((line_no, m.group(0)[-30:]))
    if hits:
        sample = "; ".join(f"{ln}행 …{frag}" for ln, frag in hits[:4])
        more = f" 외 {len(hits) - 4}건" if len(hits) > 4 else ""
        rep.warn(
            f"강조가 깨질 수 있는 곳 {len(hits)}건 ({sample}{more}). "
            "닫는 ** 직전이 구두점이고 뒤에 문자가 붙으면 강조가 적용되지 않습니다. "
            "뒤에 공백을 넣거나 조사를 강조 안에 포함하세요."
        )
    else:
        rep.ok("강조 문법 문제 없음")


def check_frontmatter(text, rep):
    if not text.startswith("---\n"):
        rep.warn("frontmatter가 없습니다. title/tags를 넣으면 검색과 분류가 쉬워집니다.")
        return
    end = text.find("\n---", 4)
    if end == -1:
        rep.error("frontmatter가 닫히지 않았습니다 (--- 누락).")
        return
    fm = text[4:end]
    if re.search(r"^\s*<", fm, re.M) or "</" in fm:
        rep.error("frontmatter 안에 HTML이 섞여 있습니다. 본문과 분리하세요.")
    else:
        rep.ok("frontmatter 정상")


def main():
    ap = argparse.ArgumentParser(description="Obsidian 노트와 임베드 SVG 검증")
    ap.add_argument("note", help="검증할 .md 파일 경로")
    ap.add_argument("--quiet", action="store_true", help="문제만 출력")
    args = ap.parse_args()

    note_path = Path(args.note).expanduser()
    if not note_path.is_file():
        print(f"{RED}파일을 찾을 수 없음:{RESET} {note_path}")
        return 2

    text = note_path.read_text(encoding="utf-8")
    rep = Report(quiet=args.quiet)

    print(f"\n{DIM}검증 대상{RESET} {note_path.name}  ({len(text):,} bytes)\n")

    check_frontmatter(text, rep)
    check_inline_svg(text, rep)
    check_emphasis(text, rep)
    svg_files = [p for p in check_embeds(text, note_path, rep) if p.suffix.lower() == ".svg"]
    for svg in svg_files:
        check_svg_file(svg, rep)

    return rep.render()


if __name__ == "__main__":
    sys.exit(main())
