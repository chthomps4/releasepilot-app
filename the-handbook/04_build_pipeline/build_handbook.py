#!/usr/bin/env python3
"""
Build The Handbook manuscript into a single HTML preview file.

Usage from repo root:
    python3 the-handbook/04_build_pipeline/build_handbook.py

Output:
    the-handbook/build/handbook_preview.html
"""

from pathlib import Path
import html
import re

ROOT = Path(__file__).resolve().parents[1]
CHAPTERS_DIR = ROOT / "01_manuscript" / "chapters"
BUILD_DIR = ROOT / "build"
OUTPUT_HTML = BUILD_DIR / "handbook_preview.html"

BOOK_TITLE = "The Handbook"
BOOK_SUBTITLE = "A Continuity Archive of Ancient Knowledge, Source Trails, and Responsible Interpretation"


def markdown_to_html(markdown_text: str) -> str:
    """Small dependency-free Markdown converter for manuscript preview.

    This is intentionally simple. It supports headings, blockquotes, paragraphs,
    unordered lists, ordered lists, fenced code blocks, and basic pipe tables.
    For final publishing, use Pandoc or a dedicated Markdown processor.
    """
    lines = markdown_text.splitlines()
    out = []
    in_ul = False
    in_ol = False
    in_code = False
    code_lines = []
    paragraph = []

    def flush_paragraph():
        nonlocal paragraph
        if paragraph:
            text = " ".join(line.strip() for line in paragraph).strip()
            if text:
                out.append(f"<p>{inline_format(text)}</p>")
            paragraph = []

    def close_lists():
        nonlocal in_ul, in_ol
        if in_ul:
            out.append("</ul>")
            in_ul = False
        if in_ol:
            out.append("</ol>")
            in_ol = False

    def render_table(table_lines):
        rows = []
        for row in table_lines:
            cells = [html.escape(cell.strip()) for cell in row.strip().strip("|").split("|")]
            rows.append(cells)
        if len(rows) < 2:
            return
        out.append("<table>")
        out.append("<thead><tr>" + "".join(f"<th>{cell}</th>" for cell in rows[0]) + "</tr></thead>")
        out.append("<tbody>")
        for row in rows[2:]:
            out.append("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>")
        out.append("</tbody></table>")

    def inline_format(text):
        text = html.escape(text)
        text = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", text)
        text = re.sub(r"\*(.*?)\*", r"<em>\1</em>", text)
        text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
        return text

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("```"):
            flush_paragraph()
            close_lists()
            if not in_code:
                in_code = True
                code_lines = []
            else:
                out.append("<pre><code>" + html.escape("\n".join(code_lines)) + "</code></pre>")
                in_code = False
            i += 1
            continue

        if in_code:
            code_lines.append(line)
            i += 1
            continue

        if stripped.startswith("|") and i + 1 < len(lines) and lines[i + 1].strip().startswith("|"):
            flush_paragraph()
            close_lists()
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i])
                i += 1
            render_table(table_lines)
            continue

        if not stripped:
            flush_paragraph()
            close_lists()
            i += 1
            continue

        heading = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if heading:
            flush_paragraph()
            close_lists()
            level = len(heading.group(1))
            text = inline_format(heading.group(2))
            out.append(f"<h{level}>{text}</h{level}>")
            i += 1
            continue

        if stripped.startswith(">"):
            flush_paragraph()
            close_lists()
            quote = stripped.lstrip("> ").strip()
            out.append(f"<blockquote>{inline_format(quote)}</blockquote>")
            i += 1
            continue

        if re.match(r"^-\s+", stripped):
            flush_paragraph()
            if in_ol:
                out.append("</ol>")
                in_ol = False
            if not in_ul:
                out.append("<ul>")
                in_ul = True
            out.append(f"<li>{inline_format(stripped[2:].strip())}</li>")
            i += 1
            continue

        numbered = re.match(r"^\d+\.\s+(.*)$", stripped)
        if numbered:
            flush_paragraph()
            if in_ul:
                out.append("</ul>")
                in_ul = False
            if not in_ol:
                out.append("<ol>")
                in_ol = True
            out.append(f"<li>{inline_format(numbered.group(1).strip())}</li>")
            i += 1
            continue

        close_lists()
        paragraph.append(line)
        i += 1

    flush_paragraph()
    close_lists()
    return "\n".join(out)


def build_html():
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    chapters = sorted(CHAPTERS_DIR.glob("CH*.md"))
    if not chapters:
        raise SystemExit(f"No chapter files found in {CHAPTERS_DIR}")

    body_parts = []
    toc_items = []

    for chapter in chapters:
        text = chapter.read_text(encoding="utf-8")
        first_heading = next((line.replace("#", "").strip() for line in text.splitlines() if line.startswith("# ")), chapter.stem)
        anchor = chapter.stem.lower().replace("_", "-")
        toc_items.append(f'<li><a href="#{anchor}">{html.escape(first_heading)}</a></li>')
        body_parts.append(f'<section class="chapter" id="{anchor}">\n{markdown_to_html(text)}\n</section>')

    html_doc = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(BOOK_TITLE)}</title>
  <style>
    :root {{
      --bg: #f4efe6;
      --paper: #fffaf0;
      --ink: #1f1a14;
      --muted: #655b50;
      --rule: #cbbfae;
      --accent: #4e342e;
    }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: Georgia, 'Times New Roman', serif;
      line-height: 1.7;
    }}
    .page {{
      max-width: 920px;
      margin: 0 auto;
      padding: 48px 22px 80px;
    }}
    header, .toc, .chapter {{
      background: var(--paper);
      border: 1px solid var(--rule);
      border-radius: 18px;
      padding: 34px;
      margin-bottom: 28px;
      box-shadow: 0 12px 30px rgba(31, 26, 20, 0.08);
    }}
    h1, h2, h3 {{
      line-height: 1.2;
      color: var(--accent);
    }}
    h1 {{ font-size: 2.4rem; }}
    h2 {{ margin-top: 2rem; border-bottom: 1px solid var(--rule); padding-bottom: .25rem; }}
    p {{ font-size: 1.08rem; }}
    blockquote {{
      border-left: 4px solid var(--accent);
      margin: 1.5rem 0;
      padding: .5rem 1rem;
      color: var(--muted);
      background: rgba(78, 52, 46, 0.06);
    }}
    table {{ width: 100%; border-collapse: collapse; margin: 1.2rem 0; font-size: .95rem; }}
    th, td {{ border: 1px solid var(--rule); padding: 8px 10px; vertical-align: top; }}
    th {{ background: rgba(78, 52, 46, 0.08); text-align: left; }}
    code, pre {{ background: rgba(31, 26, 20, 0.08); border-radius: 8px; }}
    code {{ padding: 1px 4px; }}
    pre {{ padding: 14px; overflow-x: auto; }}
    a {{ color: var(--accent); }}
    .subtitle {{ color: var(--muted); font-size: 1.15rem; }}
    @media print {{
      body {{ background: white; }}
      .page {{ max-width: none; padding: 0; }}
      header, .toc, .chapter {{ box-shadow: none; border: none; page-break-after: auto; }}
      .chapter {{ page-break-before: always; }}
    }}
  </style>
</head>
<body>
  <main class="page">
    <header>
      <h1>{html.escape(BOOK_TITLE)}</h1>
      <p class="subtitle">{html.escape(BOOK_SUBTITLE)}</p>
      <p><strong>Preview build:</strong> Markdown manuscript assembled into browser-readable HTML.</p>
    </header>
    <nav class="toc">
      <h2>Table of Contents</h2>
      <ol>
        {''.join(toc_items)}
      </ol>
    </nav>
    {''.join(body_parts)}
  </main>
</body>
</html>
"""
    OUTPUT_HTML.write_text(html_doc, encoding="utf-8")
    print(f"Built {OUTPUT_HTML}")


if __name__ == "__main__":
    build_html()
