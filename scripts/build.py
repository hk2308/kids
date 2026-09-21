#!/usr/bin/env python3
"""apps/ 以下の HTML を集めて、公開用サイト (_site/) を組み立てるスクリプト。

使いかた:
    python3 scripts/build.py          # index.html と _site/ を作りなおす

アプリの置きかた:
    apps/<なまえ>/index.html          # フォルダ型（画像やCSSも一緒に置ける）
    apps/<なまえ>.html                # 1ファイル型

apps/<なまえ>/app.json（任意）で、トップページのカードの見た目を上書きできる:
    {"title": "...", "description": "...", "emoji": "🧪", "group": "理科", "order": 1}
なければ HTML の <title> と <meta name="description"> から自動で拾う。

group は下の GROUPS にある名前を書く（ないものは「そのた」にまとめられる）。
トップページでは group ごとに見出しが付き、チップと検索でしぼりこめる。
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
INDEX_FILE = ROOT / "index.html"

SITE_TITLE = "キッズ がくしゅうアプリ"
SITE_SUBTITLE = "あそびながら まなべる ミニアプリ あつめ"

# (グループ名, 絵文字, カードの色, ひとこと説明)
GROUPS: list[tuple[str, str, tuple[str, str], str]] = [
    ("算数", "🔢", ("#60a5fa", "#4f46e5"), "かず・計算・そろばん"),
    ("ことば", "✍️", ("#f472b6", "#e11d48"), "ひらがな・漢字・ことわざ"),
    ("理科", "🔬", ("#34d399", "#0f766e"), "元素・分子・じっけん・色"),
    ("社会", "🗾", ("#fbbf24", "#ea580c"), "地図・鉄道・歴史"),
    ("受験", "🎓", ("#c084fc", "#7e22ce"), "小学校受験・中学受験の4教科"),
    ("パズル", "🧩", ("#22d3ee", "#0369a1"), "あたまを つかう あそび"),
    ("音・アート", "🎵", ("#fb923c", "#db2777"), "リズム・絵・デザイン"),
    ("くらし・AI", "💡", ("#a3e635", "#15803d"), "きせつ・おかね・きもち・AI"),
]
OTHER = ("そのた", "🌟", ("#94a3b8", "#475569"), "")
GROUP_INDEX = {name: i for i, (name, *_rest) in enumerate(GROUPS)}

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

        if info.get("group") not in GROUP_INDEX:
            info["group"] = OTHER[0]

        apps.append(info)

    apps.sort(key=lambda a: (a.get("order", 999), a["title"]))
    return apps


def group_defs(apps: list[dict]) -> list[tuple[str, str, tuple[str, str], str]]:
    """じっさいに アプリが ある グループだけ、きめた じゅんばんで かえす。"""
    used = {a["group"] for a in apps}
    out = [g for g in GROUPS if g[0] in used]
    if OTHER[0] in used:
        out.append(OTHER)
    return out


def render_index(apps: list[dict]) -> str:
    """トップページ（アプリ一覧）の HTML を組み立てる。"""
    defs = group_defs(apps)
    colors = {name: cols for name, _e, cols, _d in defs}

    chips = [
        '<button class="chip on" data-chip="all" type="button">'
        f'🎒 ぜんぶ <span class="n">{len(apps)}</span></button>'
    ]
    for name, emoji, (start, _end), _desc in defs:
        n = sum(1 for a in apps if a["group"] == name)
        chips.append(
            f'<button class="chip" data-chip="{html.escape(name)}" type="button" '
            f'style="--dot: {start};">{html.escape(emoji)} {html.escape(name)} '
            f'<span class="n">{n}</span></button>'
        )

    sections = []
    for name, emoji, (start, end), desc in defs:
        mine = [a for a in apps if a["group"] == name]
        if not mine:
            continue
        cards = "\n".join(render_card(a, colors) for a in mine)
        sections.append(
            f'  <section class="group" data-group="{html.escape(name)}">\n'
            f'    <h2 class="gtitle" style="--from: {start}; --to: {end};">'
            f'<span class="gemoji">{html.escape(emoji)}</span>{html.escape(name)}'
            f'<span class="gdesc">{html.escape(desc)}</span>'
            f'<span class="gn">{len(mine)}</span></h2>\n'
            f'    <div class="grid">\n{cards}\n    </div>\n'
            f"  </section>"
        )
    body = "\n".join(sections) if sections else (
        '  <p class="empty">まだアプリがありません。apps/ に HTML を追加してね。</p>'
    )

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
    padding: 40px 16px 48px;
    text-align: center;
  }}
  header h1 {{ margin: 0 0 8px; font-size: clamp(1.8rem, 6vw, 3rem); font-weight: 900; letter-spacing: .04em; }}
  header p {{ margin: 0; font-weight: 700; opacity: .92; font-size: clamp(.85rem, 3vw, 1rem); }}
  header .count {{
    display: inline-block; margin-top: 14px; padding: 5px 16px;
    background: rgba(255, 255, 255, .22); border: 1px solid rgba(255, 255, 255, .4);
    border-radius: 999px; font-size: .8rem;
  }}

  .bar {{
    position: sticky; top: 0; z-index: 20;
    background: rgba(255, 251, 235, .95);
    backdrop-filter: blur(8px);
    border-bottom: 2px solid #fde68a;
    padding: 10px 16px;
  }}
  .bar-in {{ max-width: 960px; margin: 0 auto; display: flex; flex-direction: column; gap: 8px; }}
  .chips {{ display: flex; gap: 8px; overflow-x: auto; padding-bottom: 2px; scrollbar-width: none; }}
  .chips::-webkit-scrollbar {{ display: none; }}
  .chip {{
    flex: none; display: inline-flex; align-items: center; gap: 6px;
    font-family: inherit; font-weight: 900; font-size: .85rem;
    padding: 7px 14px; border-radius: 999px; cursor: pointer;
    background: #fff; color: #475569; border: 2px solid #e2e8f0;
    transition: transform .12s cubic-bezier(.175,.885,.32,1.275);
  }}
  .chip:active {{ transform: scale(.94); }}
  .chip .n {{ font-size: .72rem; opacity: .7; font-variant-numeric: tabular-nums; }}
  .chip.on {{ background: #1e293b; color: #fff; border-color: #1e293b; }}
  .chip[style*="--dot"].on {{ background: var(--dot); border-color: var(--dot); color: #fff; }}
  .search {{
    width: 100%; font-family: inherit; font-weight: 700; font-size: .95rem;
    padding: 10px 14px; border-radius: 14px; border: 2px solid #e2e8f0; background: #fff; color: inherit;
  }}
  .search:focus {{ outline: none; border-color: #38bdf8; }}

  main {{ flex: 1; width: 100%; max-width: 960px; margin: 0 auto; padding: 20px 16px 48px; }}
  .group {{ margin-bottom: 34px; }}
  .group[hidden] {{ display: none; }}
  .gtitle {{
    display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
    margin: 0 0 14px; padding: 10px 16px; border-radius: 16px;
    font-size: 1.15rem; font-weight: 900; color: #fff;
    background: linear-gradient(120deg, var(--from), var(--to));
  }}
  .gemoji {{ font-size: 1.5rem; line-height: 1; }}
  .gdesc {{ font-size: .78rem; font-weight: 700; opacity: .9; }}
  .gn {{
    margin-left: auto; font-size: .78rem; font-variant-numeric: tabular-nums;
    background: rgba(255,255,255,.25); border-radius: 999px; padding: 2px 10px;
  }}
  .grid {{ display: grid; gap: 18px; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); }}
  .card {{
    display: flex;
    flex-direction: column;
    gap: 10px;
    padding: 22px;
    border-radius: 24px;
    border: 4px solid #fff;
    color: #fff;
    text-decoration: none;
    box-shadow: 0 10px 25px rgba(15, 23, 42, .12);
    transition: transform .2s cubic-bezier(.175,.885,.32,1.275), box-shadow .2s;
    position: relative;
    overflow: hidden;
  }}
  .card[hidden] {{ display: none; }}
  .card:hover, .card:focus-visible {{ transform: translateY(-4px) scale(1.02); box-shadow: 0 16px 32px rgba(15, 23, 42, .2); }}
  .card:active {{ transform: scale(.98); }}
  .card .emoji {{ font-size: 2.4rem; line-height: 1; }}
  .card h3 {{ margin: 0; font-size: 1.25rem; font-weight: 900; }}
  .card p {{ margin: 0; font-size: .88rem; font-weight: 700; opacity: .95; line-height: 1.6; }}
  .card .go {{
    margin-top: auto; align-self: flex-start;
    background: #fff; color: #334155; font-weight: 900; font-size: .85rem;
    padding: 8px 18px; border-radius: 999px;
  }}
  .empty {{ font-weight: 900; color: #64748b; text-align: center; padding: 40px 0; }}
  footer {{ text-align: center; padding: 20px; font-size: .75rem; font-weight: 700; color: #94a3b8; }}
  @media (prefers-color-scheme: dark) {{
    body {{ background: #0f172a; color: #e2e8f0; }}
    .bar {{ background: rgba(15,23,42,.95); border-bottom-color: #1e293b; }}
    .chip {{ background: #1e293b; color: #cbd5e1; border-color: #334155; }}
    .chip.on {{ background: #f1f5f9; color: #0f172a; border-color: #f1f5f9; }}
    .search {{ background: #1e293b; border-color: #334155; }}
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
  <p class="count">ぜんぶで {len(apps)}こ の アプリ</p>
</header>

<div class="bar">
  <div class="bar-in">
    <div class="chips" id="chips">
{chr(10).join('      ' + c for c in chips)}
    </div>
    <input class="search" id="search" type="search" placeholder="🔍 アプリを さがす（元素・かけ算・受験 …）"
           autocomplete="off">
  </div>
</div>

<main id="main">
{body}
  <p class="empty" id="nohit" hidden>🔍 見つかりませんでした</p>
</main>
<footer>© 2026 kids apps</footer>

<script>
(function () {{
  var KEY = 'kids-index-group';
  var chips = Array.prototype.slice.call(document.querySelectorAll('[data-chip]'));
  var groups = Array.prototype.slice.call(document.querySelectorAll('.group'));
  var cards = Array.prototype.slice.call(document.querySelectorAll('.card'));
  var search = document.getElementById('search');
  var nohit = document.getElementById('nohit');
  var picked = 'all';

  function apply() {{
    var q = search.value.trim().toLowerCase();
    var shown = 0;
    groups.forEach(function (g) {{
      var inGroup = picked === 'all' || g.dataset.group === picked;
      var visible = 0;
      Array.prototype.forEach.call(g.querySelectorAll('.card'), function (c) {{
        var hit = inGroup && (!q || c.dataset.search.indexOf(q) >= 0);
        c.hidden = !hit;
        if (hit) visible++;
      }});
      g.hidden = visible === 0;
      shown += visible;
    }});
    nohit.hidden = shown > 0;
    chips.forEach(function (b) {{ b.classList.toggle('on', b.dataset.chip === picked); }});
  }}

  chips.forEach(function (b) {{
    b.addEventListener('click', function () {{
      picked = b.dataset.chip;
      try {{ localStorage.setItem(KEY, picked); }} catch (e) {{}}
      apply();
      window.scrollTo({{ top: 0, behavior: 'smooth' }});
    }});
  }});
  search.addEventListener('input', apply);

  var saved = null;
  try {{ saved = localStorage.getItem(KEY); }} catch (e) {{}}
  if (saved && chips.some(function (b) {{ return b.dataset.chip === saved; }})) picked = saved;
  apply();
}})();
</script>
</body>
</html>
"""


def render_card(app: dict, colors: dict[str, tuple[str, str]]) -> str:
    start, end = colors.get(app["group"], OTHER[2])
    emoji = app.get("emoji") or "🌟"
    desc = app.get("description") or ""
    desc_html = f'\n        <p>{html.escape(desc)}</p>' if desc else ""
    needle = " ".join([app["title"], desc, app["group"], app["slug"]]).lower()
    return (
        f'      <a class="card" href="{html.escape(app["href"])}" '
        f'data-search="{html.escape(needle)}" '
        f'style="background: linear-gradient(135deg, {start}, {end});">\n'
        f'        <span class="emoji">{html.escape(emoji)}</span>\n'
        f'        <h3>{html.escape(app["title"])}</h3>{desc_html}\n'
        f'        <span class="go">あそぶ →</span>\n'
        f"      </a>"
    )


def main() -> None:
    apps = collect_apps()

    # トップページは リポジトリ直下に おく（そのまま ひらいて かくにんできる）
    INDEX_FILE.write_text(render_index(apps), encoding="utf-8")

    # 公開用の _site/ を くみたてる
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True)

    if APPS_DIR.is_dir():
        shutil.copytree(APPS_DIR, OUT_DIR / "apps")

    shutil.copy2(INDEX_FILE, OUT_DIR / "index.html")
    (OUT_DIR / ".nojekyll").write_text("", encoding="utf-8")

    print(f"built {len(apps)} app(s) -> index.html, {OUT_DIR.relative_to(ROOT)}/")
    for name, _emoji, _cols, _desc in group_defs(apps):
        mine = [a for a in apps if a["group"] == name]
        print(f"  [{name}] {len(mine)}")
        for app in mine:
            print(f"    - {app['title']}  ({app['href']})")


if __name__ == "__main__":
    main()
