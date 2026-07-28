#!/usr/bin/env python3
"""자립형 SVG 골격을 만든다.

옵시디언 노트에 임베드할 SVG는 스타일을 스스로 갖고 있어야 한다. 이 스크립트는
테마 변수(라이트/다크), 배경, 화살촉 마커, 텍스트 클래스를 미리 채운 골격을
만들어 준다. 도해 내용만 <!-- 내용 시작 --> 아래에 그리면 된다.

사용법:
    python svg_scaffold.py --out attachments/flow.svg --kind sequence
    python svg_scaffold.py --out attachments/cmp.svg --kind compare --width 920 --height 320
    python svg_scaffold.py --out attachments/arch.svg --kind blank --roles user,server,db
"""

import argparse
import sys
from pathlib import Path

# 참여자별 색. 라이트/다크 두 벌을 두는 이유는 라이트에서 좋은 색이 다크에서
# 눈을 찌르는 경우가 많기 때문이다.
PALETTE = {
    "light": {
        "ink": "#14202e", "ink-soft": "#43535f", "ink-faint": "#77858e",
        "paper": "#eef1f2", "card": "#f8fafa", "card-2": "#e4e9ea", "rule": "#cdd6d8",
        "r1": "#a8681c", "r2": "#4a5a8c", "r3": "#0f6e6a", "r4": "#5b7355", "danger": "#a83a2c",
        "r1-bg": "#f3e7d5", "r2-bg": "#e2e6f0", "r3-bg": "#d9e9e7", "r4-bg": "#e2e9df",
        "danger-bg": "#f2ddd9",
    },
    "dark": {
        "ink": "#dfe6e8", "ink-soft": "#a3b0b5", "ink-faint": "#74838a",
        "paper": "#0e1620", "card": "#16212c", "card-2": "#1e2b37", "rule": "#2c3b47",
        "r1": "#d9a05c", "r2": "#93a4d8", "r3": "#52b8af", "r4": "#9ab68f", "danger": "#dd7f6d",
        "r1-bg": "#33261e", "r2-bg": "#20263a", "r3-bg": "#123a37", "r4-bg": "#212f1e",
        "danger-bg": "#3a201b",
    },
}

FONT = 'ui-monospace,"SF Mono",SFMono-Regular,Menlo,Consolas,monospace'


def style_block():
    def decls(theme):
        return ";".join(f"--{k}:{v}" for k, v in PALETTE[theme].items())

    return f"""<style>
svg{{{decls('light')}}}
@media (prefers-color-scheme:dark){{svg{{{decls('dark')}}}}}
text{{font-family:{FONT}}}
.lbl{{font-size:12.5px;fill:var(--ink)}}
.lbl-sm{{font-size:11px;fill:var(--ink-soft)}}
.lbl-xs{{font-size:10px;fill:var(--ink-faint)}}
.num{{font-size:10.5px;font-weight:600;fill:var(--card)}}
.head{{font-size:12.5px;font-weight:700}}
</style>"""


def markers():
    """화살촉을 참여자 색마다 하나씩, 위험용으로 하나 더 정의한다.

    참여자 수와 무관하게 4개를 모두 만들어 둔다. 도해를 그리다 참여자를
    늘릴 때 마커가 없어서 화살표가 안 보이는 일을 막는 편이 낫다.
    """
    out = ["<defs>"]
    for i in range(1, 5):
        out.append(
            f'<marker id="a{i}" markerWidth="9" markerHeight="7" refX="8" refY="3.5" orient="auto">'
            f'<polygon points="0 0, 9 3.5, 0 7" fill="var(--r{i})"/></marker>'
        )
    out.append(
        '<marker id="ad" markerWidth="9" markerHeight="7" refX="8" refY="3.5" orient="auto">'
        '<polygon points="0 0, 9 3.5, 0 7" fill="var(--danger)"/></marker>'
    )
    out.append("</defs>")
    return "\n".join(out)


def sequence_body(roles, w, h):
    """참여자별 세로 생명선과 첫 단계 예시를 그린다."""
    n = len(roles)
    margin, box_w, box_h = 40, 140, 46
    gap = (w - 2 * margin - box_w) / max(n - 1, 1)
    lines = ["<!-- 내용 시작: 레인 헤더와 생명선 -->"]
    xs = []
    for i, role in enumerate(roles):
        x = margin + gap * i
        cx = x + box_w / 2
        xs.append(cx)
        ci = min(i + 1, 4)
        lines.append(
            f'<rect x="{x:g}" y="14" width="{box_w}" height="{box_h}" '
            f'fill="var(--r{ci}-bg)" stroke="var(--r{ci})" stroke-width="1.5"/>'
            f'<text class="head" x="{cx:g}" y="42" text-anchor="middle" fill="var(--r{ci})">{role}</text>'
        )
    for i, cx in enumerate(xs):
        ci = min(i + 1, 4)
        lines.append(
            f'<line x1="{cx:g}" y1="{14 + box_h}" x2="{cx:g}" y2="{h - 24}" '
            f'stroke="var(--r{ci})" stroke-width="1" stroke-dasharray="3 4" opacity="0.55"/>'
        )
    if len(xs) >= 2:
        y = 14 + box_h + 46
        lines += [
            "",
            "<!-- 단계 1 예시: 원(번호) + 화살표 + 라벨. 아래 패턴을 복제해 단계를 늘린다 -->",
            f'<circle cx="{xs[0]:g}" cy="{y}" r="9" fill="var(--r1)"/>',
            f'<text class="num" x="{xs[0]:g}" y="{y + 4}" text-anchor="middle">1</text>',
            f'<line x1="{xs[0] + 12:g}" y1="{y}" x2="{xs[1] - 8:g}" y2="{y}" '
            f'stroke="var(--r1)" stroke-width="1.8" marker-end="url(#a1)"/>',
            f'<text class="lbl-sm" x="{(xs[0] + xs[1]) / 2:g}" y="{y - 8}" '
            f'text-anchor="middle" fill="var(--ink)">여기에 단계 설명</text>',
        ]
    return "\n".join(lines)


def compare_body(roles, w, h):
    """좌우 비교 패널. 왼쪽을 문제/현재, 오른쪽을 해결/목표로 쓴다."""
    pad, gap = 8, 44
    pw = (w - 2 * pad - gap) / 2
    lx, rx = pad, pad + pw + gap
    return f"""<!-- 내용 시작: 좌(문제/현재) · 우(해결/목표) -->
<rect x="{lx:g}" y="8" width="{pw:g}" height="{h - 16:g}" fill="var(--danger-bg)"
      stroke="var(--danger)" stroke-width="1" stroke-dasharray="4 3"/>
<text class="head" x="{lx + 18:g}" y="34" fill="var(--danger)">지금 방식</text>
<text class="lbl-xs" x="{lx + 18:g}" y="52" fill="var(--danger)">무엇이 문제인지 한 줄로</text>

<rect x="{rx:g}" y="8" width="{pw:g}" height="{h - 16:g}" fill="var(--r3-bg)"
      stroke="var(--r3)" stroke-width="1"/>
<text class="head" x="{rx + 18:g}" y="34" fill="var(--r3)">바뀐 방식</text>
<text class="lbl-xs" x="{rx + 18:g}" y="52" fill="var(--r3)">무엇이 나아지는지 한 줄로</text>

<!-- 각 패널 안에 박스와 화살표를 배치한다. 대응되는 요소는 같은 y를 쓰면 비교가 쉽다 -->"""


def blank_body(roles, w, h):
    # XML 주석 안에는 하이픈 두 개를 연달아 쓸 수 없어서 CSS 변수 이름을 주석으로
    # 안내할 수 없다. 대신 <desc>에 담고, 자세한 목록은 실행 시 stdout으로 알린다.
    return """<desc>도해 내용을 이 아래에 그린다. 사용 가능한 색 변수와 클래스는 style 블록 참고.</desc>
<!-- 내용 시작 -->"""


BUILDERS = {"sequence": sequence_body, "compare": compare_body, "blank": blank_body}


def main():
    ap = argparse.ArgumentParser(description="자립형 SVG 골격 생성")
    ap.add_argument("--out", required=True, help="저장 경로 (.svg)")
    ap.add_argument("--kind", default="blank", choices=sorted(BUILDERS), help="도해 형태")
    ap.add_argument("--width", type=int, default=900)
    ap.add_argument("--height", type=int, default=460)
    ap.add_argument("--roles", default="사용자,서버", help="참여자 이름 쉼표 구분 (sequence에서 사용)")
    ap.add_argument("--no-background", action="store_true")
    args = ap.parse_args()

    roles = [r.strip() for r in args.roles.split(",") if r.strip()] or ["사용자", "서버"]
    if len(roles) > 4:
        print("참여자는 4명까지 색이 배정됩니다. 5번째부터는 var(--r4)를 공유합니다.", file=sys.stderr)

    w, h = args.width, args.height
    bg = "" if args.no_background else f'<rect x="0" y="0" width="{w}" height="{h}" fill="var(--card)"/>\n'
    body = BUILDERS[args.kind](roles, w, h)

    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}"
     role="img" aria-label="도해 설명을 여기에 적는다">
{style_block()}
{markers()}
{bg}{body}
</svg>
"""

    out = Path(args.out).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(svg, encoding="utf-8")

    print(f"생성: {out}  ({w}x{h}, {args.kind})")
    print(f"노트에 넣을 구문:  ![[{out.name}]]")
    print("\naria-label을 실제 설명으로 바꾸고, '내용 시작' 아래를 채우세요.\n")
    print("쓸 수 있는 토큰")
    print("  참여자 색   var(--r1) var(--r2) var(--r3) var(--r4)   배경은 -bg 접미사")
    print("  위험        var(--danger) / var(--danger-bg)")
    print("  글자        var(--ink) var(--ink-soft) var(--ink-faint)")
    print("  면과 선     var(--card) var(--card-2) var(--rule)")
    print("  화살촉      marker-end=\"url(#a1)\" … url(#a4), url(#ad)")
    print("  글자 클래스 .head .lbl .lbl-sm .lbl-xs .num")
    return 0


if __name__ == "__main__":
    sys.exit(main())
