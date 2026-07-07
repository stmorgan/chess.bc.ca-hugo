# BC Chess Federation Website Rebuild — Plan & Recommendations

## 1. Technology Stack

| Concern | Recommendation | Why |
|---|---|---|
| Static site generator | **Hugo** | You already know it; extremely fast builds; native `shuffle`, `where`, and date-comparison template functions cover requirements 4 and 5 with no plugins. |
| Source control | **GitHub** (public repo, e.g. `bc-chess-federation/chess.bc.ca`) | Free, familiar, satisfies your "free platform" goal, and is what Decap actually commits to. |
| Hosting / build / deploy | **Netlify** (free tier) | Builds Hugo automatically on every push, serves over HTTPS, supports your custom domain `chess.bc.ca`, and — critically — provides Identity + Git Gateway so Decap CMS needs no custom OAuth server. |
| CMS | **Decap CMS** (open source, formerly Netlify CMS) | Confirmed workable for all seven content types (see §3). Runs as a static admin page (`/admin/`) baked into the Hugo output — no separate backend to run yourself. |
| CMS auth | **Netlify Identity + Git Gateway** | Editors log in with email/password (or invite links); Netlify proxies their edits into GitHub commits. No OAuth app, no secrets to rotate. |
| Styling | **Hand-written responsive CSS** (mobile-first, Flexbox/Grid), no heavy JS framework | The site is content-driven, not app-like — a framework like Bootstrap/Tailwind is optional convenience, not a requirement. Given your background, plain CSS will be easy to maintain and keeps the build simple. |
| Scheduled rebuilds | **Netlify scheduled build** (via a build hook + cron, e.g. a free GitHub Actions workflow that pings the Netlify build hook daily) | Needed because "expired" and "banner order" are *build-time* decisions. Without a rebuild, a News item won't move to the archive on its expiry date just because time passed — the site has to be rebuilt to notice. A nightly rebuild handles this automatically. |

This satisfies all of your numbered goals:
1. Static generator + free GitHub/Netlify hosting.
2. Fully responsive CSS from scratch.
3. Decap CMS for all seven list types (see below).
4. Banner order via Hugo's `shuffle` at each rebuild.
5. News expiry + archive via front-matter date filtering.
6. New SVG logo replaces the old top banner.

## 2. Site & Content Structure (Hugo)

```
chess.bc.ca/
├── content/
│   ├── news/                  # one .md file per news item
│   ├── clubs/                 # one .md file per club (or a single data list — see below)
│   ├── instruction/           # chess instruction listings
│   ├── bulletins/             # BC Bulletin uploads (PDF + metadata)
│   ├── arbiters/              # arbiters list
│   ├── links/                 # links list
│   └── champions/             # champions list, by year
├── data/
│   └── banners.yaml           # list of banner images/links, editable via Decap
├── layouts/
│   ├── partials/
│   │   ├── nav.html
│   │   ├── banners.html       # renders {{ shuffle .Site.Data.banners }}
│   │   └── footer.html
│   └── _default/
├── static/
│   ├── admin/                 # Decap CMS: index.html + config.yml
│   ├── css/
│   └── logo.svg
├── netlify.toml
└── CLAUDE.md
```

**Simple, repeated lists** (arbiters, links, champions) work well as a *single* Decap "file collection" backed by `data/*.yaml`, edited with Decap's `list` widget — one form, add/remove/reorder rows, no separate files. **News, clubs, instruction, bulletins** are better as Decap "folder collections" (one Markdown file per entry) since each entry has enough of its own metadata (dates, PDFs, expiry) to deserve its own file with full editorial history in git.

## 3. Decap CMS Feasibility — confirmed workable

| Content type | Decap collection type | Notes |
|---|---|---|
| News | Folder collection | Fields: title, body, `date`, `expiry_date` (see §4 for default logic). |
| Clubs | Folder or list collection | Name, city, contact, meeting info, link. |
| Chess Instruction | Folder or list collection | Similar shape to Clubs. |
| BC Bulletins | Folder collection with a **file widget** | Decap uploads the PDF into the repo (e.g. `static/bulletins/`) and commits it — works well at federation scale; repo size grows slowly and is not a concern for years of PDFs. |
| Arbiters | List collection | Name, certification level, contact/region. |
| Links | List collection | Label + URL. |
| Champions | List collection, grouped by year | Year, category, name(s). |

All of this is standard, well-supported Decap functionality — nothing exotic required.

**Multiple editors, different logins:** yes — invite each editor by email through Netlify Identity; each gets their own login and commits show their name as the git author. The one caveat (flagged above) is that Decap's open-source tier doesn't gate *which collections* a given login can touch — that requires either trusting your editors (reasonable for a small federation) or standing up separate Netlify sites per role later if it becomes necessary.

## 4. News Expiry & Archive Logic

Front matter for each news item:
```yaml
---
title: "2026 BC Closed Championship Results"
date: 2026-07-06
expiry_date: 2026-07-20   # Decap default: date + 14 days
---
```

In Decap's `config.yml`, the `expiry_date` field uses a `datetime` widget with a computed default. Decap doesn't natively do "today + 14 days" as a default value, so the practical approach is:
- A small script (or a Decap **Editorial workflow** + a lightweight pre-fill via a custom widget/dateTime default expression) sets it automatically when `hugo new` scaffolds a post, **or**
- Simpler and more robust: a tiny Netlify **build-time** check is unnecessary — instead, handle the default in the Hugo archetype (`archetypes/news.md`) so anyone using `hugo new news/foo.md` gets `expiry_date` pre-filled to `{{ .Date | dateModify "+336h" }}` (14 days). For the Decap **form** itself, we'll set the field's default using Decap's `{{now}}`-style default plus document a "leave as-is unless you want a different expiry" convention — Claude Code can wire up whichever of these proves cleanest once we're looking at the real config.

Home page News section (Hugo template, conceptually):
```go-html-template
{{ $now := now }}
{{ range where .Site.RegularPages "Section" "news" }}
  {{ if gt (.Params.expiry_date) $now }}
    <!-- render on home page -->
  {{ end }}
{{ end }}
```

News Archive page: the inverse condition (`expiry_date` ≤ now). Because this is evaluated at **build time**, the nightly scheduled rebuild (§1) is what actually moves an item from "current" to "archived" the day after it expires — nobody has to manually intervene.

## 5. Banner Randomization

```go-html-template
{{ $banners := .Site.Data.banners }}
{{ range shuffle $banners }}
  <a href="{{ .link }}"><img src="{{ .image }}" alt="{{ .name }}"></a>
{{ end }}
```
`shuffle` is a built-in Hugo function — new random order every build, and the list itself (add/remove banners) is editable via Decap against `data/banners.yaml`.

## 6. Rollout Plan (Big Bang)

1. **Content inventory & migration prep** — extract all current News, Clubs, Instruction, Bulletins, Arbiters, Links, Champions content out of the existing PHP/HTML into structured Markdown/YAML. This is mostly mechanical; Claude Code can script the extraction once it has the real files.
2. **Hugo scaffold** — site structure, base templates, nav, footer, responsive CSS skeleton, logo swap.
3. **Content model + Decap config** — build `config.yml` for all seven collections, wire up Netlify Identity/Git Gateway.
4. **Banner shuffle + news expiry/archive logic** — implement and test with sample data.
5. **Responsive QA** — test at common breakpoints (mobile, tablet, desktop).
6. **Netlify setup** — connect repo, configure custom domain `chess.bc.ca`, enable Identity, invite editors.
7. **Content migration (real)** — move actual production content in.
8. **Cutover** — point DNS from the old PHP host to Netlify; decommission old code once verified.

## 7. Which Claude Product for Which Part

- **This Claude Project ("BC Chess Federation Website")** — planning, architecture decisions, content-model design, drafting/reviewing copy, discussing tradeoffs (like the Decap auth/roles question above), and keeping durable context across sessions without needing repo access. Good for "should we do X or Y" conversations.
- **Claude Code (CLI), run from `~/Projects/Claude/chess.bc.ca`** — all actual implementation: scaffolding Hugo, writing templates/CSS, writing `config.yml`, migrating content out of the old PHP, setting up the GitHub repo and Netlify config, iterating against your local `localhost:8080` dev server. This is where real file edits happen with full repo context — use the `CLAUDE.md` below there.
- **Claude for Excel** — if the Champions list or Arbiters list currently lives in (or would be easiest to clean up in) a spreadsheet before converting to YAML, this is a fast way to tidy that data before Claude Code ingests it.
- **Claude in Chrome** — useful once the dev site is running, to visually check responsive behavior and click through the Decap admin UI as a non-technical editor would.
- **Cowork** — optional; if the content migration turns into a large multi-step research/extraction job across many old pages, Cowork can grind through that in the background. For a site this size, Claude Code alone is probably sufficient.

## 8. Open Items to Confirm With Claude Code (once it has the real files)

- Exact current URL structure, so redirects can be set up (SEO / bookmarks).
- Whether any News/Clubs/etc. content has structure Decap's default widgets don't cleanly capture.
- Real banner count and image dimensions.
- Whether BC Bulletins should also get an expiry/archive treatment similar to News, or stay as a permanent list.
