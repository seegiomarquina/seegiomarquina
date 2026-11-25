import os
import datetime
import urllib.request
import json
import html

USERNAME = "seegiomarquina"
TOKEN = os.environ.get("ACCESS_TOKEN", "")
START_DATE = datetime.date(2024, 8, 1)  # B.Sc. Data Science / Dev start date

GRAPHQL_QUERY = """
query($login: String!) {
  user(login: $login) {
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false) {
      totalCount
      nodes {
        stargazerCount
        languages(first: 5, orderBy: {field: SIZE, direction: DESC}) {
          edges {
            size
            node {
              name
            }
          }
        }
      }
    }
    pullRequests {
      totalCount
    }
    followers {
      totalCount
    }
    contributionsCollection {
      totalCommitContributions
      restrictedContributionsCount
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            contributionCount
            date
          }
        }
      }
    }
  }
}
"""


def fetch_github_stats():
    if not TOKEN:
        raise RuntimeError("ACCESS_TOKEN environment variable is missing.")

    payload = json.dumps({"query": GRAPHQL_QUERY, "variables": {"login": USERNAME}}).encode("utf-8")
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=payload,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "Neofetch-SVG-Generator"
        }
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    user = data["data"]["user"]
    repos = user["repositories"]["totalCount"]
    stars = sum(r["stargazerCount"] for r in user["repositories"]["nodes"])
    prs = user["pullRequests"]["totalCount"]
    followers = user["followers"]["totalCount"]

    contrib = user["contributionsCollection"]
    commits = contrib["totalCommitContributions"] + contrib["restrictedContributionsCount"]
    total_contributions = contrib["contributionCalendar"]["totalContributions"]

    # Language aggregation
    lang_sizes = {}
    for repo in user["repositories"]["nodes"]:
        for edge in repo["languages"]["edges"]:
            name = edge["node"]["name"]
            lang_sizes[name] = lang_sizes.get(name, 0) + edge["size"]

    total_bytes = sum(lang_sizes.values()) or 1
    sorted_langs = sorted(lang_sizes.items(), key=lambda x: x[1], reverse=True)[:3]
    lang_str = " · ".join(f"{name} {round((size / total_bytes) * 100)}%" for name, size in sorted_langs)

    # Flatten contribution days for streak & bottom bar graph
    days = []
    for week in contrib["contributionCalendar"]["weeks"]:
        for day in week["contributionDays"]:
            days.append(day)

    # Calculate current & best streak
    best_streak = 0
    temp_streak = 0
    for d in days:
        if d["contributionCount"] > 0:
            temp_streak += 1
            best_streak = max(best_streak, temp_streak)
        else:
            temp_streak = 0

    current_streak = 0
    for d in reversed(days):
        if d["contributionCount"] > 0:
            current_streak += 1
        elif d["date"] == datetime.date.today().isoformat():
            continue
        else:
            break

    recent_30 = [d["contributionCount"] for d in days[-30:]]

    return {
        "repos": repos,
        "stars": stars,
        "prs": prs,
        "followers": followers,
        "commits": commits,
        "contributions": total_contributions,
        "languages": lang_str or "Python 78% · Jupyter 14% · TypeScript 8%",
        "current_streak": current_streak,
        "best_streak": best_streak,
        "recent_30": recent_30
    }


def calculate_uptime(start_date):
    today = datetime.date.today()
    years = today.year - start_date.year
    months = today.month - start_date.month
    days = today.day - start_date.day

    if days < 0:
        months -= 1
        prev_month = (today.replace(day=1) - datetime.timedelta(days=1))
        days += prev_month.day
    if months < 0:
        years -= 1
        months += 12

    return f"{years} years, {months} months, {days} days"


def make_dot_row(label, value, total_width=64):
    prefix = f". {label}: "
    dots_count = max(2, total_width - len(prefix) - len(str(value)))
    dots = "." * dots_count
    return (
        f'<tspan fill="#00F5D4">. {html.escape(label)}:</tspan> '
        f'<tspan fill="#334155">{dots}</tspan> '
        f'<tspan fill="#E2E8F0">{html.escape(str(value))}</tspan>'
    )


def build_svg(stats):
    with open("assets/ascii_art.txt", "r", encoding="utf-8") as f:
        ascii_lines = [line.rstrip("\n") for line in f.readlines()]

    uptime_str = calculate_uptime(START_DATE)

    right_rows = [
        f'<tspan fill="#00F5D4" font-weight="bold">— adityadhage1@github</tspan>',
        make_dot_row("Uptime", uptime_str),
        "",
        f'<tspan fill="#00F5D4" font-weight="bold">— About Me</tspan>',
        make_dot_row("Education", "B.Sc. Data Science · B.K. Birla College"),
        make_dot_row("Tech Stack", "Python · SQL · PyTorch · FAISS · FastAPI"),
        f'  <tspan fill="#94A3B8">OpenCV · Scikit-Learn · React Native · Power BI</tspan>',
        make_dot_row("Current Focus", "Applied ML · Multimodal AI · Vector Search"),
        make_dot_row("Building", "MindMatters AI · CineVibe · EV Range AI"),
        make_dot_row("Open to", "Data Science &amp; AI Engineering Roles"),
        "",
        f'<tspan fill="#00F5D4" font-weight="bold">— Contact</tspan>',
        make_dot_row("Email", "adityadhage161181@gmail.com"),
        make_dot_row("GitHub", "github.com/adityadhage1"),
        make_dot_row("Portfolio", "AdityaVerse · Hugging Face Spaces"),
        "",
        f'<tspan fill="#00F5D4" font-weight="bold">— GitHub Stats</tspan>',
        (
            f'<tspan fill="#00F5D4">. Repos:</tspan> <tspan fill="#334155">..........</tspan> '
            f'<tspan fill="#F59E0B" font-weight="bold">{stats["repos"]:>4}</tspan>  <tspan fill="#475569">|</tspan>  '
            f'<tspan fill="#00F5D4">. Stars:</tspan> <tspan fill="#334155">..........</tspan> '
            f'<tspan fill="#F59E0B" font-weight="bold">{stats["stars"]:>4}</tspan>'
        ),
        (
            f'<tspan fill="#00F5D4">. Commits:</tspan> <tspan fill="#334155">........</tspan> '
            f'<tspan fill="#F59E0B" font-weight="bold">{stats["commits"]:>4}</tspan>  <tspan fill="#475569">|</tspan>  '
            f'<tspan fill="#00F5D4">. PRs:</tspan> <tspan fill="#334155">............</tspan> '
            f'<tspan fill="#F59E0B" font-weight="bold">{stats["prs"]:>4}</tspan>'
        ),
        (
            f'<tspan fill="#00F5D4">. Contributions:</tspan> <tspan fill="#334155">..</tspan> '
            f'<tspan fill="#F59E0B" font-weight="bold">{stats["contributions"]:>4}</tspan>  <tspan fill="#475569">|</tspan>  '
            f'<tspan fill="#00F5D4">. Followers:</tspan> <tspan fill="#334155">......</tspan> '
            f'<tspan fill="#F59E0B" font-weight="bold">{stats["followers"]:>4}</tspan>'
        ),
        make_dot_row("Streak", f'{stats["current_streak"]} days (best {stats["best_streak"]})'),
        make_dot_row("Languages", stats["languages"]),
    ]

    # Render ASCII art on the left
    ascii_svg = []
    for idx, line in enumerate(ascii_lines):
        y = 55 + idx * 20
        color = "#00F5D4" if idx % 2 == 0 else "#10B981"
        ascii_svg.append(
            f'<text x="32" y="{y}" fill="{color}" font-family="JetBrains Mono, Fira Code, Consolas, monospace" '
            f'font-size="13" xml:space="preserve">{html.escape(line)}</text>'
        )

    # Render telemetry rows on the right
    info_svg = []
    for idx, row in enumerate(right_rows):
        if not row:
            continue
        y = 45 + idx * 21
        info_svg.append(
            f'<text x="430" y="{y}" font-family="JetBrains Mono, Fira Code, Consolas, monospace" '
            f'font-size="13.5" xml:space="preserve">{row}</text>'
        )

    # Render 30-day contribution bar chart at bottom right
    bars_svg = []
    max_val = max(stats["recent_30"] + [1])
    for i, val in enumerate(stats["recent_30"]):
        bar_h = max(3, int((val / max_val) * 26))
        x = 430 + i * 18
        y = 528 - bar_h
        fill = "#10B981" if val > 0 else "#1E293B"
        bars_svg.append(f'<rect x="{x}" y="{y}" width="13" height="{bar_h}" rx="2" fill="{fill}" />')

    svg_content = f"""<svg width="1020" height="555" viewBox="0 0 1020 555" xmlns="http://www.w3.org/2000/svg">
  <rect x="2" y="2" width="1016" height="551" rx="12" fill="#0A0A0B" stroke="#1E293B" stroke-width="2"/>
  <circle cx="24" cy="20" r="5.5" fill="#EF4444"/>
  <circle cx="42" cy="20" r="5.5" fill="#F59E0B"/>
  <circle cx="60" cy="20" r="5.5" fill="#10B981"/>
  <text x="510" y="24" text-anchor="middle" fill="#64748B" font-family="JetBrains Mono, Consolas, monospace" font-size="12">adityadhage1@arch-ds: ~/neofetch</text>
  <line x1="2" y1="34" x2="1018" y2="34" stroke="#1E293B" stroke-width="1"/>
  {''.join(ascii_svg)}
  {''.join(info_svg)}
  {''.join(bars_svg)}
</svg>"""

    with open("dark_mode.svg", "w", encoding="utf-8") as f:
        f.write(svg_content)


if __name__ == "__main__":
    stats = fetch_github_stats()
    build_svg(stats)
