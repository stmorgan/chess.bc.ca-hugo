# CLAUDE.md — BC Chess Federation Website Rebuild

## Project
Rebuilding chess.bc.ca as a static Hugo site, replacing the current PHP/no-database
codebase. Reference copy of the **old** site lives at `./public_html` (do not edit
this — it's for extracting content and behavior only). The new site is built at the
repo root. A local dev server runs at http://localhost:8080/.

Rollout approach: **big bang** — build the full new site, verify, then cut over.
Not a phased migration; old and new do not need to coexist long-term.

## Stack (do not deviate without discussion)
- Static site generator: **Hugo**
- Hosting/CI: **Netlify** (free tier), deploying from a **GitHub** repo
- CMS: **Decap CMS**, backend `git-gateway`, auth via **Netlify Identity**
  (no custom OAuth server — do not build one)
- Styling: hand-written responsive CSS (mobile-first, Flexbox/Grid). No CSS/JS
  framework unless we explicitly decide we need one.
- No database. No PHP in the new site.

## Directory layout
```
content/{news,clubs,instruction,bulletins,arbiters,links,champions}/
data/banners.yaml
layouts/partials/{nav,banners,footer}.html
static/admin/{index.html,config.yml}   # Decap CMS
static/css/
static/logo.svg
netlify.toml
```

## Content model
- **News** (folder collection, one file per item): front matter `title`, `date`,
  `expiry_date` (default = date + 14 days). Home page shows only items where
  `expiry_date > now`. News Archive page shows the rest. This is a **build-time**
  filter — a scheduled nightly rebuild (Netlify build hook + cron) is what actually
  moves items into the archive on their expiry date.
- **Clubs, Instruction** — folder collections (decided 2026-07-06): one file per
  club (grouped by a `city` field) and one file per instruction listing.
- **Events** — two kinds (decided 2026-07-06): repeating events live in
  `data/repeating_events.yaml` (Decap `list` widget); one-off tournaments stay on
  the embedded BCCF Google Calendar iframe (not CMS-managed).
- **BC Bulletins** — folder collection, Decap `file` widget uploads PDFs into
  `static/bulletins/` and commits them to the repo.
- **Arbiters, Links, Champions** — list collections backed by `data/*.yaml`,
  edited via Decap's `list` widget.
- **Banners** — `data/banners.yaml`, editable via Decap. Rendered in random order
  using Hugo's built-in `shuffle` function on every build. Count can change (not
  fixed at 4) — templates must not hard-code a banner count.
- Data files edited via Decap nest their list under a top-level key (e.g.
  `banners:` in `data/banners.yaml`) — Decap file collections require a map at
  the top level, not a bare list.
- Folder-collection items carry a hidden `type` field (= section name) so Decap's
  `filter` can hide Hugo's `_index.md` section pages from those collections;
  section intros are edited under the "Pages" collection instead. Keep `type` in
  front matter when migrating content.

## Known constraints
- Decap CMS (open source tier) has **no per-collection role restriction** — any
  logged-in editor can edit any collection. Don't try to fake per-collection ACLs
  in the CMS config; if fine-grained restriction is ever needed, that's a separate
  design conversation (e.g. splitting into multiple Netlify sites), not a quick fix.
- Old top banner is being removed entirely; replaced by `logo.svg` at the top of
  every page.
- Every page must be responsive (desktop + mobile). Check both when making layout
  changes — don't assume desktop-only.

## Workflow
- Before restructuring content types or the Decap config schema, check in rather
  than guessing — these are annoying to migrate twice.
- After template or CSS changes, run `hugo server` and sanity-check both a
  desktop-width and mobile-width viewport before considering the change done.
- Run `hugo build` (not just `hugo server`) before considering any milestone
  finished — `hugo server` can mask build errors that show up in production builds.
- Prefer Hugo's built-in template functions (`shuffle`, `where`, `dateModify`,
  time comparisons) over adding JS or external dependencies for logic like
  banner ordering or news expiry.
- Keep commit messages descriptive; Decap-driven content commits will be authored
  by editors and should stay separate/readable from code commits.
