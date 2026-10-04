#!/usr/bin/env python3
"""Turn _bibliography/papers.bib into the _publications/*.md collection.

Usage (from anywhere in the repo):

    python3 markdown_generator/bib2md.py [--check]

--check exits non-zero if the generated files are out of date instead of
writing them; that is what CI uses.

Only the standard library is required -- the BibTeX parser below is small on
purpose so that the site can be regenerated on a bare machine (and inside a
GitHub Action) without a pip install.
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BIB_FILE = REPO / "_bibliography" / "papers.bib"
OUT_DIR = REPO / "_publications"

# Names rendered in bold in the author list.
ME = ["Hanna Lachnitt"]

MARKER = "generated_from_bibtex: true"

# Section each entry lands in, in display order.
CATEGORY_ORDER = ["journal", "conference", "preprint", "thesis", "other"]


# --------------------------------------------------------------------------
# BibTeX parsing
# --------------------------------------------------------------------------

def strip_comments(text: str) -> str:
    out = []
    for line in text.splitlines():
        if line.lstrip().startswith("%"):
            continue
        out.append(line)
    return "\n".join(out)


def match_brace(text: str, start: int) -> int:
    """Index of the '}' closing the '{' at *start*."""
    depth = 0
    i = start
    while i < len(text):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    raise ValueError(f"unbalanced braces starting at offset {start}")


def split_top_level(text: str, sep: str) -> list[str]:
    """Split on *sep* but only outside braces and quotes."""
    parts, buf, depth, quoted = [], [], 0, False
    i = 0
    while i < len(text):
        c = text[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        elif c == '"' and depth == 0:
            quoted = not quoted
        if depth == 0 and not quoted and text.startswith(sep, i):
            parts.append("".join(buf))
            buf = []
            i += len(sep)
            continue
        buf.append(c)
        i += 1
    parts.append("".join(buf))
    return parts


def unwrap(value: str) -> str:
    value = value.strip()
    while len(value) >= 2 and (
        (value[0] == "{" and match_brace(value, 0) == len(value) - 1)
        or (value[0] == '"' and value[-1] == '"')
    ):
        value = value[1:-1].strip()
    return value


def parse_entries(text: str) -> list[dict]:
    """Return [{'type', 'key', 'raw', <fields...>}] in file order."""
    text = strip_comments(text)
    entries = []
    for m in re.finditer(r"@(\w+)\s*\{", text):
        kind = m.group(1).lower()
        if kind in ("comment", "preamble", "string"):
            continue
        open_brace = m.end() - 1
        close_brace = match_brace(text, open_brace)
        body = text[open_brace + 1 : close_brace]
        raw = text[m.start() : close_brace + 1].strip()

        chunks = split_top_level(body, ",")
        entry = {"type": kind, "key": chunks[0].strip(), "raw": raw}
        for chunk in chunks[1:]:
            if "=" not in chunk:
                continue
            name, _, value = chunk.partition("=")
            name = name.strip().lower()
            if name:
                entry[name] = unwrap(value)
        entries.append(entry)
    return entries


# --------------------------------------------------------------------------
# LaTeX -> Unicode
# --------------------------------------------------------------------------

COMBINING = {
    '"': "\u0308", "'": "\u0301", "`": "\u0300", "^": "\u0302",
    "~": "\u0303", "=": "\u0304", ".": "\u0307", "u": "\u0306",
    "v": "\u030c", "H": "\u030b", "c": "\u0327", "k": "\u0328",
    "r": "\u030a", "d": "\u0323", "b": "\u0331",
}

LITERALS = {
    r"\ss": "ß", r"\aa": "å", r"\AA": "Å", r"\ae": "æ", r"\AE": "Æ",
    r"\oe": "œ", r"\OE": "Œ", r"\o": "ø", r"\O": "Ø",
    r"\l": "ł", r"\L": "Ł", r"\i": "ı", r"\j": "ȷ",
    r"\textendash": "–", r"\textemdash": "—", r"\ldots": "…",
}

ESCAPED = {
    r"\&": "&", r"\_": "_", r"\%": "%", r"\$": "$", r"\#": "#",
    r"\{": "{", r"\}": "}", r"\,": " ", r"\ ": " ",
}

ACCENT_RE = re.compile(
    r'\\(["\'`^~=.]|[uvHckrdb](?=\s*\{))\s*(?:\{\s*(\\?[a-zA-Z]?)\s*\}|([a-zA-Z]))'
)


def _accent(m: re.Match) -> str:
    base = m.group(2) if m.group(2) is not None else m.group(3)
    base = LITERALS.get(base, base) if base.startswith("\\") else base
    return unicodedata.normalize("NFC", base + COMBINING[m.group(1)])


def delatex(text: str, dashes: bool = True) -> str:
    """Render a BibTeX field as plain Unicode."""
    if not text:
        return ""
    prev = None
    while prev != text:
        prev = text
        text = ACCENT_RE.sub(_accent, text)
    for src, dst in sorted(LITERALS.items(), key=lambda kv: -len(kv[0])):
        text = re.sub(re.escape(src) + r"(?![a-zA-Z])", dst, text)
    for src, dst in ESCAPED.items():
        text = text.replace(src, dst)
    text = text.replace("{", "").replace("}", "")
    if dashes:
        text = text.replace("---", "—").replace("--", "–")
    text = text.replace("~", " ")
    return re.sub(r"\s+", " ", text).strip()


def clean_url(text: str) -> str:
    for src, dst in ESCAPED.items():
        text = text.replace(src, dst)
    return text.replace("{", "").replace("}", "").strip()


# --------------------------------------------------------------------------
# Entry -> page
# --------------------------------------------------------------------------

def parse_authors(field: str) -> list[str]:
    names = []
    # BibTeX wraps long author lists over several lines; normalise first so
    # that " and " is a reliable separator.
    field = re.sub(r"\s+", " ", field).strip()
    for raw in split_top_level(field, " and "):
        name = delatex(raw, dashes=False)
        if not name:
            continue
        if "," in name:  # "Last, First" -> "First Last"
            last, _, first = name.partition(",")
            name = f"{first.strip()} {last.strip()}".strip()
        names.append(name)
    return names


def join_authors(names: list[str]) -> str:
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f"{names[0]} and {names[1]}"
    return ", ".join(names[:-1]) + f", and {names[-1]}"


ACRONYM_RE = re.compile(r"\{([^{}]+)\}")


def acronym(booktitle: str) -> str | None:
    """DBLP wraps venue acronyms in braces -- pick the first plausible one."""
    for candidate in ACRONYM_RE.findall(booktitle):
        letters = re.sub(r"[^A-Za-z]", "", candidate)
        if len(letters) >= 3 and letters.isupper():
            return letters
    return None


def categorise(e: dict) -> str:
    override = e.get("pubtype") or e.get("category")
    if override:
        chosen = delatex(override).lower()
        if chosen not in CATEGORY_ORDER:
            print(f"warning: unknown pubtype {chosen!r} in {e['key']}, using 'other'",
                  file=sys.stderr)
            return "other"
        return chosen
    journal = delatex(e.get("journal", ""))
    if e.get("eprint") or journal.lower() in ("corr", "arxiv"):
        return "preprint"
    if e["type"] in ("phdthesis", "mastersthesis"):
        return "thesis"
    if e["type"] in ("inproceedings", "conference", "incollection"):
        return "conference"
    if e["type"] == "article":
        return "journal"
    return "other"


def venue_of(e: dict, category: str) -> tuple[str, str]:
    """(short venue for the list, full venue for the detail page)."""
    if category == "preprint":
        eprint = delatex(e.get("eprint", "")) or delatex(e.get("volume", "")).replace("abs/", "")
        short = f"arXiv:{eprint}" if eprint else "Preprint"
        return short, short
    raw_booktitle = e.get("booktitle", "")
    if raw_booktitle:
        full = delatex(raw_booktitle)
        return acronym(raw_booktitle) or full, full
    if e.get("journal"):
        full = delatex(e["journal"])
        return full, full
    if e.get("school"):
        full = delatex(e["school"])
        return full, full
    full = delatex(e.get("publisher", ""))
    return full, full


def links_of(e: dict) -> list[tuple[str, str]]:
    links, seen = [], set()

    def add(label: str, url: str) -> None:
        # DOIs are case-insensitive and DBLP is inconsistent about it, so
        # compare normalised, but keep the URL as written.
        key = url.rstrip("/").lower()
        if url and key not in seen:
            seen.add(key)
            links.append((label, url))

    if e.get("doi"):
        add("DOI", "https://doi.org/" + clean_url(e["doi"]))
    if e.get("eprint"):
        add("arXiv", "https://arxiv.org/abs/" + clean_url(e["eprint"]))
    if e.get("url"):
        url = clean_url(e["url"])
        label = "PDF" if url.lower().endswith(".pdf") else "Paper"
        add(label, url)
    for field, label in (("code", "Code"), ("slides", "Slides"), ("video", "Video")):
        if e.get(field):
            add(label, clean_url(e[field]))
    return links


def slugify(title: str) -> str:
    slug = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^A-Za-z0-9]+", "-", slug).strip("-").lower()
    return re.sub(r"-{2,}", "-", slug)[:80]


MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun",
     "jul", "aug", "sep", "oct", "nov", "dec"], start=1)}


def date_of(e: dict) -> str:
    year = delatex(e.get("year", "")) or "1900"
    month = delatex(e.get("month", "")).strip().lower()[:3]
    mm = MONTHS.get(month)
    if mm is None and month.isdigit():
        mm = int(month)
    return f"{year}-{mm or 1:02d}-01"


def yaml_quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def render(e: dict) -> tuple[str, str]:
    """Return (filename, markdown) for one BibTeX entry."""
    title = delatex(e.get("title", "Untitled"))
    authors = parse_authors(e.get("author", "") or e.get("editor", ""))
    category = categorise(e)
    venue, venue_full = venue_of(e, category)
    date = date_of(e)
    year = date[:4]
    links = links_of(e)
    slug = f"{year}-{slugify(title)}"

    front = [
        "---",
        f"title: {yaml_quote(title)}",
        "collection: publications",
        f"pubtype: {category}",
        f"permalink: /publication/{slug}/",
        f"date: {date}",
        f"venue: {yaml_quote(venue)}",
        f"venue_full: {yaml_quote(venue_full)}",
        f"authors: {yaml_quote(join_authors(authors))}",
        f"bibkey: {yaml_quote(e['key'])}",
        MARKER,
    ]
    numbering = () if category == "preprint" else ("volume", "number", "publisher")
    for field in numbering + ("award",):
        key = field
        if e.get(field):
            front.append(f"{key}: {yaml_quote(delatex(e[field]))}")
    if e.get("pages"):
        front.append(f"pages: {yaml_quote(delatex(e['pages']))}")
    if e.get("note"):
        front.append(f"blurb: {yaml_quote(delatex(e['note']))}")
    if links:
        front.append(f"paperurl: {yaml_quote(links[0][1])}")
        front.append("links:")
        for label, url in links:
            front.append(f"  - label: {yaml_quote(label)}")
            front.append(f"    url: {yaml_quote(url)}")

    # Recommended-citation string, as the theme expects it.
    bits = [join_authors(authors).rstrip(".") + ".", f'“{title}.”']
    if venue_full:
        bits.append(venue_full + ",")
    bits.append(year + ".")
    front.append(f"citation: {yaml_quote(' '.join(bits))}")

    bibtex = "\n".join("  " + line for line in e["raw"].splitlines())
    front.append("bibtex: |")
    front.append(bibtex)
    front.append("---")

    body = []
    if e.get("note"):
        body.append(delatex(e["note"]))
    if links:
        body.append(" · ".join(f"[{label}]({url})" for label, url in links))
    body.append("{% include publication-bibtex.html %}")

    return f"{date}-{slugify(title)}.md", "\n".join(front) + "\n\n" + "\n\n".join(body) + "\n"


# --------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="verify _publications is up to date; write nothing")
    args = ap.parse_args()

    if not BIB_FILE.exists():
        print(f"error: {BIB_FILE} not found", file=sys.stderr)
        return 1

    entries = parse_entries(BIB_FILE.read_text(encoding="utf-8"))
    wanted: dict[str, str] = {}
    for e in entries:
        if delatex(e.get("hidden", "")).lower() in ("true", "yes", "1"):
            continue
        name, text = render(e)
        if name in wanted:
            print(f"error: two entries produce {name}", file=sys.stderr)
            return 1
        wanted[name] = text

    OUT_DIR.mkdir(exist_ok=True)
    existing = {
        p.name: p.read_text(encoding="utf-8")
        for p in OUT_DIR.glob("*.md")
    }
    stale = [n for n, t in existing.items() if n not in wanted and MARKER in t]
    changed = [n for n, t in wanted.items() if existing.get(n) != t]

    if args.check:
        if stale or changed:
            for n in sorted(stale):
                print(f"stale:   {n}")
            for n in sorted(changed):
                print(f"outdated: {n}")
            print("\n_publications is out of date; run python3 markdown_generator/bib2md.py",
                  file=sys.stderr)
            return 1
        print(f"up to date ({len(wanted)} publications)")
        return 0

    for name in stale:
        (OUT_DIR / name).unlink()
        print(f"removed {name}")
    for name in changed:
        (OUT_DIR / name).write_text(wanted[name], encoding="utf-8")
        print(f"wrote   {name}")
    print(f"{len(wanted)} publications from {BIB_FILE.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
