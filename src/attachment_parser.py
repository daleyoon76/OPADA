"""첨부 파일(PDF·HWP·HWPX) 바이트를 텍스트로 바꾼다.

프로덕션 서버(`src/server.py`)가 시스템 python3.9 로 도는데, 그 환경에는 pdfminer·pypdf·
pyhwp 가 없다(표준 라이브러리만 원칙). 그래서 이 스크립트는 별도 venv
(`/Users/user/Documents/Dev/.opada-venv`)의 python 으로 **subprocess 로만** 돈다 —
무거운 파싱 라이브러리를 서버 프로세스 메모리에 들이지 않고 완전히 격리한다.

    <venv-python> attachment_parser.py < 원본바이트 > 텍스트(stdout)

형식은 파일 확장자가 아니라 **매직 바이트로 직접 판별**한다. 표본 `22_7.hwp`가 실제로는
zip(PK) 구조인 것을 실측으로 확인했다(2026-09-12) — 온비드 첨부는 확장자와 내용이 어긋날 수
있어서, 확장자를 믿으면 이 파일 하나 때문에 파싱이 통째로 죽는다.

.opada-survey/extract_text.py 의 표본조사 로직과 같다(정규식·정정 이력 포함).
그쪽은 표본 59건을 일괄 처리하는 조사 스크립트이고, 이건 실시간 1건을 처리하는
프로덕션 스크립트라 파일이 갈렸다 — 로직이 갈리면 이 주석에 적는다.
"""

from __future__ import annotations

import html
import re
import sys
import tempfile
import zipfile
from pathlib import Path

# <hp:t> 만 잡는다. <hp:t[^>]*> 로 쓰면 <hp:tbl>·<hp:tab> 에도 걸려 표 XML 을 통째로 삼킨다.
HWPX_TEXT_RE = re.compile(r"<hp:t(?:\s[^>]*)?>(.*?)</hp:t>", re.S)
TAG_RE = re.compile(r"<[^>]+>")


def pdf_text(data: bytes) -> str:
    with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp:
        tmp.write(data)
        tmp.flush()
        try:
            from pdfminer.high_level import extract_text

            text = extract_text(tmp.name)
            if text.strip():
                return text
        except Exception:  # noqa: BLE001
            pass
        from pypdf import PdfReader

        reader = PdfReader(tmp.name, strict=False)
        return "\n".join(page.extract_text() or "" for page in reader.pages)


def hwp_text(data: bytes) -> str:
    # hwp5html --output 은 디렉터리가 아니라 «출력 파일 경로» 다(2026-09-12 --help 로 확인).
    # 옛 코드는 디렉터리로 착각해 index.xhtml 을 찾다 FileNotFoundError 로 죽었다.
    # `python -m hwp5.hwp5html` 로 부르면 exit 0 인데도 출력 파일을 안 쓴다(2026-09-12 실측,
    # 원인 불명 — 리소스 경로가 -m 실행에서 어긋나는 것으로 추정). venv bin 의 콘솔 스크립트
    # `hwp5html` 을 직접 부르면 된다.
    import subprocess

    hwp5html_bin = Path(sys.executable).with_name("hwp5html")
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "input.hwp"
        src.write_bytes(data)
        out_file = Path(tmp) / "out.html"
        subprocess.run(
            [str(hwp5html_bin), "--html", "--output", str(out_file), str(src)],
            check=True,
            capture_output=True,
            timeout=60,
        )
        raw = out_file.read_text(encoding="utf-8", errors="replace")
    raw = re.sub(r"</(p|td|tr|li|h\d)>", "\n", raw)
    return html.unescape(TAG_RE.sub("", raw))


def zip_text(data: bytes) -> str:
    # 진짜 zip(묶음 파일)은 풀지 않고 파일명 목록만 남긴다 — .opada-survey/extract_text.py 와
    # 같은 규칙(2026-09-11 확정). 묶음 안이 도면 PDF 같은 비문서 파일일 때가 많아 목록만으로도
    # find_doc_names() 가 서류명을 줍는다(예: 09_4.zip → 도면 파일명만, 서류 없음이 맞는 답).
    import io

    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        sections = sorted(n for n in zf.namelist() if re.match(r"Contents/section\d+\.xml$", n))
        if sections:
            parts = [
                " ".join(TAG_RE.sub(" ", t) for t in HWPX_TEXT_RE.findall(zf.read(n).decode("utf-8", "replace")))
                for n in sections
            ]
            return html.unescape("\n".join(parts))
        return "\n".join(zf.namelist())


def detect_kind(data: bytes) -> str:
    if data.startswith(b"%PDF"):
        return "pdf"
    if data.startswith(b"PK\x03\x04"):
        return "zip"  # HWPX, 혹은 zip 구조인데 확장자만 .hwp 인 경우(2026-09-12 22_7.hwp 실측)
    if data.startswith(b"\xd0\xcf\x11\xe0"):
        return "hwp"  # OLE2 Compound Binary — 진짜 HWP5
    raise ValueError("알 수 없는 파일 형식(매직 바이트 불일치)")


def main() -> int:
    if len(sys.argv) != 1:
        print("usage: attachment_parser.py < bytes > text", file=sys.stderr)
        return 2
    data = sys.stdin.buffer.read()
    try:
        kind = detect_kind(data)
        text = {"pdf": pdf_text, "hwp": hwp_text, "zip": zip_text}[kind](data)
    except Exception as exc:  # noqa: BLE001 — 한 첨부 실패로 분석 전체를 죽이지 않는다
        print(f"파싱 실패: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
