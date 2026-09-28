"""HTML の共通部品: レイアウト、広告枠、アフィリエイト枠、日付の書式。"""
from __future__ import annotations

import json
from datetime import date
from html import escape
from urllib.parse import quote, urlparse

from koyomi.calendar import DayInfo
from koyomi.marks import MARKS, Purpose

WEEK = "月火水木金土日"


def esc(s) -> str:
    return escape(str(s), quote=True)


def md(d: date) -> str:
    return f"{d.month}月{d.day}日（{WEEK[d.weekday()]}）"


def ymd(d: date) -> str:
    return f"{d.year}年{d.month}月{d.day}日（{WEEK[d.weekday()]}）"


def reiwa(year: int) -> str:
    return f"令和{year - 2018}年"


class Site:
    def __init__(self, cfg: dict, today: date):
        self.cfg = cfg
        self.today = today
        self.name = cfg["site_name"]
        self.base_url = cfg["base_url"].rstrip("/")
        self.base_path = urlparse(self.base_url).path.rstrip("/")
        self.pages: list[str] = []          # sitemap 用

    def url(self, path: str) -> str:
        return self.base_path + path

    def abs_url(self, path: str) -> str:
        return self.base_url + path

    # ------------------------------------------------------------ 収益化の部品
    @property
    def adsense_client(self) -> str:
        return self.cfg.get("adsense", {}).get("client", "").strip()

    def ad(self, slot_name: str) -> str:
        """AdSense の手動広告枠。未設定なら何も出さない（自動広告だけでも可）。"""
        slot = self.cfg.get("adsense", {}).get("slots", {}).get(slot_name, "").strip()
        if not (self.adsense_client and slot):
            return ""
        return (f'<div class="ad"><span class="ad-label">スポンサーリンク</span>'
                f'<ins class="adsbygoogle" style="display:block" data-ad-client="{esc(self.adsense_client)}" '
                f'data-ad-slot="{esc(slot)}" data-ad-format="auto" data-full-width-responsive="true"></ins>'
                f'<script>(adsbygoogle=window.adsbygoogle||[]).push({{}});</script></div>')

    @property
    def has_affiliate(self) -> bool:
        a = self.cfg.get("affiliate", {})
        return bool(a.get("amazon_tag") or a.get("rakuten_id") or any(a.get("extra", {}).values()))

    def affiliate_box(self, purpose: Purpose) -> str:
        """目的に合う商品リンク（PR表記つき）。ID未設定なら何も出さない。"""
        a = self.cfg.get("affiliate", {})
        links = []
        for item in a.get("extra", {}).get(purpose.key, []):
            links.append(f'<li>{item["html"]}'
                         + (f'<span class="muted"> {esc(item.get("label", ""))}</span>' if item.get("label") else "")
                         + "</li>")
        for kw in purpose.products:
            if a.get("rakuten_id"):
                target = f"https://search.rakuten.co.jp/search/mall/{quote(kw)}/"
                href = (f"https://hb.afl.rakuten.co.jp/hgc/{quote(a['rakuten_id'], safe='.')}/"
                        f"?pc={quote(target, safe='')}&m={quote(target, safe='')}")
                links.append(f'<li><a href="{esc(href)}" rel="sponsored noopener" target="_blank">'
                             f'楽天市場で「{esc(kw)}」を見る</a></li>')
            if a.get("amazon_tag"):
                href = f"https://www.amazon.co.jp/s?k={quote(kw)}&tag={quote(a['amazon_tag'])}"
                links.append(f'<li><a href="{esc(href)}" rel="sponsored noopener" target="_blank">'
                             f'Amazonで「{esc(kw)}」を見る</a></li>')
        if not links:
            return ""
        return (f'<aside class="pr-box"><p class="pr-head"><span class="pr">PR</span>'
                f'{esc(purpose.short)}の準備に</p><ul>{"".join(links)}</ul></aside>')

    # ------------------------------------------------------------ レイアウト
    def page(self, *, path: str, title: str, description: str, body: str,
             crumbs: list[tuple[str, str]] | None = None, faq: list[tuple[str, str]] | None = None,
             is_home: bool = False, noindex: bool = False) -> str:
        if not noindex:
            self.pages.append(path)
        full_title = title if is_home else f"{title}｜{self.name}"
        canonical = self.abs_url(path)
        jsonld = []
        if is_home:
            jsonld.append({"@context": "https://schema.org", "@type": "WebSite",
                           "name": self.name, "url": canonical,
                           "description": description, "inLanguage": "ja"})
        if crumbs:
            items = [("ホーム", "/")] + crumbs
            jsonld.append({"@context": "https://schema.org", "@type": "BreadcrumbList",
                           "itemListElement": [
                               {"@type": "ListItem", "position": i + 1, "name": n,
                                "item": self.abs_url(p)} for i, (n, p) in enumerate(items)]})
        if faq:
            jsonld.append({"@context": "https://schema.org", "@type": "FAQPage",
                           "mainEntity": [{"@type": "Question", "name": q,
                                           "acceptedAnswer": {"@type": "Answer", "text": a}}
                                          for q, a in faq]})
        head_extra = []
        cfg = self.cfg
        if cfg.get("google_site_verification"):
            head_extra.append(f'<meta name="google-site-verification" content="{esc(cfg["google_site_verification"])}">')
        if noindex:
            head_extra.append('<meta name="robots" content="noindex">')
        if self.adsense_client:
            head_extra.append(f'<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js'
                              f'?client={esc(self.adsense_client)}" crossorigin="anonymous"></script>')
        ga = cfg.get("analytics", {}).get("ga4_id", "").strip()
        if ga:
            head_extra.append(f'<script async src="https://www.googletagmanager.com/gtag/js?id={esc(ga)}"></script>'
                              f"<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}"
                              f"gtag('js',new Date());gtag('config','{esc(ga)}');</script>")
        cf = cfg.get("analytics", {}).get("cloudflare_token", "").strip()
        cf_tag = (f"<script defer src='https://static.cloudflareinsights.com/beacon.min.js' "
                  f"data-cf-beacon='{{\"token\": \"{esc(cf)}\"}}'></script>") if cf else ""
        crumb_html = ""
        if crumbs:
            parts = [f'<a href="{self.url("/")}">ホーム</a>']
            for i, (n, p) in enumerate(crumbs):
                parts.append(esc(n) if i == len(crumbs) - 1 else f'<a href="{self.url(p)}">{esc(n)}</a>')
            crumb_html = f'<nav class="crumbs" aria-label="パンくずリスト">{" › ".join(parts)}</nav>'
        ld = "".join(f'<script type="application/ld+json">{json.dumps(j, ensure_ascii=False)}</script>'
                     for j in jsonld)
        y = self.today.year
        pr_note = ('<p class="muted small">当サイトはアフィリエイトプログラムを利用しており、'
                   '紹介している商品・サービスのリンクには広告が含まれます。</p>') if self.has_affiliate else ""
        return f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(full_title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{esc(canonical)}">
<meta property="og:type" content="{'website' if is_home else 'article'}">
<meta property="og:title" content="{esc(full_title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{esc(canonical)}">
<meta property="og:site_name" content="{esc(self.name)}">
<meta property="og:locale" content="ja_JP">
<meta property="og:image" content="{esc(self.abs_url('/static/og.png'))}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#b8322a">
<link rel="icon" href="{self.url('/static/favicon.svg')}" type="image/svg+xml">
<link rel="stylesheet" href="{self.url('/static/style.css')}?v={self.today:%Y%m%d}">
{''.join(head_extra)}
{ld}
</head>
<body data-base="{esc(self.base_path)}" data-built="{self.today.isoformat()}">
<a class="skip" href="#main">本文へスキップ</a>
<header class="site-header">
  <div class="wrap header-inner">
    <a class="logo" href="{self.url('/')}"><svg viewBox="0 0 32 32" aria-hidden="true"><use href="#torii"/></svg><span>{esc(self.name)}</span></a>
    <nav class="nav" aria-label="メインメニュー">
      <a href="{self.url('/search/')}">吉日検索</a>
      <a href="{self.url(f'/calendar/{y}/')}">カレンダー</a>
      <a href="{self.url('/purpose/')}">目的別</a>
      <a href="{self.url('/koyomi/')}">暦の解説</a>
    </nav>
  </div>
</header>
<svg width="0" height="0" style="position:absolute" aria-hidden="true"><symbol id="torii" viewBox="0 0 32 32"><g fill="currentColor"><path d="M2 7.2Q16 10.6 30 7.2V10.2Q16 13.2 2 10.2Z"/><rect x="5" y="14.2" width="22" height="2.4" rx=".4"/><rect x="14.8" y="11.2" width="2.4" height="3.2"/><rect x="8.2" y="10.8" width="2.8" height="17.2"/><rect x="21" y="10.8" width="2.8" height="17.2"/></g></symbol></svg>
<main id="main" class="wrap">
{crumb_html}
{body}
</main>
<footer class="site-footer">
  <div class="wrap">
    <nav class="footer-nav" aria-label="フッターメニュー">
      <a href="{self.url('/subscribe/')}">カレンダーアプリに登録</a>
      <a href="{self.url('/about/')}">運営者情報</a>
      <a href="{self.url('/privacy/')}">プライバシーポリシー</a>
      <a href="{self.url('/contact/')}">お問い合わせ</a>
    </nav>
    <p class="muted small">暦注（吉日・凶日）は古くからの言い伝えにもとづくもので、流派によって日付が異なる場合があります。二十四節気・新月・満月の時刻は国立天文台の暦要項と照合して計算しています。</p>
    {pr_note}
    <p class="muted small">© {y} {esc(self.name)}</p>
  </div>
</footer>
<script src="{self.url('/static/app.js')}?v={self.today:%Y%m%d}" defer></script>
{cf_tag}
</body>
</html>
"""


# ---------------------------------------------------------------- 暦の表示部品
def badges(day: DayInfo, with_rokuyo: bool = True) -> str:
    out = []
    if with_rokuyo:
        cls = {"大安": "rk-good", "仏滅": "rk-bad", "赤口": "rk-bad"}.get(day.rokuyo_name, "rk")
        out.append(f'<span class="b {cls}">{day.rokuyo_name}</span>')
    for key in day.marks:
        m = MARKS[key]
        out.append(f'<span class="b m-{key}">{m.name}</span>')
    return "".join(out)
