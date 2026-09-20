#!/usr/bin/env python3
"""apps/ 以下の HTML を集めて、公開用サイト (_site/) を組み立てるスクリプト。

使いかた:
    python3 scripts/build.py          # _site/ を作りなおす

アプリの置きかた:
    apps/<なまえ>/index.html          # フォルダ型（画像やCSSも一緒に置ける）
    apps/<なまえ>.html                # 1ファイル型

apps/<なまえ>/app.json（任意）で、トップページのカードの見た目を上書きできる:
    {"title": "...", "description": "...", "emoji": "🧪", "order": 1}
なければ HTML の <title> と <meta name="description"> から自動で拾う。
"""

from __future__ import annotations

import html
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APPS_DIR = ROOT / "apps"
OUT_DIR = ROOT / "_site"

SITE_TITLE = "キッズ がくしゅうアプリ"
SITE_SUBTITLE = "あそびながら まなべる ミニアプリ あつめ"

DEFAULT_EMOJIS = ["🌟", "🚀", "🎨", "🔢", "🦕", "🌏", "🎵", "🧠"]
CARD_COLORS = [
    ("#f472b6", "#fb7185"),
    ("#fbbf24", "#fb923c"),
    ("#34d399", "#0d9488"),
    ("#60a5fa", "#6366f1"),
    ("#c084fc", "#a855f7"),
    ("#22d3ee", "#0ea5e9"),
]

TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
DESC_RE = re.compile(
    r"""<meta\s+[^>]*name=["']description["'][^>]*content=["'](.*?)["']""",
    re.IGNORECASE | re.DOTALL,
)


def read_meta_from_html(html_path: Path) -> dict:
    """HTML の <title> と <meta name="description"> を読む。"""
    text = html_path.read_text(encoding="utf-8", errors="replace")
    meta = {}
    m = TITLE_RE.search(text)
    if m:
        meta["title"] = html.unescape(re.sub(r"\s+", " ", m.group(1))).strip()
    m = DESC_RE.search(text)
    if m:
        meta["description"] = html.unescape(re.sub(r"\s+", " ", m.group(1))).strip()
    return meta


def collect_apps() -> list[dict]:
    """apps/ を走査して、公開するアプリの一覧を作る。"""
    apps = []
    if not APPS_DIR.is_dir():
        return apps

    for path in sorted(APPS_DIR.iterdir()):
        if path.name.startswith((".", "_")):
            continue

        if path.is_dir() and (path / "index.html").is_file():
            slug, entry, href = path.name, path / "index.html", f"apps/{path.name}/"
        elif path.is_file() and path.suffix.lower() == ".html":
            slug, entry, href = path.stem, path, f"apps/{path.name}"
        else:
            continue

        info = {"slug": slug, "href": href, "title": slug, "description": "", "order": 999}
        info.update(read_meta_from_html(entry))

        config = path / "app.json" if path.is_dir() else path.with_suffix(".json")
        if config.is_file():
            info.update(json.loads(config.read_text(encoding="utf-8")))

        apps.append(info)

    apps.sort(key=lambda a: (a.get("order", 999), a["title"]))
    return apps


def render_index(apps: list[dict]) -> str:
    """トップページ（アプリ一覧）の HTML を組み立てる。"""
    if apps:
        cards = "\n".join(render_card(app, i) for i, app in enumerate(apps))
    else:
        cards = '<p class="empty">まだアプリがありません。apps/ に HTML を追加してね。</p>'

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(SITE_TITLE)}</title>
<meta name="description" content="{html.escape(SITE_SUBTITLE)}">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🎒</text></svg>">
<link href="https://fonts.googleapis.com/css2?family=M+PLUS+Rounded+1c:wght@400;700;900&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    font-family: 'M PLUS Rounded 1c', system-ui, sans-serif;
    background: #fffbeb;
    color: #1e293b;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }}
  header {{
    background: linear-gradient(120deg, #2dd4bf, #38bdf8, #818cf8);
    color: #fff;
    padding: 48px 16px 56px;
    text-align: center;
  }}
  header h1 {{ margin: 0 0 8px; font-size: clamp(1.8rem, 6vw, 3rem); font-weight: 900; letter-spacing: .04em; }}
  header p {{ margin: 0; font-weight: 700; opacity: .92; font-size: clamp(.85rem, 3vw, 1rem); }}
  main {{ flex: 1; width: 100%; max-width: 960px; margin: -28px auto 0; padding: 0 16px 48px; }}
  .grid {{ display: grid; gap: 20px; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); }}
  .card {{
    display: flex;
    flex-direction: column;
    gap: 10px;
    padding: 24px;
    border-radius: 24px;
    border: 4px solid #fff;
    color: #fff;
    text-decoration: none;
    box-shadow: 0 10px 25px rgba(15, 23, 42, .12);
    transition: transform .2s cubic-bezier(.175,.885,.32,1.275), box-shadow .2s;
    position: relative;
    overflow: hidden;
  }}
  .card:hover, .card:focus-visible {{ transform: translateY(-4px) scale(1.02); box-shadow: 0 16px 32px rgba(15, 23, 42, .2); }}
  .card:active {{ transform: scale(.98); }}
  .card .emoji {{ font-size: 2.6rem; line-height: 1; }}
  .card h2 {{ margin: 0; font-size: 1.35rem; font-weight: 900; }}
  .card p {{ margin: 0; font-size: .9rem; font-weight: 700; opacity: .95; line-height: 1.6; }}
  .card .go {{
    margin-top: auto; align-self: flex-start;
    background: #fff; color: #334155; font-weight: 900; font-size: .85rem;
    padding: 8px 18px; border-radius: 999px;
  }}
  .empty {{ font-weight: 700; color: #64748b; text-align: center; }}
  footer {{ text-align: center; padding: 20px; font-size: .75rem; font-weight: 700; color: #94a3b8; }}
  @media (prefers-color-scheme: dark) {{
    body {{ background: #0f172a; color: #e2e8f0; }}
    .card {{ border-color: rgba(255,255,255,.18); }}
    .card .go {{ background: rgba(15,23,42,.85); color: #f1f5f9; }}
    .empty {{ color: #94a3b8; }}
  }}
</style>
</head>
<body>
<header>
  <h1>🎒 {html.escape(SITE_TITLE)}</h1>
  <p>{html.escape(SITE_SUBTITLE)}</p>
</header>
<main>
  <div class="grid">
{cards}
  </div>
</main>
<footer>© 2026 kids apps</footer>
</body>
</html>
"""


def render_card(app: dict, index: int) -> str:
    start, end = CARD_COLORS[index % len(CARD_COLORS)]
    emoji = app.get("emoji") or DEFAULT_EMOJIS[index % len(DEFAULT_EMOJIS)]
    desc = app.get("description") or ""
    desc_html = f'\n      <p>{html.escape(desc)}</p>' if desc else ""
    return (
        f'    <a class="card" href="{html.escape(app["href"])}" '
        f'style="background: linear-gradient(135deg, {start}, {end});">\n'
        f'      <span class="emoji">{html.escape(emoji)}</span>\n'
        f'      <h2>{html.escape(app["title"])}</h2>{desc_html}\n'
        f'      <span class="go">あそぶ →</span>\n'
        f"    </a>"
    )


def main() -> None:
    apps = collect_apps()

    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True)

    if APPS_DIR.is_dir():
        shutil.copytree(APPS_DIR, OUT_DIR / "apps")

    (OUT_DIR / "index.html").write_text(render_index(apps), encoding="utf-8")
    (OUT_DIR / ".nojekyll").write_text("", encoding="utf-8")

    print(f"built {len(apps)} app(s) -> {OUT_DIR.relative_to(ROOT)}/")
    for app in apps:
        print(f"  - {app['title']}  ({app['href']})")


if __name__ == "__main__":
    main()
