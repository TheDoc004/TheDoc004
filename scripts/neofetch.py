"""Draws the neofetch-style card at the top of the profile README.

Writes assets/neofetch-dark.svg and assets/neofetch-light.svg. With a GITHUB_TOKEN (or GH_TOKEN)
in the environment it pulls live stats from the GitHub API; without one it uses the fallbacks below.
If assets/me.jpg exists and Pillow is installed, the duck is swapped for an ASCII portrait of you.

    python3 scripts/neofetch.py
"""

import json
import os
import urllib.request
from datetime import date
from pathlib import Path
from xml.sax.saxutils import escape

USER = "TheDoc004"
ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
WIDTH = 60  # characters per info line, dots included

DUCK = r"""
                _.-----._
             .-'         '-.
            /    _     _    \
           |    (o)   (o)    |
           |   ___________   |
           |  [___|___|___]  |
            \    \_____/    /
             '-._       _.-'__
          _.-'   '-----'   '--'-.
       .-'                       '.
      /     .-~~~~~~~~~~~~~~-.     \
     |     /  git commit -m   \     |
     |    |   "quack (wip)"    |    |
     |     \                  /     |
      \     '-..__________..-'     /
       '-._                     _.-'
           '"--..........--""'
""".strip("\n").split("\n")

FALLBACK_STATS = {"repos": 10, "stars": 1, "followers": 0, "commits": 357}


def info_lines(stats):
    """The right-hand column. ("key", "value") pairs, "--- Title" section rules, or "" spacers."""
    return [
        ("@", "diego@thedoc004"),
        "--- ",
        ("OS", "macOS, iOS, caffeine"),
        ("Host", "San Diego State University (MIS)"),
        ("Kernel", "business brain, engineer hands"),
        ("Uptime", f"{(date.today() - date(2026, 5, 18)).days} days on GitHub"),
        ("IDE", "Claude Code, VS Code, a Telegram chat"),
        "",
        ("Languages.Programming", "Python, TypeScript, JavaScript"),
        ("Languages.Data", "SQL, JSON, YAML"),
        ("Frameworks", "React, Next.js, FastAPI, Electron"),
        ("AI", "LLM agents, MCP, tool use, voice"),
        ("Infra", "SQLite, Postgres, Vercel, Render"),
        "",
        ("Hobbies.Software", "agents that manage my agents"),
        ("Hobbies.Hardware", "chess, lifting, Brawlhalla"),
        ("Diet", "macro-tracked (I built an app)"),
        "",
        "--- Side Quests",
        ("11/08", "SDxSDSU Voice Agent Hackathon"),
        ("11/14", "SanD Hacks @ UCSD"),
        "",
        "--- GitHub Stats",
        ("Repos", f"{stats['repos']}  |  Stars: {stats['stars']}"),
        ("Commits (1y)", f"{stats['commits']}  |  Followers: {stats['followers']}"),
    ]


def graphql(token, query):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query}).encode(),
        headers={"Authorization": f"bearer {token}", "User-Agent": USER},
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.load(resp)["data"]


def fetch_stats():
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        return FALLBACK_STATS
    try:
        u = graphql(token, f"""{{ user(login: "{USER}") {{
            followers {{ totalCount }}
            repositories(ownerAffiliations: OWNER, first: 100) {{
                totalCount nodes {{ stargazerCount }} }}
            contributionsCollection {{ totalCommitContributions restrictedContributionsCount }}
        }} }}""")["user"]
    except Exception as err:  # a broken stats call shouldn't break the card
        print(f"stats fetch failed, using fallbacks: {err}")
        return FALLBACK_STATS
    cc = u["contributionsCollection"]
    return {
        "repos": u["repositories"]["totalCount"],
        "stars": sum(r["stargazerCount"] for r in u["repositories"]["nodes"]),
        "followers": u["followers"]["totalCount"],
        "commits": cc["totalCommitContributions"] + cc["restrictedContributionsCount"],
    }


def portrait(path, cols=38, rows=20):
    """ASCII portrait from a photo; None if there's no photo or no Pillow."""
    try:
        from PIL import Image, ImageOps
    except ImportError:
        return None
    if not path.exists():
        return None
    ramp = " .:-=+*#%@"
    img = ImageOps.grayscale(Image.open(path)).resize((cols, rows))
    img = ImageOps.autocontrast(img)
    px = list(img.getdata())
    return ["".join(ramp[(255 - px[r * cols + c]) * (len(ramp) - 1) // 255] for c in range(cols))
            for r in range(rows)]


THEMES = {
    "dark": {"bg": "#161b22", "border": "#30363d", "text": "#c9d1d9", "key": "#ffa657",
             "value": "#a5d6ff", "dots": "#616e7f", "art": "#7ee787", "bar": "#21262d"},
    "light": {"bg": "#f6f8fa", "border": "#d0d7de", "text": "#24292f", "key": "#953800",
              "value": "#0a3069", "dots": "#c2cfde", "art": "#1a7f37", "bar": "#eaeef2"},
}


def svg(theme, art, lines):
    t = THEMES[theme]
    lh, top, art_x, info_x = 20, 52, 20, 410
    height = top + max(len(art), len(lines)) * lh + 20
    art_top = top + (len(lines) - len(art)) * lh // 2

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" font-family="ui-monospace,SFMono-Regular,Consolas,'
        f'Menlo,monospace" width="985" height="{height}" font-size="15px">',
        "<style>",
        f".key{{fill:{t['key']}}}.value{{fill:{t['value']}}}.dots{{fill:{t['dots']}}}",
        f".art{{fill:{t['art']}}}text,tspan{{white-space:pre}}",
        "</style>",
        f'<rect width="985" height="{height}" rx="12" fill="{t["bg"]}" stroke="{t["border"]}"/>',
        f'<path d="M0 12a12 12 0 0 1 12-12h961a12 12 0 0 1 12 12v18H0z" fill="{t["bar"]}"/>',
        '<circle cx="20" cy="15" r="6" fill="#ff5f57"/><circle cx="40" cy="15" r="6" fill="#febc2e"/>'
        '<circle cx="60" cy="15" r="6" fill="#28c840"/>',
        f'<text x="492" y="20" text-anchor="middle" fill="{t["dots"]}" font-size="13px">'
        f"diego@thedoc004: ~ — neofetch</text>",
        f'<text x="{art_x}" y="{art_top}" class="art">',
    ]
    for i, row in enumerate(art):
        out.append(f'<tspan x="{art_x}" y="{art_top + i * lh}">{escape(row)}</tspan>')
    out.append("</text>")

    out.append(f'<text x="{info_x}" y="{top}" fill="{t["text"]}">')
    for i, line in enumerate(lines):
        y = top + i * lh
        if line == "":
            continue
        if isinstance(line, str):  # section rule
            title = line[4:]
            rule = f"- {title} " if title else ""
            out.append(f'<tspan x="{info_x}" y="{y}">{escape(rule)}{"—" * (WIDTH - len(rule) - 4)}</tspan>')
            continue
        key, value = line
        if key == "@":
            out.append(f'<tspan x="{info_x}" y="{y}" class="key" font-weight="bold">{escape(value)}</tspan>')
            continue
        dots = "." * max(2, WIDTH - len(key) - len(value) - 6)
        out.append(
            f'<tspan x="{info_x}" y="{y}">. </tspan><tspan class="key">{escape(key)}</tspan>:'
            f'<tspan class="dots"> {dots} </tspan><tspan class="value">{escape(value)}</tspan>'
        )
    out.append("</text></svg>")
    return "\n".join(out)


def main():
    stats = fetch_stats()
    art = portrait(ASSETS / "me.jpg") or DUCK
    lines = info_lines(stats)
    ASSETS.mkdir(exist_ok=True)
    for theme in THEMES:
        (ASSETS / f"neofetch-{theme}.svg").write_text(svg(theme, art, lines))
    print(f"wrote neofetch cards with {stats}")


if __name__ == "__main__":
    main()
