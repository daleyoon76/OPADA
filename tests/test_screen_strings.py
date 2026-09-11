"""화면 문자열 ↔ 금지표현 게이트 (재기획안 판정 r2 P0-F).

금지표현 가드는 sanitize_ai_text() 한 곳에만 있었다. 그런데 headline·notes·profile.label 같은
결정적 문자열은 그 관문을 지나지 않는다. 이 게이트는 «화면으로 나갈 수 있는 문자열 전부»를 본다.

창 (무엇을 보고 무엇을 안 보는가)
- src/server.py : 파이썬 문자열 토큰 전부(tokenize). 주석은 토큰이 아니라서 자연히 빠진다.
- src/app.js    : 주석을 벗긴 뒤 따옴표·백틱 문자열 전부.
- src/index.html: 주석을 벗긴 뒤 태그 밖 본문과 속성값 전부.
- 이 창이 통과시키는 변형: 사용자에게 안 보이는 문자열(로그 메시지·dict 키)도 함께 본다 → 오탐 쪽으로
  넓다. 반대로 서버가 «런타임에 조립»하는 문자열(f-string 조각을 이어 붙인 결과)은 조각 단위로만 본다 →
  두 조각에 걸친 금지표현은 못 잡는다.
- 대조는 공백을 전부 벗기고 영문 대소문자를 무시한다(「자동입찰」「vertex ai」도 잡는다).

    python3 tests/test_screen_strings.py
"""

from __future__ import annotations

import io
import re
import sys
import tokenize
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"

# CLAUDE.md 「발표·시연 금지표현」 원문을 손으로 옮겼다. CLAUDE.md 에서 «읽어 오지» 않는다 —
# 읽어 오면 그 줄이 비었을 때 게이트가 조용히 빈 목록으로 초록이 된다. 대신 둘이 어긋나면 붉힌다(G1).
FORBIDDEN = [
    "자동 입찰", "입찰 대행", "낙찰 가능성 예측", "투자수익률 판단", "법률 자문", "권리분석 대체",
    "PDF 리포트", "Q&A", "공고 해석 리포트", "Vertex AI", "Gemini AI", "Local MVP", "로컬 분석 API", "완전 자동",
]
# 권장 문장(CLAUDE.md). 금지어와 이웃한 어휘를 부정문으로 담는다 — 이 문장을 붉히면 게이트가 틀린 것이다.
RECOMMENDED = (
    "본 서비스는 입찰 여부, 법률 판단, 투자수익률, 낙찰 가능성을 제공하지 않으며, "
    "온비드 원문과 담당기관 확인을 우선하는 준비 보조 도구입니다."
)
MIN_STRINGS = {"server.py": 300, "app.js": 300, "index.html": 30}  # 창이 비면 기본 분기에서 초록이 난다

PLAYED = [("사용자 화면", "브라우저를 띄우지 않는다. 소스의 문자열 리터럴을 «화면 후보»로 연기한다")]
AXES = [
    ("G1", "게이트의 금지 목록 = CLAUDE.md 목록"),
    ("G2", "src 3개 파일의 화면 후보 문자열에 금지표현 0건"),
    ("G3", "판정 함수 직접 호출 — 금지어를 잡고(양성) 권장 문장·부정문은 통과(음성)"),
    ("G4", "창 — 주석 속 금지어는 세지 않고, 문자열 속 금지어는 센다"),
    ("G5", "모수 — 파일마다 화면 후보 문자열이 하한 이상"),
]

_results: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    _results.append((name, ok, detail))


def squash(text: str) -> str:
    return re.sub(r"\s+", "", text).lower()


def hits(text: str) -> list[str]:
    body = squash(text)
    return [term for term in FORBIDDEN if squash(term) in body]


def python_strings(source: str) -> list[str]:
    out: list[str] = []
    for tok in tokenize.generate_tokens(io.StringIO(source).readline):
        if tok.type == tokenize.STRING:
            out.append(tok.string)
    return out


def strip_js_comments(source: str) -> str:
    out, i, n, quote = [], 0, len(source), ""
    while i < n:
        ch = source[i]
        if quote:
            out.append(ch)
            if ch == "\\" and i + 1 < n:
                out.append(source[i + 1])
                i += 2
                continue
            if ch == quote:
                quote = ""
        elif ch in "'\"`":
            quote = ch
            out.append(ch)
        elif source.startswith("//", i):
            i = source.find("\n", i)
            i = n if i < 0 else i
            continue
        elif source.startswith("/*", i):
            j = source.find("*/", i + 2)
            i = n if j < 0 else j + 2
            continue
        else:
            out.append(ch)
        i += 1
    return "".join(out)


def js_strings(source: str) -> list[str]:
    body = strip_js_comments(source)
    return re.findall(r"`(?:\\.|[^`\\])*`|\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'", body, re.S)


def html_strings(source: str) -> list[str]:
    body = re.sub(r"<!--.*?-->", "", source, flags=re.S)
    texts = [t for t in re.split(r"<[^>]*>", body) if t.strip()]
    attrs = re.findall(r"=\s*\"([^\"]*)\"", body)
    return texts + attrs


def main() -> int:
    print(f"PLAYED — 이 게이트가 대신 연기한 것 {len(PLAYED)}개")
    for symbol, note in PLAYED:
        print(f"  · {symbol} — {note}")
    print(f"AXES — 축 {len(AXES)}개")
    for code, name in AXES:
        print(f"  {code} {name}")

    # G1 — SSOT 대조
    claude = (ROOT / "CLAUDE.md").read_text()
    line = next((l for l in claude.splitlines() if "자동 입찰" in l and "완전 자동" in l), "")
    ssot = [t.strip() for t in line.split("·")] if line else []
    ssot_flat: list[str] = []
    for term in ssot:
        ssot_flat.extend(part.strip() for part in term.split("/"))
    check("G1 CLAUDE.md 목록 줄을 찾았다", bool(line), line[:40])
    check("G1 게이트 목록 = CLAUDE.md 목록", sorted(ssot_flat) == sorted(FORBIDDEN),
          f"CLAUDE.md 에만 {sorted(set(ssot_flat) - set(FORBIDDEN))} · 게이트에만 {sorted(set(FORBIDDEN) - set(ssot_flat))}")

    # G3 — 판정 함수 직접 호출
    check("G3 양성 — 「완전 자동으로 처리합니다」를 잡는다", hits("완전 자동으로 처리합니다") == ["완전 자동"])
    check("G3 양성 — 붙여 쓴 「자동입찰」도 잡는다", hits("자동입찰 지원") == ["자동 입찰"])
    check("G3 양성 — 대소문자 다른 「vertex ai」도 잡는다", hits("powered by vertex ai") == ["Vertex AI"])
    check("G3 음성 — 권장 문장은 통과", hits(RECOMMENDED) == [], str(hits(RECOMMENDED)))
    check("G3 음성 — 「낙찰 가능성을 제공하지 않습니다」는 통과", hits("낙찰 가능성을 제공하지 않습니다") == [])
    check("G3 음성 — 「규칙 기반 누락 점검」은 통과", hits("규칙 기반 누락 점검") == [])

    # G4 — 창
    js_probe = '// 자동 입찰 은 하지 않는다\nconst a = "평범한 문구";\n/* 완전 자동 */'
    check("G4 음성 — JS 주석 속 금지어는 세지 않는다", not any(hits(s) for s in js_strings(js_probe)))
    js_probe2 = 'const b = "입찰 대행 서비스"; // 주석'
    check("G4 양성 — JS 문자열 속 금지어는 센다", any(hits(s) for s in js_strings(js_probe2)))
    js_probe3 = 'const u = "http://x.y/z"; const c = "완전 자동";'
    check("G4 양성 — 문자열 속 // 를 주석으로 오인하지 않는다", any(hits(s) for s in js_strings(js_probe3)))
    py_probe = '# 법률 자문 은 제외\nx = "평범"\n'
    check("G4 음성 — 파이썬 주석 속 금지어는 세지 않는다", not any(hits(s) for s in python_strings(py_probe)))
    check("G4 양성 — 파이썬 문자열 속 금지어는 센다", any(hits(s) for s in python_strings('y = "PDF 리포트"\n')))
    html_probe = '<!-- Q&A 섹션 --><p>안내</p><button title="공고 해석 리포트">x</button>'
    found = [h for s in html_strings(html_probe) for h in hits(s)]
    check("G4 HTML — 주석은 빼고 속성값은 센다", found == ["공고 해석 리포트"], str(found))

    # G2·G5 — 실제 파일
    extractors = {"server.py": python_strings, "app.js": js_strings, "index.html": html_strings}
    for name, extract in extractors.items():
        strings = extract((SRC / name).read_text())
        check(f"G5 {name} 화면 후보 문자열 {len(strings)}개 ≥ {MIN_STRINGS[name]}", len(strings) >= MIN_STRINGS[name])
        found = [(term, s.strip()[:50]) for s in strings for term in hits(s)]
        check(f"G2 {name} 금지표현 0건", not found, "; ".join(f"{t} ← {s}" for t, s in found[:3]))

    passed = sum(1 for _, ok, _ in _results if ok)
    print()
    for name, ok, detail in _results:
        if not ok:
            print(f"FAIL {name} — {detail}")
    covered = {name.split()[0] for name, _, _ in _results}
    uncovered = [code for code, _ in AXES if code not in covered]
    print(f"{passed}/{len(_results)} 통과 · 연기 {len(PLAYED)}개 · 축 {len(AXES)}개 중 미실행 {len(uncovered)}개"
          f"{' — ' + ', '.join(uncovered) if uncovered else ''}")
    if len(_results) < 20:
        print(f"🔴 판정 수 {len(_results)} < 20 — 축이 돌지 않았다")
        return 1
    return 0 if passed == len(_results) else 1


if __name__ == "__main__":
    sys.exit(main())
