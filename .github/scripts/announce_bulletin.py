"""Create a "Bulletin #N Posted" news item for each newly added bulletin.

Invoked by .github/workflows/announce-bulletin.yml with the push's
before/after commit SHAs. Only *added* files in content/bulletins/ count —
edits to existing bulletins never produce a second announcement, and a
bulletin that already has an announcement is skipped, so the script is
safe to re-run.
"""

import datetime
import glob
import re
import subprocess
import sys

BEFORE, AFTER = sys.argv[1], sys.argv[2]
if set(BEFORE) == {"0"}:  # first push / force push: fall back to one commit
    BEFORE = AFTER + "~1"

added = subprocess.run(
    ["git", "diff", "--name-only", "--diff-filter=A", BEFORE, AFTER,
     "--", "content/bulletins/*.md"],
    capture_output=True, text=True, check=True,
).stdout.split()

for path in added:
    if path.endswith("_index.md"):
        continue
    src = open(path, encoding="utf-8").read()

    def field(name):
        m = re.search(rf'^{name}:\s*"?([^"\n]+)"?\s*$', src, re.M)
        return m.group(1).strip() if m else None

    number, pdf, date = field("number"), field("pdf"), field("date")
    if not number or not pdf:
        print(f"skip {path}: missing number or pdf front matter")
        continue
    if glob.glob(f"content/news/*bulletin-{number}-posted.md"):
        print(f"skip {path}: news item for bulletin {number} already exists")
        continue

    posted = (datetime.date.fromisoformat(date[:10]) if date
              else datetime.date.today())
    expiry = posted + datetime.timedelta(days=14)
    out = f"{posted.isoformat()}-bulletin-{number}-posted.md"
    open(f"content/news/{out}", "w", encoding="utf-8").write(
        f'---\n'
        f'type: news\n'
        f'title: "Bulletin #{number} Posted"\n'
        f'date: {posted.isoformat()}\n'
        f'expiry_date: {expiry.isoformat()}\n'
        f'---\n\n'
        f'[BC Bulletin #{number}]({pdf}) has been posted!\n'
    )
    print(f"created content/news/{out}")
