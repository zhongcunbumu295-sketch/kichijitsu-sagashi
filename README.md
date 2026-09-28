# 吉日さがし — 寝ている間も働く「吉日検索」サイト

一粒万倍日・天赦日・大安・寅の日などの「縁起の良い日」を、**目的別（財布・入籍・引っ越し・宝くじなど）に探せる無料Webツール**です。
検索から来た人に広告やアフィリエイトを表示して収益を得ます。暦はすべて自動で計算するので、公開したあとは基本的に手を入れなくても動き続けます。

## なぜこのテーマか

| キーワード | 月間検索数（推定） |
|---|---|
| 一粒万倍日 | 約13.5万回 |
| 大安 | 約13.5万回 |
| 天赦日 | 約7.4万回 |
| 宝くじ 買う日 | 約1.8万回 |
| 寅の日 | 約1.5万回 |

- 検索上位は財布メーカーや結婚式場の「記事」がほとんどで、**目的と期間から吉日を探せるツールは少ない**
- 財布・入籍・引っ越し・車・家づくりなど、**報酬の高いアフィリエイトと相性が良い**
- 暦は計算で出せるので**何年先まで自動で作れる**。毎年「来年の開運日」が検索されるので需要がなくならない

## できあがっているもの

- **トップ**：今日の六曜・吉日と、次の開運日までのカウントダウン（閲覧した日に合わせて自動更新）
- **吉日検索ツール**：目的・期間・土日祝で絞り込み、良い日を順位付けして表示
- **年別・月別カレンダー**：2026〜2028年（毎年自動で増える）
- **暦の解説ページ（14本）**：一粒万倍日・天赦日・最強開運日・寅の日・巳の日・大安・六曜・不成就日・三隣亡など
- **目的別ページ（10本）**：財布・宝くじ・入籍・引っ越し・納車・開業・契約・参拝・旅行・家づくり
- **カレンダー購読**：開運日を Googleカレンダー／iPhone に自動表示（リピーター獲得用）
- **収益化の部品**：AdSense・楽天・Amazon・A8.net などのIDを `config.json` に書くだけで表示（PR表記も自動）
- **SEO対策**：ページごとのタイトル・説明文、構造化データ、サイトマップ、SNS用サムネイル画像
- **運営ページ**：運営者情報・プライバシーポリシー（AdSense・アフィリエイト対応）・お問い合わせ

## 正直な収益の見通し

- **最初の3〜6か月はほぼ0円**です。Googleが新しいサイトを評価するまで時間がかかります。
- AdSenseの収益は、一般的に1,000ページビューあたり数百円程度です。
- 検索上位に入れれば月数千〜数万円も狙えますが、**保証はできません**。
- アクセスの山は、年末（翌年の開運日を調べる人が増える）・春（財布の買い替え）・ジャンボ宝くじの発売期間です。

## 公開までの手順（あなたの操作が必要なところ）

アカウント作成・ドメイン購入・広告の申し込みは、本人が行う必要があります。

### 1. 手元で確認する

```bash
python build.py
```

```bash
python -m http.server 8000 --directory dist
```

ブラウザで http://localhost:8000 を開きます。Python 3.10 以上が必要です（追加のインストールは不要）。

### 2. GitHub Pages で無料公開する

1. [GitHub](https://github.com/) のアカウントを作る
2. 新しいリポジトリを **Public** で作る（例：`kichijitsu`）
3. このフォルダをアップロードする（`git push`）
4. リポジトリの **Settings → Pages → Build and deployment → Source** を **GitHub Actions** にする
5. 数分で `https://ユーザー名.github.io/リポジトリ名/` に公開されます

以後は `main` ブランチに変更を push するたびに自動で公開されます。さらに**毎月1日に自動で作り直す**ので、年が変わると新しい年のページやカレンダーが自動で増えます。

### 3. 独自ドメインを設定する（AdSenseに必要）

AdSense は `github.io` のようなサブドメインでは申し込めません。ドメインを取得します（年1,500〜2,000円程度。Cloudflare Registrar、お名前.com、Xserverドメインなど）。

1. GitHub の **Settings → Pages → Custom domain** にドメインを入力
2. ドメイン会社のDNS設定をする（[GitHubの説明](https://docs.github.com/ja/pages/configuring-a-custom-domain-for-your-github-pages-site)）
3. `config.json` の `base_url` も同じドメインにしておく（手元で確認するとき用）

### 4. Google Search Console に登録する

1. [Search Console](https://search.google.com/search-console) でサイトを追加（URLプレフィックス）
2. 所有権の確認で「HTMLタグ」を選び、`content="..."` の中身を `config.json` の `google_site_verification` に貼って公開し直す
3. 「サイトマップ」に `sitemap.xml` を送信する

### 5. 運営者情報とお問い合わせ先を入れる

AdSense の審査では、運営者情報とお問い合わせ先がないと不利になります。

- `operator`：運営者名（ニックネームでも可）
- `contact_url`：お問い合わせフォームのURL（Googleフォームで無料で作れます）

### 6. Google AdSense に申し込む

公開して検索に少し載り始めたら（目安は数週間）、[AdSense](https://adsense.google.com/) に申し込みます。承認されたら：

- `config.json` の `adsense.client` に `ca-pub-XXXXXXXXXXXXXXXX` を入れる
  - 広告のコードと `ads.txt` が自動で入ります
  - AdSense 管理画面で「自動広告」をオンにすれば、それだけで広告が表示されます
- 広告の位置を自分で決めたい場合は、広告ユニットのIDを `adsense.slots` の `top`・`middle`・`bottom` に入れます

### 7. アフィリエイト（任意・おすすめ）

| 設定項目 | 取得先 | 表示される場所 |
|---|---|---|
| `affiliate.rakuten_id` | [楽天アフィリエイト](https://affiliate.rakuten.co.jp/) のアフィリエイトID | 目的別ページ（財布・印鑑・御朱印帳など） |
| `affiliate.amazon_tag` | [Amazonアソシエイト](https://affiliate.amazon.co.jp/) のトラッキングID（例：`xxxx-22`） | 同上 |
| `affiliate.extra` | [A8.net](https://www.a8.net/)、[もしもアフィリエイト](https://af.moshimo.com/) などの広告リンク | 目的ごとに自由に追加 |

報酬が高いのは、入籍（結婚指輪・結婚式場）、引っ越し（一括見積もり）、納車（車の買取・保険）、家づくり（注文住宅の資料請求）です。`extra` の書き方の例：

```json
"extra": {
  "hikkoshi": [
    { "label": "複数の業者の見積もりを比較できます", "html": "<a href=\"（ASPでもらったURL）\" rel=\"sponsored noopener\">引っ越し料金を一括比較する</a>" }
  ]
}
```

目的のキーは `saifu` `takarakuji` `nyuseki` `hikkoshi` `nousha` `kaigyo` `keiyaku` `sanpai` `ryoko` `kenchiku` です。広告には自動で「PR」と表示され、フッターにも広告を含む旨が表示されます（2023年10月からのステマ規制に対応）。

### 8. アクセス解析（任意）

- `analytics.ga4_id`：Google アナリティクスの測定ID（`G-XXXXXXX`）
- `analytics.cloudflare_token`：Cloudflare Web Analytics のトークン（Cookieを使わない解析）

## config.json の項目一覧

| 項目 | 内容 |
|---|---|
| `site_name` | サイト名 |
| `base_url` | 公開URL（GitHub Actions では自動で正しいURLに置き換わります） |
| `operator` | 運営者名 |
| `contact_url` / `contact_email` | お問い合わせ先（どちらか） |
| `first_year` | ページを作り始める年。一度公開した年のページは消えません |
| `years_ahead` | 何年先までページを作るか（標準は2年先） |
| `google_site_verification` | Search Console の所有権確認用 |
| `analytics` | アクセス解析のID |
| `adsense` | AdSense のIDと広告ユニット |
| `affiliate` | アフィリエイトのIDとリンク |

設定を変えたら、GitHub に push すれば自動で反映されます。

## 暦の正確さ

- 二十四節気と新月・満月の時刻は、天文学の標準的な計算方法（J. Meeus『Astronomical Algorithms』、VSOP87）で求めています
- **国立天文台の暦要項（2025〜2027年）と照合し、二十四節気72件・新月／満月74件がすべて1分以内で一致**することをテストで確認しています
- 祝日・振替休日・雑節（節分・彼岸・土用・八十八夜など）も国立天文台の発表と一致しています
- 2026〜2027年の一粒万倍日・天赦日・不成就日・三隣亡・母倉日・天恩日・大明日・大安などは、複数の暦サイトの日付と一致しています
- 暦注のうち流派で違いがあるもの（大明日・母倉日など）は、採用している決まり方を解説ページで公開しています

テストの実行：

```bash
python -m unittest discover -s tests
```

国立天文台は毎年2月に翌年の暦要項を発表します。新しい年を検証に加えたいときは次を実行します（任意）。

```bash
python tests/fetch_naoj.py 2025 2026 2027 2028
```

## アクセスを早く増やすコツ（任意）

- X（旧Twitter）やInstagramで「明日は一粒万倍日」などを投稿する。開運日の話題は拡散されやすいです
- 年末に「来年の最強開運日」、春に「財布の買い替え」、ジャンボ宝くじの発売前に「宝くじを買う日」を発信する
- `/subscribe/`（カレンダー登録）を紹介する。登録した人は毎回サイトの存在を思い出してくれます

## ファイル構成

```
build.py              サイトを生成（dist/ に出力）
config.json           サイト名・広告・アフィリエイトなどの設定
koyomi/
  astro.py            天文計算（二十四節気・新月・満月）
  calendar.py         旧暦・六曜・干支・暦注・祝日・雑節
  marks.py            暦注の説明と、目的別の吉日スコア（ここを変えると評価が変わる）
sitegen/
  pages.py            各ページの組み立て
  content.py          解説ページの本文
  parts.py / html.py  カレンダー表示やレイアウトなどの部品
  ics.py              カレンダー購読ファイル
  ogimage.py          SNS用サムネイル画像
static/               CSS・JavaScript・アイコン
tests/                暦計算のテストと国立天文台のデータ
.github/workflows/    自動公開の設定（push時と毎月1日）
```
