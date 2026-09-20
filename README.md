# kids

こどもむけ 学習ミニアプリを GitHub Pages で公開するリポジトリ。

公開URL: `https://hk2308.github.io/kids/`

## アプリ一覧

| アプリ | 内容 |
| --- | --- |
| [元素記号キッズマスター](apps/elements/) | 全118元素の図鑑・クイズ・しんけいすいじゃく |
| [分子ビルダー キッズラボ](apps/molecules/) | 原子をつないで水・二酸化炭素などを組み立てる |
| [ビジュアル すうがくラボ](apps/math-lab/) | 円周率π・ネイピア数e・三角関数をアニメーションで |
| [リズム たいそう](apps/rhythm/) | 音を消しても拍が見えるリズムゲーム |
| [ゆうき化学ラボ](apps/organic/) | ベンゼン環の共鳴・官能基パズル・構造式図鑑 |
| [かけ算ラボ](apps/multiply/) | 九九（面積モデル＋読み方）とインド式2けたかけ算 |
| [日本地図ラボ](apps/japan/) | 47都道府県の地図・県庁所在地・名産品・位置あてクイズ |
| [さんすうランド](apps/arithmetic/) | 小1〜3: くり上がり・時計・分数・わり算・大きい数 |
| [こくごランド](apps/kokugo/) | 小1〜3: 50音表と学年別漢字440字 |
| [りか・しゃかいランド](apps/science/) | 小3: じしゃく・電気・こん虫と植物・地図記号・方位 |

## 構成

```
index.html       ← アプリ一覧（トップページ / 自動生成・編集しない）
apps/
  <アプリ名>/
    index.html   ← アプリ本体（1ファイル完結）
    app.json     ← トップページのカード設定（任意）
scripts/build.py ← index.html を生成し、_site/ を組み立てる
scripts/make_prefecture_paths.py ← 日本地図のSVGパスを作りなおすとき用
.github/workflows/pages.yml ← main への push で自動デプロイ
```

各アプリは外部ファイルに依存しない1枚のHTML（CDNの Tailwind とフォントのみ使用）。
`apps/japan/` の地図データの出典とライセンスは `apps/japan/MAP_DATA_LICENSE.txt`。

トップページ `index.html` は `apps/` の中身から**自動生成**される。
手で編集せず、`python3 scripts/build.py` を実行して作りなおすこと
（ブラウザでそのまま開いても動作確認できる）。

## 新しい HTML を追加する

1. `apps/<なまえ>/index.html` を置く（画像やCSSも同じフォルダに置ける）
   - 1ファイルだけなら `apps/<なまえ>.html` でもよい
2. `python3 scripts/build.py` を実行して `index.html` を作りなおす
3. 必要なら `apps/<なまえ>/app.json` でカードの見た目を指定する

   ```json
   {
     "title": "アプリのなまえ",
     "description": "かんたんな せつめい",
     "emoji": "🚀",
     "order": 2
   }
   ```

   省略した場合は HTML の `<title>` と `<meta name="description">` から自動で拾う。
   `order` は小さいほど前に並ぶ（省略時は 999）。
4. `main` に push する → GitHub Actions が自動で公開する
   （push 前に build.py を忘れても、デプロイ時に作りなおされる）

## ローカルで確認する

```sh
python3 scripts/build.py      # index.html と _site/ を生成
python3 -m http.server -d _site 8000
# http://localhost:8000 を開く
```

## 初回セットアップ（リポジトリ設定 / 手動・1回だけ）

1. **Settings → Pages → Build and deployment → Source** を **GitHub Actions** にする
   （この操作は Actions の `GITHUB_TOKEN` からは実行できないため手動が必要）
2. 設定後、**Actions → Deploy to GitHub Pages → Run workflow** で再実行する
   （以降は `main` への push で自動デプロイ）

> プライベートリポジトリの Pages は有料プラン（Pro / Team / Enterprise）が必要。
> 無料プランの場合は、リポジトリを public にすると公開できる。
