"""サイトを生成する。

    python build.py                       # config.json の base_url で dist/ に出力
    python build.py --base-url https://…  # 公開先URLを上書き（GitHub Actions から使う）
    python build.py --today 2027-01-15    # 「今日」を指定して確認する
"""
from __future__ import annotations

import argparse
import json
import shutil
from datetime import date, datetime, timedelta
from pathlib import Path

from koyomi.astro import JST, moon_phases
from koyomi.calendar import BRANCHES, ROKUYO, STEMS, Koyomi
from koyomi.marks import KAIUN_KEYS, MARK_ORDER, MARKS, PURPOSES, ROKUYO_INFO, ROKUYO_KEYS
from sitegen import ics
from sitegen.content import TOPIC_ORDER
from sitegen.html import Site
from sitegen.ogimage import write_og_image
from sitegen.pages import Pages

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"


def write(path: str, html: str) -> None:
    target = DIST / (path.lstrip("/") + ("index.html" if path.endswith("/") else ""))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html, encoding="utf-8")


def data_json(days) -> str:
    meta = {
        "start": days[0].date.isoformat(),
        "end": days[-1].date.isoformat(),
        "marks": {k: {"name": m.name, "short": m.short, "kind": m.kind, "summary": m.summary, "slug": m.slug}
                  for k, m in MARKS.items()},
        "markOrder": MARK_ORDER,
        "kaiun": KAIUN_KEYS,
        "rokuyo": ROKUYO,
        "rokuyoInfo": {n: {"key": ROKUYO_KEYS[n], "reading": r, "desc": d} for n, (r, d) in ROKUYO_INFO.items()},
        "purposes": [{"key": p.key, "name": p.name, "short": p.short, "weights": p.weights,
                      "reasons": p.reasons, "rest": p.rest_day_default} for p in PURPOSES],
        "stems": STEMS,
        "branches": BRANCHES,
        # [干支, 六曜, 旧暦月, 旧暦日, 閏月, 暦注, 二十四節気, 祝日, 雑節, 月相, 月齢, 土用]
        "days": [[d.kanshi, d.rokuyo, d.lunar_month, d.lunar_day, int(d.lunar_leap), ",".join(d.marks),
                  d.sekki or "", d.holiday or "", "|".join(d.zassetsu), d.moon or "", d.moon_age, int(d.doyo)]
                 for d in days],
    }
    return json.dumps(meta, ensure_ascii=False, separators=(",", ":"))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url")
    ap.add_argument("--today", type=date.fromisoformat)
    args = ap.parse_args()

    cfg = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    if args.base_url:
        cfg["base_url"] = args.base_url
    today = args.today or datetime.now(JST).date()
    # 一度公開したページは消さない（検索エンジンの評価を保つ）ため、first_year から毎年増やしていく
    first_year = min(int(cfg.get("first_year", today.year)), today.year)
    years = list(range(first_year, today.year + int(cfg.get("years_ahead", 2)) + 1))
    # 検索ツール用のデータは、ページを作る年のさらに2年先まで
    koyomi = Koyomi(date(first_year, 1, 1), date(years[-1] + 2, 12, 31))
    days = koyomi.days()

    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    site = Site(cfg, today)
    pages = Pages(site, days, years)

    outputs = [pages.home(), pages.search(), pages.calendar_index()]
    for y in years:
        outputs.append(pages.year(y))
        outputs += [pages.month(y, m) for m in range(1, 13)]
    outputs.append(pages.koyomi_index())
    outputs += [pages.topic(slug) for slug in TOPIC_ORDER]
    outputs.append(pages.purpose_index())
    outputs += [pages.purpose(p) for p in PURPOSES]
    outputs.append(pages.subscribe([(f, t, d) for f, t, d, _, _ in ics.FEEDS]))
    outputs += [pages.about(), pages.contact(), pages.privacy(), pages.not_found()]
    for path, html in outputs:
        write(path, html)

    (DIST / "data").mkdir()
    (DIST / "data" / "koyomi.json").write_text(data_json(days), encoding="utf-8")

    (DIST / "ics").mkdir()
    feed_days = ics.feed_range(days, today)
    stamp = datetime.now(JST)
    for feed in ics.FEEDS:
        (DIST / "ics" / feed[0]).write_bytes(
            ics.build_feed(site.name, site.base_url, feed, feed_days, stamp).encode("utf-8"))

    shutil.copytree(ROOT / "static", DIST / "static")
    write_og_image(DIST / "static" / "og.png")

    urls = "".join(f"<url><loc>{site.abs_url(p)}</loc><lastmod>{today.isoformat()}</lastmod></url>"
                   for p in site.pages)
    (DIST / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>',
        encoding="utf-8")
    (DIST / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {site.abs_url('/sitemap.xml')}\n",
                                     encoding="utf-8")
    if site.adsense_client:
        pub = site.adsense_client.replace("ca-", "")
        (DIST / "ads.txt").write_text(f"google.com, {pub}, DIRECT, f08c47fec0942fa0\n", encoding="utf-8")
    (DIST / ".nojekyll").write_text("", encoding="utf-8")

    # 日付の変わり目の前後2分以内の節気・新月は、計算誤差で日付がずれる可能性があるので知らせる
    events = [(f"太陽黄経{lon}度", dt) for lon, dt in koyomi.solar_events]
    events += [("新月", dt) for dt in moon_phases(days[0].date, days[-1].date)]
    for label, dt in events:
        if (dt.hour == 23 and dt.minute >= 58) or (dt.hour == 0 and dt.minute <= 2):
            print(f"注意: {label}が日付の変わり目付近です（{dt:%Y-%m-%d %H:%M}）。国立天文台の暦要項で確認してください。")
    print(f"生成しました: {len(outputs)}ページ / 暦データ {days[0].date}〜{days[-1].date} / 出力先 {DIST}")


if __name__ == "__main__":
    main()
