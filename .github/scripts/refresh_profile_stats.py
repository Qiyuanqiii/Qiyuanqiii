"""Refresh public PR counts and OpenCodeReview commit rank.

The figures come from GitHub's REST API. Run with GITHUB_TOKEN
set; the script leaves existing files untouched if any API request fails.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import re
import urllib.parse
import urllib.request


ROOT = Path(__file__).resolve().parents[2]
USER = "Qiyuanqiii"
COMMUNITY = "alibaba/open-code-review"
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
if not TOKEN:
    raise SystemExit("Set GITHUB_TOKEN or GH_TOKEN before refreshing profile stats")


def github(url: str):
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {TOKEN}",
            "User-Agent": "Qiyuanqiii-profile-stats",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        result = json.load(response)
    if isinstance(result, dict) and result.get("errors"):
        raise ValueError(result["errors"])
    return result


def search_count(query: str) -> int:
    params = urllib.parse.urlencode({"q": query, "per_page": 1})
    result = github(f"https://api.github.com/search/issues?{params}")
    if result.get("incomplete_results"):
        raise ValueError(f"GitHub returned incomplete search results for {query}")
    return result["total_count"]


def contributor_rank() -> tuple[int, int, int]:
    people = []
    for page in range(1, 21):
        batch = github(
            f"https://api.github.com/repos/{COMMUNITY}/contributors?per_page=100&page={page}"
        )
        if not isinstance(batch, list):
            raise ValueError("Contributor list is unavailable")
        people.extend(batch)
        if len(batch) < 100:
            break
    else:
        raise ValueError("Contributor list exceeded the pagination limit")
    humans = [
        person for person in people
        if person.get("type") != "Bot" and not person.get("login", "").endswith("[bot]")
    ]
    for position, person in enumerate(humans, start=1):
        if person.get("login", "").lower() == USER.lower():
            return position, len(humans), person["contributions"]
    raise ValueError(f"{USER} is absent from the contributor list")


def replace_once(text: str, pattern: str, replacement: str) -> str:
    updated, count = re.subn(pattern, lambda _: replacement, text, count=1, flags=re.S)
    if count != 1:
        raise ValueError(f"Expected one README match for: {pattern}")
    return updated


def update_readme(readme: str, prs: int, merged: int, rank: int, people: int, commits: int, today: str) -> str:
    if 'id="pr-snapshot"' not in readme:
        marker = '<p align="center">📬 <strong>Connect</strong></p>'
        if readme.count(marker) != 1:
            raise ValueError("Could not place the PR snapshot")
        newline = "\r\n" if "\r\n" in readme else "\n"
        readme = readme.replace(marker, '<p align="center"><sub id="pr-snapshot"></sub></p>' + newline * 2 + marker)
    readme = replace_once(
        readme,
        r'(?:<a href="https://github\.com/pulls\?q=is%3Apr\+author%3AQiyuanqiii(?:\+is%3Apublic)?">)?<img src="(?:https://img\.shields\.io/badge/Open%20Source-[^"]+|\./assets/open-source-prs\.svg)" alt="[^"]+" />(?:</a>)?',
        (f'<a href="https://github.com/pulls?q=is%3Apr+author%3A{USER}+is%3Apublic">'
         f'<img src="https://img.shields.io/badge/Open%20Source-{prs}%20PRs%20%C2%B7%20{merged}%20Merged-2EA44F?style=for-the-badge&logo=git&logoColor=white" '
         f'alt="{prs} public authored pull requests, {merged} merged" /></a>'),
    )
    readme = replace_once(
        readme,
        r'<sub id="pr-snapshot">.*?</sub>',
        (f'<sub id="pr-snapshot">{prs} public PRs authored · {merged} merged · '
         f'includes personal repositories · snapshot {today} · '
         f'<a href="https://github.com/pulls?q=is%3Apr+author%3A{USER}+is%3Apublic">GitHub search</a></sub>'),
    )
    readme = replace_once(
        readme,
        r'\*\*(?:Human|Commit) contributor rank: #[0-9]+ / [0-9]+\*\*',
        f'**Commit contributor rank: #{rank} / {people}**',
    )
    readme = replace_once(
        readme,
        r'alt="OpenCodeReview — (?:human|commit) contributor rank #[0-9]+ / [0-9]+\.[^"]+"',
        f'alt="OpenCodeReview — commit contributor rank #{rank} / {people}. Issue assessment, PR review, personal-branch SVN support, and validation and fixes. Full text follows."',
    )
    readme = replace_once(
        readme,
        r'<sub>Snapshot: .*?\[My pull requests\]\(https://github\.com/alibaba/open-code-review/pulls\?q=is%3Apr\+author%3AQiyuanqiii\)</sub>',
        (f'<sub>Snapshot: {today}. Ranked by {commits} attributed commits in '
         f'[GitHub\'s contributor list](https://github.com/{COMMUNITY}/graphs/contributors); '
         f'bots excluded from both rank and total. Reviews and issues are separate from this rank. '
         f'[My pull requests](https://github.com/{COMMUNITY}/pulls?q=is%3Apr+author%3A{USER})</sub>'),
    )
    if "contribution-activity.svg" in readme or "github-readme-activity-graph.vercel.app" in readme:
        readme = replace_once(
            readme,
            r'<p align="center">\r?\n  <img width="900" src="(?:https://github-readme-activity-graph\.vercel\.app/[^"]+|\./assets/contribution-activity\.svg)" alt="(?:Contribution activity graph|Weekly GitHub contribution activity over the past year)" loading="lazy" decoding="async" />\r?\n</p>\r?\n\r?\n',
            "",
        )
    old_about = "The streak, trophy, contribution calendar, and snake animations on this page are regenerated automatically by [GitHub Actions](./.github/workflows) and committed back to this repository. Only the [README](./README.md) and the [assets](./assets) are hand-maintained."
    current_about = "The PR badge, commit rank, activity graph, streak, trophy, contribution calendar, and snake animations are refreshed by [GitHub Actions](./.github/workflows). The rank uses GitHub's contributor API and counts attributed commits; the PR badge counts public PRs authored across GitHub, including personal repositories. Other prose and artwork are maintained in this repository."
    new_about = "The PR badge, commit rank, streak, trophy, contribution calendar, and snake animations are refreshed by [GitHub Actions](./.github/workflows). The rank uses GitHub's contributor API and counts attributed commits; the PR badge counts public PRs authored across GitHub, including personal repositories. Other prose and artwork are maintained in this repository."
    if old_about in readme:
        readme = readme.replace(old_about, new_about, 1)
    elif current_about in readme:
        readme = readme.replace(current_about, new_about, 1)
    return readme


def main():
    prs = search_count(f"is:pr author:{USER} is:public")
    merged = search_count(f"is:pr author:{USER} is:merged is:public")
    rank, people, commits = contributor_rank()
    local_day = datetime.now(timezone(timedelta(hours=8)))
    today = f"{local_day.day} {local_day.strftime('%B %Y')}"
    readme_path = ROOT / "README.md"
    readme = update_readme(readme_path.read_bytes().decode("utf-8"), prs, merged, rank, people, commits, today)
    readme_path.write_bytes(readme.encode("utf-8"))
    print(f"Public PRs {prs} / {merged} merged; commit rank #{rank} / {people} ({commits} commits)")


if __name__ == "__main__":
    main()
