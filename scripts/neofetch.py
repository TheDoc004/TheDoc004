"""Draws the neofetch-style card at the top of the profile README.

Writes assets/neofetch-dark.svg and assets/neofetch-light.svg. With a GITHUB_TOKEN (or GH_TOKEN)
in the environment it pulls live stats from the GitHub API; without one it uses the fallbacks below.
If assets/portrait.txt exists, it replaces the duck. Make one from a photo (needs Pillow; the photo
itself never goes in the repo):

    python3 scripts/neofetch.py
    python3 scripts/neofetch.py ~/me.jpg 200,600,700,1300   # optional crop: left,top,right,bottom
"""

import json
import os
import sys
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


def portrait_from_photo(path, crop=None, cols=76, rows=52):
    """Turns a photo into ASCII art lines (needs Pillow). crop is (left, top, right, bottom).
    Dark pixels get dense characters: a positive on the light card, a glowing negative on the dark
    one, and dark hair carries the silhouette either way. The edges fade out in an oval so the
    background doesn't fight the face."""
    from PIL import Image, ImageOps

    img = Image.open(path)
    if crop:
        img = img.crop(crop)
    img = ImageOps.equalize(ImageOps.grayscale(img).resize((cols, rows)))
    px = list(img.get_flattened_data())
    ramp = " .:-=+*#%@"
    out = []
    for r in range(rows):
        row = ""
        for c in range(cols):
            d = ((c - cols / 2) / (cols / 2)) ** 2 + ((r - rows / 2) / (rows / 2)) ** 2
            v = int((255 - px[r * cols + c]) * max(0.0, min(1.0, (1.08 - d) / 0.3)))  # oval fade
            row += ramp[v * (len(ramp) - 1) // 255]
        out.append(row.rstrip())
    return out


def portrait():
    """The saved ASCII portrait (assets/portrait.txt), or None to fall back to the duck."""
    path = ASSETS / "portrait.txt"
    return path.read_text().rstrip("\n").split("\n") if path.exists() else None


THEMES = {
    "dark": {"bg": "#161b22", "border": "#30363d", "text": "#c9d1d9", "key": "#ffa657",
             "value": "#a5d6ff", "dots": "#616e7f", "art": "#7ee787", "bar": "#21262d"},
    "light": {"bg": "#f6f8fa", "border": "#d0d7de", "text": "#24292f", "key": "#953800",
              "value": "#0a3069", "dots": "#c2cfde", "art": "#1a7f37", "bar": "#eaeef2"},
}


def svg(theme, art, lines):
    t = THEMES[theme]
    lh, top, art_x, info_x = 20, 52, 20, 410
    height = top + len(lines) * lh
    # a big portrait shrinks to the height of the info column; the duck stays at full size
    art_lh = min(lh, (len(lines) * lh) / len(art))
    art_font = f' font-size="{art_lh * 0.8:.1f}px"' if art_lh < lh else ""
    art_top = top - 14 + (len(lines) * lh - len(art) * art_lh) / 2 + art_lh * 0.75

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
        f'<text x="{art_x}" y="{art_top:.1f}" class="art"{art_font}>',
    ]
    for i, row in enumerate(art):
        out.append(f'<tspan x="{art_x}" y="{art_top + i * art_lh:.1f}">{escape(row)}</tspan>')
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
    if len(sys.argv) > 1:  # neofetch.py photo.jpg [left,top,right,bottom]: save a new portrait
        crop = tuple(int(n) for n in sys.argv[2].split(",")) if len(sys.argv) > 2 else None
        (ASSETS / "portrait.txt").write_text("\n".join(portrait_from_photo(sys.argv[1], crop)) + "\n")
    stats = fetch_stats()
    art = portrait() or DUCK
    lines = info_lines(stats)
    ASSETS.mkdir(exist_ok=True)
    for theme in THEMES:
        (ASSETS / f"neofetch-{theme}.svg").write_text(svg(theme, art, lines))
    print(f"wrote neofetch cards with {stats}")


if __name__ == "__main__":
    main()
