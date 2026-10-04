# Publication list

The publication list on <https://lachnitt.github.io/publications/> is generated
from one file:

    _bibliography/papers.bib

## Adding a paper

1. Copy the BibTeX entry (DBLP's "BibTeX" export works as-is) into
   `_bibliography/papers.bib`.
2. Run

       python3 markdown_generator/bib2md.py

   which rewrites `_publications/*.md` — one Markdown page per entry.
3. Commit both the `.bib` change and the regenerated pages.

Step 2 is optional: `.github/workflows/publications.yml` runs the same command
on every push that touches the `.bib` file and commits the result for you. So
pushing only the `.bib` edit works too.

Nothing in `_publications/` should be edited by hand — the generator overwrites
every file it previously produced (they carry a `generated_from_bibtex: true`
marker in their front matter).

## What the generator does

* Parses BibTeX with the standard library only — no `pip install` needed.
* Converts LaTeX accents and escapes to Unicode (`N{\"{o}}tzli` → `Nötzli`).
* Sorts entries into sections: journal articles, conference and workshop
  papers, preprints, theses, other. The section is guessed from the entry type
  (`@article` in `CoRR`, or anything with an `eprint` field, counts as a
  preprint).
* Shortens conference venues to the acronym DBLP already braces in the
  `booktitle` (`{TACAS} 2023, Held as Part of ...` → `TACAS`); the full venue
  stays available as the tooltip and on the paper's own page.
* Collects `doi`, `eprint` and `url` into the link row and keeps the verbatim
  BibTeX entry for the "BibTeX" toggle.

## Optional fields

These are not standard BibTeX; the generator understands them and other tools
ignore them.

| Field | Effect |
| --- | --- |
| `pubtype = {journal}` | Force the section (`journal`, `conference`, `preprint`, `thesis`, `other`). |
| `note = {...}` | One-line blurb shown under the entry. |
| `award = {Best Paper}` | Badge next to the venue. |
| `code = {https://...}` | Adds a "Code" link. |
| `slides = {https://...}` | Adds a "Slides" link. |
| `video = {https://...}` | Adds a "Video" link. |
| `hidden = {true}` | Keep the entry in the `.bib` but leave it off the site. |

## Checking without writing

    python3 markdown_generator/bib2md.py --check

exits non-zero when `_publications/` does not match the `.bib` file.

## Where the rendering lives

* `_pages/publications.md` — the page, grouping entries into sections.
* `_includes/archive-single-publication.html` — one entry in the list.
* `_includes/publication-bibtex.html` — the BibTeX block on a paper's own page.
* `_sass/_publications.scss` — styling (imported from `assets/css/main.scss`).
