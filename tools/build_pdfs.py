"""Build the PDF versions of docs/*.md with headless Chrome.

Usage:  python tools/build_pdfs.py
Needs:  mistune (pip install mistune) and Google Chrome or Microsoft Edge.
Set the CHROME environment variable if the browser is not found automatically.
"""
import html
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import mistune

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
OUT = DOCS / "pdf"

FOOTERS = {
    "00_Roadmap_2026-2028": "AIM²P — Roadmap scientifique et opérationnelle 2026–2028",
}
DEFAULT_FOOTER = "AIM²P — Phase 0 : cadrage scientifique"

CSS = """
@page {
  size: A4;
  margin: 18mm 17mm 20mm 17mm;
  @bottom-left { content: "%(footer)s"; font: 8pt 'Segoe UI', Arial, sans-serif; color: #6B7A90; }
  @bottom-right { content: "Page " counter(page) " / " counter(pages); font: 8pt 'Segoe UI', Arial, sans-serif; color: #6B7A90; }
}
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { font: 10pt/1.55 'Segoe UI', 'Helvetica Neue', Arial, sans-serif; color: #1F2733; margin: 0; }
h1 { font-size: 21pt; line-height: 1.2; color: #1B2F55; text-transform: uppercase; margin: 0 0 4pt; letter-spacing: .2pt; }
h1 + p { color: #5A6578; font-size: 11pt; margin: 0 0 10pt; }
h1 + p strong { font-weight: 400; }
h1 + p + p { background: #EEF2F6; border-radius: 4px; padding: 7pt 10pt; font-size: 8.5pt; color: #3B4658; }
hr { border: 0; border-top: 2px solid #1B2F55; margin: 14pt 0 16pt; }
h2 { font-size: 12.5pt; color: #1B2F55; text-transform: uppercase; border-bottom: 1px solid #DCE3EC;
     padding-bottom: 3pt; margin: 18pt 0 8pt; break-after: avoid; }
h2:has(+ p + pre) { break-before: page; }
h3 { font-size: 11pt; color: #2E6DB4; margin: 12pt 0 6pt; break-after: avoid; }
p { margin: 0 0 7pt; text-align: justify; }
ul { margin: 0 0 8pt; padding-left: 16pt; }
li { margin: 0 0 4pt; text-align: justify; }
code { font-family: Consolas, 'Cascadia Mono', monospace; font-size: 8.8pt; background: #F1F4F8; padding: 0 3pt; border-radius: 3px; }
pre { background: #141C2B; color: #DCE3EC; border-radius: 6px; padding: 9pt 12pt; font-size: 6.9pt; line-height: 1.17;
      break-inside: avoid; overflow: hidden; }
pre code { background: none; padding: 0; color: inherit; font-size: inherit; }
table { width: 100%; border-collapse: collapse; margin: 6pt 0 10pt; font-size: 8.8pt; break-inside: auto; }
th { background: #2E6DB4; color: #fff; text-align: left; padding: 6pt 7pt; font-weight: 600; }
td { border-bottom: 1px solid #DCE3EC; padding: 5pt 7pt; vertical-align: top; }
tr:nth-child(even) td { background: #F6F8FB; }
tr { break-inside: avoid; }
a { color: #2E6DB4; text-decoration: none; }
.callout { border-left: 4px solid #2E6DB4; background: #EAF3FB; padding: 8pt 11pt; margin: 8pt 0 10pt;
           border-radius: 0 4px 4px 0; break-inside: avoid; }
.callout p:last-child { margin-bottom: 0; }
.callout.caution { border-color: #D64545; background: #FDF1F1; color: #8E2525; }
"""

ALERT = re.compile(r"^> \[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*$")


def find_chrome():
    if os.environ.get("CHROME"):
        return os.environ["CHROME"]
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    ]
    for c in candidates:
        if Path(c).exists():
            return c
    for name in ("google-chrome", "chromium", "chromium-browser", "chrome", "msedge"):
        if shutil.which(name):
            return shutil.which(name)
    sys.exit("Chrome/Edge not found: set the CHROME environment variable.")


def render(md_text, md):
    """Markdown -> HTML, turning GitHub alerts (> [!NOTE]) into styled callouts."""
    lines, out, i = md_text.splitlines(), [], 0
    while i < len(lines):
        m = ALERT.match(lines[i])
        if m:
            kind = m.group(1).lower()
            i += 1
            inner = []
            while i < len(lines) and lines[i].startswith(">"):
                inner.append(re.sub(r"^> ?", "", lines[i]))
                i += 1
            out += ["", f'<div class="callout {kind}">{md(chr(10).join(inner))}</div>', ""]
        else:
            out.append(lines[i])
            i += 1
    return md("\n".join(out))


def main():
    md = mistune.create_markdown(escape=False, plugins=["table", "strikethrough"])
    chrome = find_chrome()
    OUT.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        for src in sorted(DOCS.glob("*.md")):
            footer = FOOTERS.get(src.stem, DEFAULT_FOOTER).replace('"', '\\"')
            title = html.escape(src.stem.replace("_", " "))
            body = render(src.read_text(encoding="utf-8"), md)
            page = (f'<!doctype html><html lang="fr"><head><meta charset="utf-8"><title>{title}</title>'
                    f"<style>{CSS.replace('%(footer)s', footer)}</style></head><body>{body}</body></html>")
            tmp_html = Path(tmp) / f"{src.stem}.html"
            tmp_html.write_text(page, encoding="utf-8")
            pdf = OUT / f"{src.stem}.pdf"
            subprocess.run([chrome, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                            f"--print-to-pdf={pdf}", tmp_html.as_uri()],
                           check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("built", pdf.relative_to(ROOT))


if __name__ == "__main__":
    main()
