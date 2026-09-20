# kids

こどもむけ 学習ミニアプリを GitHub Pages で公開するリポジトリ。

公開URL: `https://hk2308.github.io/kids/`

## 構成

```
apps/
  elements/
    index.html   ← アプリ本体
    app.json     ← トップページのカード設定（任意）
scripts/build.py ← apps/ を集めて _site/ を組み立てる
.github/workflows/pages.yml ← デフォルトブランチへの push で自動デプロイ
```

トップページ (`index.html`) は `apps/` の中身から**自動生成**される。手で編集する必要はない。

## 新しい HTML を追加する

1. `apps/<なまえ>/index.html` を置く（画像やCSSも同じフォルダに置ける）
   - 1ファイルだけなら `apps/<なまえ>.html` でもよい
2. 必要なら `apps/<なまえ>/app.json` でカードの見た目を指定する

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
3. デフォルトブランチに push する → GitHub Actions が自動で公開する

## ローカルで確認する

```sh
python3 scripts/build.py      # _site/ を生成
python3 -m http.server -d _site 8000
# http://localhost:8000 を開く
```

## 初回セットアップ（リポジトリ設定 / 手動・1回だけ）

1. **Settings → Pages → Build and deployment → Source** を **GitHub Actions** にする
   （この操作は Actions の `GITHUB_TOKEN` からは実行できないため手動が必要）
2. 設定後、**Actions → Deploy to GitHub Pages → Run workflow** で再実行する
   （以降はデフォルトブランチへの push で自動デプロイ）

> プライベートリポジトリの Pages は有料プラン（Pro / Team / Enterprise）が必要。
> 無料プランの場合は、リポジトリを public にすると公開できる。
