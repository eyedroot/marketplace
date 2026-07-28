#!/usr/bin/env python3
"""HTML 문서의 인라인 SVG를 자립형 .svg 파일로 추출한다.

원본 HTML의 <style>에 정의된 CSS 변수를 각 SVG 내부로 옮겨 넣으므로,
SVG 안의 fill="var(--accent)" 같은 속성을 고치지 않아도 그대로 동작한다.
다크 모드는 prefers-color-scheme 블록을 함께 옮겨 유지한다.

사용법:
    python extract_svg.py 원본.html --out-dir "<vault>/폴더/attachments"
    python extract_svg.py 원본.html --out-dir ./attachments --prefix fig --names flow,pkce
"""

import argparse
import re
import sys
from pathlib import Path

# SVG 안에서 쓰일 만한 클래스 규칙은 원본 CSS에서 함께 옮긴다.
SVG_CLASS_HINT = re.compile(r"(?:^|\s|,)(?:svg\s+)?(text|\.lbl[a-z-]*|\.num|\.head)\b")


def parse_css_blocks(html):
    """원본 <style>에서 변수 정의와 SVG 관련 규칙을 추출한다."""
    styles = re.findall(r"<style[^>]*>(.*?)</style>", html, re.S)
    css = "\n".join(styles)
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)

    light_vars, dark_vars = {}, {}

    # 라이트: :root 또는 [data-theme="light"] 선언
    for m in re.finditer(r"(?::root|\[data-theme=[\"']light[\"']\])[^{]*\{([^}]*)\}", css):
        for name, val in re.findall(r"(--[a-z0-9-]+)\s*:\s*([^;]+)", m.group(1)):
            light_vars.setdefault(name, val.strip())

    # 다크: prefers-color-scheme 블록과 [data-theme="dark"]
    dark_src = ""
    for m in re.finditer(r"@media\s*\([^)]*prefers-color-scheme\s*:\s*dark[^)]*\)\s*\{", css):
        start = m.end()
        depth, i = 1, start
        while i < len(css) and depth:
            depth += (css[i] == "{") - (css[i] == "}")
            i += 1
        dark_src += css[start : i - 1]
    for m in re.finditer(r"\[data-theme=[\"']dark[\"']\][^{]*\{([^}]*)\}", css):
        dark_src += m.group(1)
    for name, val in re.findall(r"(--[a-z0-9-]+)\s*:\s*([^;]+)", dark_src):
        dark_vars.setdefault(name, val.strip())

    # SVG 텍스트 클래스 규칙
    svg_rules = []
    for sel, body in re.findall(r"([^{}]+)\{([^{}]*)\}", css):
        sel_clean = sel.strip()
        if SVG_CLASS_HINT.search(sel_clean) and "--" not in body:
            # 'svg text' -> 'text', '.oauth-guide svg .lbl' -> '.lbl'
            simple = re.sub(r"^.*\bsvg\s+", "", sel_clean).strip()
            simple = re.sub(r"^\.[a-z0-9-]+\s+", "", simple).strip()
            if simple:
                svg_rules.append(f"{simple}{{{body.strip()}}}")

    return light_vars, dark_vars, svg_rules


def strip_alpha(color):
    """8자리 hex의 알파를 제거한다. 투명 배경 위에서 예측하기 어려워지는 것을 막는다."""
    m = re.fullmatch(r"#([0-9a-fA-F]{6})[0-9a-fA-F]{2}", color.strip())
    return f"#{m.group(1)}" if m else color


def build_style(light, dark, rules, used_vars):
    keep_l = {k: v for k, v in light.items() if k in used_vars}
    keep_d = {k: strip_alpha(v) for k, v in dark.items() if k in used_vars}
    # 라이트에만 있고 다크에 없는 변수는 그대로 상속된다 (문제 없음)
    lines = ["<style>"]
    if keep_l:
        decls = ";".join(f"{k}:{v}" for k, v in sorted(keep_l.items()))
        lines.append(f"svg{{{decls}}}")
    if keep_d:
        decls = ";".join(f"{k}:{v}" for k, v in sorted(keep_d.items()))
        lines.append(f"@media (prefers-color-scheme:dark){{svg{{{decls}}}}}")
    if not any("font-family" in r for r in rules):
        lines.append('text{font-family:ui-monospace,"SF Mono",SFMono-Regular,Menlo,Consolas,monospace}')
    lines.extend(rules)
    lines.append("</style>")
    return "\n".join(lines)


def slugify(text, fallback):
    s = re.sub(r"[^a-zA-Z0-9가-힣]+", "-", text or "").strip("-").lower()
    return s[:48] or fallback


def guess_name(html, svg, index, auto=False):
    """파일명을 정한다. 기본은 fig1, fig2… 로 짧고 예측 가능하게 둔다.

    --auto-name을 주면 aria-label이나 figcaption에서 추론하는데, 한국어 설명이
    그대로 파일명이 되어 길어지기 쉬우므로 기본값으로 삼지 않는다.
    """
    if not auto:
        return f"fig{index}"
    label = re.search(r'aria-label="([^"]+)"', svg)
    if label:
        return slugify(label.group(1), f"fig{index}")[:32].rstrip("-")
    pos = html.find(svg)
    tail = html[pos + len(svg) : pos + len(svg) + 400]
    cap = re.search(r"<figcaption[^>]*>(.*?)</figcaption>", tail, re.S)
    if cap:
        plain = re.sub(r"<[^>]+>", "", cap.group(1))
        return slugify(plain, f"fig{index}")[:32].rstrip("-")
    return f"fig{index}"


def main():
    ap = argparse.ArgumentParser(description="HTML의 인라인 SVG를 자립형 파일로 추출")
    ap.add_argument("html", help="원본 HTML 경로")
    ap.add_argument("--out-dir", required=True, help="저장할 디렉터리 (보통 vault의 attachments)")
    ap.add_argument("--prefix", default="", help="파일명 접두사 (예: oauth)")
    ap.add_argument("--names", default="", help="쉼표로 구분한 파일명 목록 (순서대로 적용)")
    ap.add_argument("--no-background", action="store_true", help="배경 rect를 넣지 않음")
    ap.add_argument("--auto-name", action="store_true", help="aria-label/figcaption에서 파일명 추론 (기본은 fig1, fig2…)")
    args = ap.parse_args()

    src = Path(args.html).expanduser()
    if not src.is_file():
        print(f"파일을 찾을 수 없음: {src}")
        return 2
    html = src.read_text(encoding="utf-8")

    out_dir = Path(args.out_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)

    light, dark, rules = parse_css_blocks(html)
    svgs = re.findall(r"<svg\b.*?</svg>", html, re.S)
    if not svgs:
        print("인라인 SVG를 찾지 못했습니다.")
        return 1

    given = [n.strip() for n in args.names.split(",") if n.strip()]
    print(f"\nSVG {len(svgs)}개 추출 → {out_dir}\n")
    written = []

    for i, svg in enumerate(svgs, 1):
        used = set(re.findall(r"var\((--[a-z0-9-]+)\)", svg))
        style = build_style(light, dark, rules, used)

        vb = re.search(r'viewBox="([-\d.\s]+)"', svg)
        bg = ""
        if vb and not args.no_background:
            x, y, w, h = (float(v) for v in vb.group(1).split())
            fill = "var(--card)" if "--card" in light else "var(--paper)"
            if fill.strip("var(-)") not in [k.strip("-") for k in light]:
                fill = "#f8fafa"
            bg = f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" fill="{fill}"/>\n'
            # 배경에 쓰인 변수도 정의에 포함되도록 style을 다시 만든다
            used |= set(re.findall(r"var\((--[a-z0-9-]+)\)", bg))
            style = build_style(light, dark, rules, used)

        open_end = svg.index(">") + 1
        head = svg[:open_end]
        if "xmlns=" not in head:
            head = head.replace("<svg", '<svg xmlns="http://www.w3.org/2000/svg"', 1)
        out = f'<?xml version="1.0" encoding="UTF-8"?>\n{head}\n{style}\n{bg}{svg[open_end:]}\n'

        base = given[i - 1] if i <= len(given) else guess_name(html, svg, i, auto=args.auto_name)
        fname = f"{args.prefix}-{base}.svg" if args.prefix else f"{base}.svg"
        path = out_dir / fname
        path.write_text(out, encoding="utf-8")
        written.append(fname)

        missing = used - set(light) - set(dark)
        flag = f"  변수 누락 {sorted(missing)}" if missing else ""
        print(f"  {i}. {fname}{flag}")

    print("\n노트에 넣을 임베드 구문:\n")
    for f in written:
        print(f"  ![[{f}]]")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
