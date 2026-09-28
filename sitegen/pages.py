"""各ページの本文を組み立てる。戻り値はどれも (パス, HTML)。"""
from __future__ import annotations

from datetime import date

from koyomi.calendar import DayInfo
from koyomi.marks import (MARKS, PURPOSES, ROKUYO_INFO, Purpose, is_saikyo, kaiun_overlap,
                          rank_label, score)

from .content import TOPIC_ORDER, TOPICS
from .html import Site, badges, esc, md, reiwa, ymd
from .parts import (best_days, best_table, by_month_table, countdown_text, date_table, day_link,
                    first_after, key_name_and_summary, month_grid, next_box, overlap_note,
                    special_days, weights_table)

ICONS = {"saifu": "👛", "takarakuji": "🎫", "nyuseki": "💍", "hikkoshi": "📦", "nousha": "🚗",
         "kaigyo": "🏪", "keiyaku": "🖋️", "sanpai": "⛩️", "ryoko": "✈️", "kenchiku": "🏠"}

# 「次の○○」に出す暦注（キー, 表示名, 解説ページ）
UPCOMING = [("saikyo", "最強開運日", "saikyo-kaiunbi"), ("tensha", "天赦日", "tenshanichi"),
            ("ichiryu", "一粒万倍日", "ichiryumanbaibi"), ("tora", "寅の日", "toranohi"),
            ("mi", "巳の日", "minohi"), ("tsuchinotomi", "己巳の日", "minohi"),
            ("kinoene", "甲子の日", "kinoenenohi"), ("taian", "大安", "taian")]


def matches(d: DayInfo, key: str) -> bool:
    if key == "saikyo":
        return is_saikyo(d)
    if key == "taian":
        return d.rokuyo_name == "大安"
    return key in d.marks


def faq_html(faq: list[tuple[str, str]]) -> str:
    if not faq:
        return ""
    items = "".join(f"<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>" for q, a in faq)
    return f'<section><h2>よくある質問</h2><div class="faq">{items}</div></section>'


def purpose_cards(site: Site) -> str:
    cards = "".join(
        f'<a class="pcard" href="{site.url(f"/purpose/{p.key}/")}"><span class="picon" aria-hidden="true">'
        f'{ICONS[p.key]}</span><span>{esc(p.name)}</span></a>' for p in PURPOSES)
    return f'<div class="pgrid">{cards}</div>'


def topic_cards(site: Site) -> str:
    cards = []
    for slug in TOPIC_ORDER:
        t = TOPICS[slug]
        cards.append(f'<a class="tcard" href="{site.url(f"/koyomi/{slug}/")}"><strong>{esc(t["name"])}</strong>'
                     f'<span class="small muted">{esc(t["reading"])}</span></a>')
    return f'<div class="tgrid">{"".join(cards)}</div>'


class Pages:
    def __init__(self, site: Site, days: list[DayInfo], years: list[int]):
        self.site = site
        self.days = days
        self.by_date = {d.date: d for d in days}
        self.years = years                      # ページを作る年（過去の年も含む）
        self.y1, self.y2 = site.today.year, site.today.year + 1   # 解説・目的別で扱う「今年・来年」

    # ------------------------------------------------------------ 共通
    def year_days(self, y: int) -> list[DayInfo]:
        return [d for d in self.days if d.date.year == y]

    def month_days(self, y: int, m: int) -> list[DayInfo]:
        return [d for d in self.days if d.date.year == y and d.date.month == m]

    def current_sekki(self, target: date) -> tuple[str, date] | None:
        found = None
        for d in self.days:
            if d.date > target:
                break
            if d.sekki:
                found = (d.sekki, d.date)
        return found

    def today_card(self, d: DayInfo) -> str:
        notes = "".join(f"<li><strong>{MARKS[k].name}</strong>：{esc(MARKS[k].summary)}</li>" for k in d.marks)
        extra = []
        sekki = self.current_sekki(d.date)
        if sekki:
            extra.append(f"二十四節気：{sekki[0]}（{sekki[1].month}月{sekki[1].day}日〜）")
        extra.append(f"月齢：{d.moon_age}")
        if d.holiday:
            extra.insert(0, d.holiday)
        rk_desc = ROKUYO_INFO[d.rokuyo_name][1]
        marks_html = badges(d, with_rokuyo=False) or '<span class="muted">特別な暦注はありません</span>'
        return (f'<p class="today-date">{ymd(d.date)}<span class="muted small">旧暦{d.lunar_name}・{d.kanshi_name}の日</span></p>'
                f'<p class="today-rk"><span class="rk-big">{d.rokuyo_name}</span><span class="small">{esc(rk_desc)}</span></p>'
                f'<div class="today-marks">{marks_html}</div>'
                + (f'<ul class="today-notes">{notes}</ul>' if notes else "")
                + f'<p class="small muted">{"｜".join(extra)}</p>')

    def upcoming_list(self, today: date) -> str:
        items = []
        for key, label, slug in UPCOMING:
            d = first_after(self.days, today, lambda x, k=key: matches(x, k))
            items.append(f'<li data-key="{key}"><a href="{self.site.url(f"/koyomi/{slug}/")}">{label}</a>'
                         f'<span class="up-date">{countdown_text(d, today)}</span></li>')
        return f'<ul class="upcoming">{"".join(items)}</ul>'

    # ------------------------------------------------------------ トップ
    def home(self) -> tuple[str, str]:
        s = self.site
        today = self.by_date[s.today]
        y = s.today.year
        month_links = " ".join(f'<a href="{s.url(f"/calendar/{yy}/")}">{yy}年</a>' for yy in self.years)
        body = f"""
<section class="hero">
  <h1>今日は何の日？<br>吉日・開運日がすぐわかる</h1>
  <p class="lead">一粒万倍日・天赦日・大安・寅の日などの吉日を、国立天文台のデータと照合した暦計算で自動表示。財布・入籍・引っ越し・宝くじなど、<strong>目的に合わせていちばん良い日</strong>を探せます。</p>
</section>
<section class="card today" id="today" aria-live="polite">{self.today_card(today)}</section>
<section>
  <h2>目的から吉日を探す</h2>
  {purpose_cards(s)}
  <p class="center"><a class="btn" href="{s.url('/search/')}">期間や土日祝で絞り込んで探す</a></p>
</section>
{s.ad('top')}
<section>
  <h2>次の開運日</h2>
  <div id="upcoming">{self.upcoming_list(s.today)}</div>
</section>
<section>
  <h2>開運日カレンダー</h2>
  <p>{month_links}</p>
  <p><a href="{s.url(f'/calendar/{y}/{s.today.month:02d}/')}">{y}年{s.today.month}月のカレンダーを見る</a> ／ <a href="{s.url('/subscribe/')}">スマホのカレンダーアプリに開運日を自動表示する</a></p>
</section>
<section>
  <h2>暦の解説</h2>
  {topic_cards(s)}
</section>
{s.ad('bottom')}
<section class="prose">
  <h2>{esc(s.name)}について</h2>
  <p>{esc(s.name)}は、日本の暦に書かれてきた「暦注（れきちゅう）」をもとに、縁起の良い日を調べられる無料のツールです。一粒万倍日や天赦日のような選日、大安や仏滅などの六曜、二十四節気や新月・満月まで、すべて天文計算で求めています。</p>
  <p>二十四節気と新月・満月の時刻は、国立天文台が発表する暦要項と照合して1分以内の精度であることを確認しています。暦注は流派によって日付が異なるものもあるため、当サイトで採用している決まり方は各解説ページで公開しています。</p>
</section>
"""
        return "/", s.page(path="/", title=f"{s.name}｜今日は何の日？吉日・開運日カレンダーと目的別の吉日検索",
                           description=f"今日の六曜と吉日がすぐわかる無料ツール。一粒万倍日・天赦日・寅の日・巳の日・大安の{y}年・{y + 1}年カレンダー、財布・入籍・引っ越し・宝くじなど目的別の吉日検索。",
                           body=body, is_home=True)

    # ------------------------------------------------------------ 吉日検索ツール
    def search(self) -> tuple[str, str]:
        s = self.site
        radios = "".join(
            f'<label class="pradio"><input type="radio" name="p" value="{p.key}"{" checked" if i == 0 else ""}>'
            f'<span>{ICONS[p.key]} {esc(p.name)}</span></label>' for i, p in enumerate(PURPOSES))
        guide_rows = []
        for p in PURPOSES:
            good = [key_name_and_summary(k)[0] for k, w in sorted(p.weights.items(), key=lambda kv: -kv[1]) if w >= 3]
            bad = [key_name_and_summary(k)[0] for k, w in sorted(p.weights.items(), key=lambda kv: kv[1]) if w <= -2]
            guide_rows.append(f'<tr><th scope="row"><a href="{s.url(f"/purpose/{p.key}/")}">{esc(p.name)}</a></th>'
                              f'<td>{"・".join(good)}</td><td>{"・".join(bad)}</td></tr>')
        body = f"""
<h1>吉日検索｜目的別に縁起の良い日を探す</h1>
<p class="lead">目的と期間を選ぶと、暦注の組み合わせから縁起の良い日を順番に表示します。入籍や引っ越しなど、土日祝に予定したい場合は「土日・祝日だけ」にチェックを入れてください。</p>
<form id="search-form" class="card tool" autocomplete="off">
  <fieldset><legend>目的</legend><div class="pradios">{radios}</div></fieldset>
  <div class="tool-row">
    <label>期間
      <select name="range">
        <option value="1">1か月</option><option value="3" selected>3か月</option>
        <option value="6">6か月</option><option value="12">1年</option><option value="custom">日付を指定</option>
      </select>
    </label>
    <label class="custom" hidden>開始日 <input type="date" name="from"></label>
    <label class="custom" hidden>終了日 <input type="date" name="to"></label>
  </div>
  <div class="tool-row">
    <label class="check"><input type="checkbox" name="rest"> 土日・祝日だけ</label>
    <label class="check"><input type="checkbox" name="avoid" checked> 避けたい日（不成就日・仏滅など）を除く</label>
  </div>
  <button class="btn" type="submit">吉日を探す</button>
</form>
<section id="results" aria-live="polite"><noscript><p>検索ツールを使うには JavaScript を有効にしてください。目的別のおすすめ日は<a href="{s.url('/purpose/')}">目的別ページ</a>でも確認できます。</p></noscript></section>
{s.ad('middle')}
<section class="card">
  <h2>日付から吉凶を調べる</h2>
  <p><label>日付 <input type="date" id="lookup-date"></label></p>
  <div id="lookup-result" aria-live="polite"></div>
</section>
<section class="prose">
  <h2>目的別・吉日の選び方</h2>
  <p>検索結果は、その日に重なっている暦注ごとの「重み」を合計して並べています。重みは一般的な言い伝えをもとにした目安です。</p>
  <div class="table-wrap"><table class="rule"><thead><tr><th scope="col">目的</th><th scope="col">重視する吉日</th><th scope="col">避けたい日</th></tr></thead><tbody>{"".join(guide_rows)}</tbody></table></div>
</section>
"""
        return "/search/", s.page(path="/search/", title="吉日検索｜財布・入籍・引っ越し・宝くじなど目的別に縁起の良い日を探す",
                                  description="目的と期間を選ぶだけで縁起の良い日がわかる無料の吉日検索ツール。一粒万倍日・天赦日・大安・寅の日などの重なりから、財布・入籍・引っ越し・納車・宝くじに良い日を表示します。",
                                  body=body, crumbs=[("吉日検索", "/search/")])

    # ------------------------------------------------------------ カレンダー
    def calendar_index(self) -> tuple[str, str]:
        s = self.site
        blocks = []
        for y in self.years:
            months = "".join(f'<a href="{s.url(f"/calendar/{y}/{m:02d}/")}">{m}月</a>' for m in range(1, 13))
            blocks.append(f'<h2><a href="{s.url(f"/calendar/{y}/")}">{y}年（{reiwa(y)}）</a></h2><p class="mlinks">{months}</p>')
        body = f'<h1>開運日カレンダー</h1><p class="lead">年ごと・月ごとの吉日カレンダーです。</p>{"".join(blocks)}'
        return "/calendar/", s.page(path="/calendar/", title="開運日カレンダー一覧",
                                    description="一粒万倍日・天赦日・大安・寅の日・巳の日などの吉日を年別・月別のカレンダーで確認できます。",
                                    body=body, crumbs=[("カレンダー", "/calendar/")])

    def year(self, y: int) -> tuple[str, str]:
        s = self.site
        days = self.year_days(y)
        count = {k: sum(1 for d in days if k in d.marks) for k in ("ichiryu", "tensha", "tora", "mi", "tsuchinotomi", "kinoene", "fujoju")}
        taian = sum(1 for d in days if d.rokuyo_name == "大安")
        tensha_days = [d for d in days if "tensha" in d.marks]
        saikyo = [d for d in days if is_saikyo(d)]
        summary = (f"{y}年の一粒万倍日は{count['ichiryu']}日、天赦日は{count['tensha']}日"
                   f"（{'・'.join(f'{d.date.month}月{d.date.day}日' for d in tensha_days)}）、"
                   f"大安は{taian}日、寅の日は{count['tora']}日、巳の日は{count['mi']}日（うち己巳の日{count['tsuchinotomi']}日）です。")
        if saikyo:
            summary += f"天赦日と一粒万倍日が重なる最強開運日は{'、'.join(md(d.date) for d in saikyo)}です。"
        else:
            summary += "天赦日と一粒万倍日が重なる日はありません。"
        rows = []
        for m in range(1, 13):
            md_ = [d for d in days if d.date.month == m]

            def cell(pred):
                return "・".join(str(d.date.day) for d in md_ if pred(d)) or "－"
            rows.append(f'<tr><th scope="row"><a href="{s.url(f"/calendar/{y}/{m:02d}/")}">{m}月</a></th>'
                        f'<td>{cell(lambda d: "ichiryu" in d.marks)}</td>'
                        f'<td>{cell(lambda d: "tora" in d.marks)}</td>'
                        f'<td>{cell(lambda d: "mi" in d.marks)}</td>'
                        f'<td>{cell(lambda d: d.rokuyo_name == "大安")}</td>'
                        f'<td>{cell(lambda d: "fujoju" in d.marks)}</td></tr>')
        months = "".join(f'<a href="{s.url(f"/calendar/{y}/{m:02d}/")}">{m}月</a>' for m in range(1, 13))
        other = " ".join(f'<a href="{s.url(f"/calendar/{yy}/")}">{yy}年</a>' for yy in self.years if yy != y)
        body = f"""
<h1>{y}年（{reiwa(y)}）の開運日カレンダー</h1>
<p class="lead">{esc(summary)}</p>
<p class="mlinks">{months}</p>
<section><h2>{y}年の最強開運日・吉日が重なる日</h2>
<p>天赦日と一粒万倍日が重なる日と、主要な吉日（天赦日・一粒万倍日・寅の日・巳の日・甲子の日・大安）が3つ以上重なる日です。</p>
{date_table(s, special_days(days), overlap_note)}</section>
{s.ad('top')}
<section><h2>{y}年の天赦日</h2>{date_table(s, tensha_days)}</section>
<section><h2>{y}年 月別の開運日一覧</h2>
<div class="table-wrap"><table class="year"><thead><tr><th scope="col">月</th><th scope="col">一粒万倍日</th><th scope="col">寅の日</th><th scope="col">巳の日</th><th scope="col">大安</th><th scope="col">不成就日</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>
<p class="small muted">数字は日付です。各月の詳しいカレンダーは月の名前から開けます。</p></section>
{s.ad('bottom')}
<section><h2>ほかの年</h2><p>{other}</p></section>
"""
        return f"/calendar/{y}/", s.page(
            path=f"/calendar/{y}/", title=f"{y}年（{reiwa(y)}）開運日カレンダー｜一粒万倍日・天赦日・寅の日・大安の一覧",
            description=f"{y}年の開運日カレンダー。一粒万倍日{count['ichiryu']}日・天赦日{count['tensha']}日・大安{taian}日・寅の日・巳の日の日付を月別に一覧表示。最強開運日（天赦日と一粒万倍日が重なる日）も掲載。",
            body=body, crumbs=[("カレンダー", "/calendar/"), (f"{y}年", f"/calendar/{y}/")])

    def month(self, y: int, m: int) -> tuple[str, str]:
        s = self.site
        days = self.month_days(y, m)
        by_key = {k: [d for d in days if k in d.marks] for k in MARKS}
        taian = [d for d in days if d.rokuyo_name == "大安"]
        # 導入文（その月だけの具体的な内容）
        parts = [f"{y}年{m}月の一粒万倍日は{len(by_key['ichiryu'])}日"]
        if by_key["tensha"]:
            parts.append(f"天赦日は{'・'.join(md(d.date) for d in by_key['tensha'])}")
        parts.append(f"大安は{len(taian)}日、寅の日は{len(by_key['tora'])}日、巳の日は{len(by_key['mi'])}日あります")
        lead = "、".join(parts) + "。"
        specials = special_days(days)
        if specials:
            best = max(specials, key=lambda d: (is_saikyo(d), len(kaiun_overlap(d))))
            label = "最強開運日" if is_saikyo(best) else "吉日が重なる日"
            lead += f"特に{md(best.date)}は{'・'.join(kaiun_overlap(best))}が重なる{label}です。"
        sections = []
        for key, title in [("tensha", "天赦日"), ("ichiryu", "一粒万倍日"), ("tora", "寅の日"),
                           ("mi", "巳の日"), ("tsuchinotomi", "己巳の日"), ("kinoene", "甲子の日"),
                           ("tenon", "天恩日"), ("daimyo", "大明日"), ("bosou", "母倉日")]:
            if by_key[key]:
                slug = MARKS[key].slug
                sections.append(f'<h3><a href="{s.url(f"/koyomi/{slug}/")}">{title}</a>（{len(by_key[key])}日）</h3>'
                                f'<p class="dayline">{"、".join(md(d.date) for d in by_key[key])}</p>')
        sections.append(f'<h3><a href="{s.url("/koyomi/taian/")}">大安</a>（{len(taian)}日）</h3>'
                        f'<p class="dayline">{"、".join(md(d.date) for d in taian)}</p>')
        bad = []
        for key in ("fujoju", "sanrinbo"):
            if by_key[key]:
                bad.append(f'<h3><a href="{s.url(f"/koyomi/{MARKS[key].slug}/")}">{MARKS[key].name}</a>（{len(by_key[key])}日）</h3>'
                           f'<p class="dayline">{"、".join(md(d.date) for d in by_key[key])}</p>')
        butsu = [d for d in days if d.rokuyo_name == "仏滅"]
        bad.append(f'<h3>仏滅（{len(butsu)}日）</h3><p class="dayline">{"、".join(md(d.date) for d in butsu)}</p>')
        events = []
        for d in days:
            for label in ([d.holiday] if d.holiday else []) + ([f"{d.sekki}（{d.sekki_time}）"] if d.sekki else []) + d.zassetsu + ([d.moon] if d.moon else []):
                events.append(f"<li>{md(d.date)}：{esc(label)}</li>")
        rows = "".join(
            f'<tr data-date="{d.date.isoformat()}"><td class="nowrap">{md(d.date)}</td><td>{d.rokuyo_name}</td>'
            f'<td>{d.kanshi_name}</td><td class="nowrap">{d.lunar_name}</td><td>{badges(d, with_rokuyo=False)}</td></tr>'
            for d in days)
        recs = []
        for p in PURPOSES:
            picks = sorted(((d, score(d, p)) for d in days), key=lambda x: (-x[1], x[0].date))[:3]
            picks = [x for x in picks if x[1] >= 2]
            if picks:
                txt = "、".join(f'<a href="#d-{d.date.isoformat()}">{md(d.date)}</a>{rank_label(sc)[0]}'
                                for d, sc in sorted(picks, key=lambda x: x[0].date))
                recs.append(f'<tr><th scope="row"><a href="{s.url(f"/purpose/{p.key}/")}">{ICONS[p.key]} {esc(p.short)}</a></th><td>{txt}</td></tr>')
        prev_y, prev_m = (y, m - 1) if m > 1 else (y - 1, 12)
        next_y, next_m = (y, m + 1) if m < 12 else (y + 1, 1)
        nav = []
        if prev_y in self.years:
            nav.append(f'<a href="{s.url(f"/calendar/{prev_y}/{prev_m:02d}/")}">‹ {prev_m}月</a>')
        nav.append(f'<a href="{s.url(f"/calendar/{y}/")}">{y}年の一覧</a>')
        if next_y in self.years:
            nav.append(f'<a href="{s.url(f"/calendar/{next_y}/{next_m:02d}/")}">{next_m}月 ›</a>')
        body = f"""
<h1>{y}年{m}月の開運日・吉日カレンダー</h1>
<p class="lead">{esc(lead)}</p>
<nav class="month-nav">{" ".join(nav)}</nav>
{month_grid(s, days)}
{s.ad('top')}
<section><h2>{m}月の開運日</h2>{"".join(sections)}</section>
<section><h2>{m}月の目的別おすすめ日</h2>
<div class="table-wrap"><table class="rule"><tbody>{"".join(recs)}</tbody></table></div>
<p class="small muted">◎最良 ○良い △まずまず。条件を変えて探すなら<a href="{s.url('/search/')}">吉日検索</a>へ。</p></section>
<section><h2>{m}月の注意したい日</h2>{"".join(bad)}</section>
{s.ad('middle')}
<section><h2>{m}月の祝日・二十四節気・雑節</h2><ul class="events">{"".join(events)}</ul></section>
<section><h2>{y}年{m}月の暦 一覧</h2>
<div class="table-wrap"><table class="list"><thead><tr><th scope="col">日付</th><th scope="col">六曜</th><th scope="col">干支</th><th scope="col">旧暦</th><th scope="col">暦注</th></tr></thead><tbody>{rows}</tbody></table></div></section>
<nav class="month-nav">{" ".join(nav)}</nav>
"""
        return f"/calendar/{y}/{m:02d}/", s.page(
            path=f"/calendar/{y}/{m:02d}/", title=f"{y}年{m}月の開運日・吉日カレンダー｜一粒万倍日・天赦日・大安・寅の日",
            description=f"{y}年{m}月の吉日カレンダー。{lead[:80]}",
            body=body, crumbs=[("カレンダー", "/calendar/"), (f"{y}年", f"/calendar/{y}/"), (f"{m}月", f"/calendar/{y}/{m:02d}/")])

    # ------------------------------------------------------------ 暦の解説
    def koyomi_index(self) -> tuple[str, str]:
        s = self.site
        body = f'<h1>暦の解説</h1><p class="lead">吉日・凶日の意味と決まり方、日程の一覧です。</p>{topic_cards(s)}'
        return "/koyomi/", s.page(path="/koyomi/", title="暦の解説｜吉日・凶日の意味と決まり方",
                                  description="一粒万倍日・天赦日・寅の日・巳の日・大安・不成就日・三隣亡など、暦注の意味と決まり方、日程の一覧。",
                                  body=body, crumbs=[("暦の解説", "/koyomi/")])

    def topic(self, slug: str) -> tuple[str, str]:
        s = self.site
        t = TOPICS[slug]
        y1, y2 = self.y1, self.y2
        fmt = {"y1": y1, "y2": y2}
        today = s.today
        marks = t.get("marks", [])
        lists = []
        next_html = ""
        if slug == "saikyo-kaiunbi":
            for y in (y1, y2):
                lists.append(f"<section><h2>{y}年の最強開運日・吉日が重なる日</h2>"
                             f"{date_table(s, special_days(self.year_days(y)), overlap_note)}</section>")
            nd = first_after(self.days, today, is_saikyo)
            next_html = next_box("最強開運日", 'data-next="saikyo"', countdown_text(nd, today))
        elif slug == "taian":
            for y in (y1, y2):
                yd = self.year_days(y)
                lists.append(f"<section><h2>{y}年の大安一覧</h2>"
                             + by_month_table(s, y, yd, lambda d: d.rokuyo_name == "大安", lambda d: d.is_rest_day)
                             + '<p class="small muted">色付きの日付は土日・祝日の大安です。</p>'
                             + f"<h3>{y}年の大安と一粒万倍日・天赦日が重なる日</h3>"
                             + date_table(s, [d for d in yd if d.rokuyo_name == "大安" and ({"ichiryu", "tensha"} & set(d.marks))])
                             + "</section>")
            nd = first_after(self.days, today, lambda d: d.rokuyo_name == "大安")
            next_html = next_box("大安", 'data-next="taian"', countdown_text(nd, today))
        elif slug == "rokuyo":
            rows = "".join(f'<tr><th scope="row">{n}<span class="small muted">（{r}）</span></th><td>{esc(desc)}</td></tr>'
                           for n, (r, desc) in ROKUYO_INFO.items())
            lists.append(f'<section><h2>六曜それぞれの意味</h2><div class="table-wrap"><table class="rule"><tbody>{rows}</tbody></table></div>'
                         f'<p>月ごとの六曜は<a href="{s.url(f"/calendar/{today.year}/{today.month:02d}/")}">今月のカレンダー</a>で確認できます。</p></section>')
            d = self.by_date[today]
            next_html = (f'<p class="next-box" data-today-rokuyo><span class="next-label">今日の六曜</span>'
                         f'<span class="next-body">{md(today)}は{d.rokuyo_name}</span></p>')
        elif slug == "doyo":
            for y in (y1, y2):
                yd = self.year_days(y)
                rows = []
                for d in yd:
                    if "土用入り" in d.zassetsu:
                        end = next(x for x in self.days if x.date >= d.date and "土用明け" in x.zassetsu)
                        ushi = [x for x in self.days if d.date <= x.date <= end.date and "土用の丑の日" in x.zassetsu]
                        season = {1: "冬", 4: "春", 7: "夏", 10: "秋"}.get(d.date.month, "")
                        rows.append(f'<tr data-date="{end.date.isoformat()}"><th scope="row">{season}の土用</th>'
                                    f'<td>{md(d.date)}〜{md(end.date)}</td><td>{"、".join(md(x.date) for x in ushi)}</td></tr>')
                lists.append(f'<section><h2>{y}年の土用と土用の丑の日</h2><div class="table-wrap"><table class="list"><thead>'
                             f'<tr><th scope="col">季節</th><th scope="col">期間</th><th scope="col">土用の丑の日</th></tr></thead>'
                             f'<tbody>{"".join(rows)}</tbody></table></div></section>')
        else:
            for y in (y1, y2):
                yd = [d for d in self.year_days(y) if any(k in d.marks for k in marks)]
                lists.append(f"<section><h2>{y}年の{t['name']}一覧（{len(yd)}日）</h2>{date_table(s, yd)}</section>")
            nd = first_after(self.days, today, lambda d: any(k in d.marks for k in marks))
            next_html = next_box(t["name"], f'data-next="{",".join(marks)}"', countdown_text(nd, today))
        sections = "".join(f"<section class=\"prose\"><h2>{h}</h2>{html}</section>" for h, html in t["sections"])
        dos = "".join(f"<li>{esc(x)}</li>" for x in t.get("dos", []))
        donts = "".join(f"<li>{esc(x)}</li>" for x in t.get("donts", []))
        dodont = ""
        if dos or donts:
            dodont = (f'<section><h2>{t["name"]}にやると良いこと・避けたいこと</h2><div class="two">'
                      f'<div class="card good"><h3>やると良いこと</h3><ul>{dos}</ul></div>'
                      f'<div class="card bad"><h3>避けたいこと</h3><ul>{donts}</ul></div></div></section>')
        related = "".join(f'<a class="pcard" href="{s.url(f"/purpose/{p.key}/")}"><span class="picon" aria-hidden="true">{ICONS[p.key]}</span>'
                          f'<span>{esc(p.name)}</span></a>'
                          for p in PURPOSES if any(p.weights.get(k, 0) >= 3 for k in marks))
        body = f"""
<h1>{esc(t['name'])}<span class="reading">（{esc(t['reading'])}）</span></h1>
<p class="lead">{t['lead']}</p>
{next_html}
{s.ad('top')}
{lists[0] if lists else ""}
{sections}
{dodont}
{s.ad('middle')}
{"".join(lists[1:])}
{faq_html(t.get("faq", []))}
{f'<section><h2>目的別に{esc(t["name"])}を活かす</h2><div class="pgrid">{related}</div></section>' if related else ""}
<section><h2>ほかの暦の解説</h2>{topic_cards(s)}</section>
"""
        return f"/koyomi/{slug}/", s.page(
            path=f"/koyomi/{slug}/", title=t["title"].format(**fmt), description=t["description"].format(**fmt),
            body=body, crumbs=[("暦の解説", "/koyomi/"), (t["name"], f"/koyomi/{slug}/")], faq=t.get("faq"))

    # ------------------------------------------------------------ 目的別
    def purpose_index(self) -> tuple[str, str]:
        s = self.site
        body = f'<h1>目的別の吉日</h1><p class="lead">やりたいことに合わせて、縁起の良い日を一覧で紹介しています。</p>{purpose_cards(s)}'
        return "/purpose/", s.page(path="/purpose/", title="目的別の吉日一覧｜財布・入籍・引っ越し・宝くじ・納車",
                                   description="財布の購入、入籍・結婚式、引っ越し、納車、宝くじ、開業、契約、神社参拝、旅行、地鎮祭に良い日を目的別に紹介。",
                                   body=body, crumbs=[("目的別", "/purpose/")])

    def purpose(self, p: Purpose) -> tuple[str, str]:
        s = self.site
        y1, y2 = self.y1, self.y2
        start = date(s.today.year, s.today.month, 1)
        end = date(y2, 12, 31)
        span = [d for d in self.days if start <= d.date <= end]
        picks = best_days(span, p)
        future = [(d, sc) for d, sc in picks if d.date >= s.today]
        top = max(future, key=lambda x: (x[1], -x[0].date.toordinal())) if future else None
        nd = next((d for d, sc in future if sc >= 5), None)
        faq = []
        if top:
            faq.append((f"{p.short}にいちばん良い日はいつですか？",
                        f"{ymd(s.today)}時点で、{end.year}年末までで最も評価が高いのは{top[0].date.year}年{md(top[0].date)}です"
                        f"（{'・'.join([top[0].rokuyo_name] + [MARKS[k].name for k in top[0].marks])}）。"))
        faq.append((f"{p.short}で避けたほうが良い日は？",
                    "・".join(key_name_and_summary(k)[0] for k, w in sorted(p.weights.items(), key=lambda kv: kv[1]) if w <= -2)
                    + "は避けるのが一般的です。"))
        tips = "".join(f"<li>{esc(x)}</li>" for x in p.tips)
        body = f"""
<h1>{esc(p.title_word)}【{y1}年・{y2}年】</h1>
<p class="lead">{esc(p.name)}日を、一粒万倍日・天赦日・大安などの暦注の重なりから評価し、月ごとのおすすめ日を自動で選んでいます。</p>
{next_box(f"{p.short}におすすめの日", f'data-next-purpose="{p.key}"', countdown_text(nd, s.today))}
{s.ad('top')}
<section><h2>{esc(p.short)}に良い日の選び方</h2>{weights_table(p)}</section>
{s.affiliate_box(p)}
<section><h2>{start.year}年{start.month}月〜{y2}年12月のおすすめ日</h2>
<p>各月で評価の高い日を最大5日まで表示しています。<span class="rest">休</span>は土日・祝日です。</p>
{best_table(s, picks, p)}
<p class="center"><a class="btn" href="{s.url(f'/search/?p={p.key}')}">期間や土日祝で絞り込んで探す</a></p></section>
{s.ad('middle')}
<section class="prose"><h2>{esc(p.short)}の日取りのポイント</h2><ul>{tips}</ul></section>
{faq_html(faq)}
<section><h2>ほかの目的</h2>{purpose_cards(s)}</section>
"""
        return f"/purpose/{p.key}/", s.page(
            path=f"/purpose/{p.key}/", title=f"{p.title_word}【{y1}年・{y2}年】おすすめの吉日カレンダー",
            description=f"{y1}年・{y2}年の{p.title_word}を月別に紹介。一粒万倍日・天赦日・大安・寅の日などの重なりから評価した{p.short}のおすすめ日と、避けたい日。",
            body=body, crumbs=[("目的別", "/purpose/"), (p.short, f"/purpose/{p.key}/")], faq=faq)

    # ------------------------------------------------------------ カレンダー登録
    def subscribe(self, feeds: list[tuple[str, str, str]]) -> tuple[str, str]:
        s = self.site
        from urllib.parse import quote
        rows = []
        for fname, title, desc in feeds:
            https = s.abs_url(f"/ics/{fname}")
            webcal = "webcal://" + https.split("://", 1)[1]
            google = f"https://calendar.google.com/calendar/render?cid={quote(webcal, safe='')}"
            rows.append(f'<div class="card feed"><h3>{esc(title)}</h3><p class="small">{esc(desc)}</p>'
                        f'<p><a class="btn small" href="{esc(google)}" target="_blank" rel="noopener">Googleカレンダーに追加</a> '
                        f'<a class="btn small ghost" href="{esc(webcal)}">iPhone・Macに追加</a></p>'
                        f'<p class="small muted">URL：<code>{esc(https)}</code></p></div>')
        body = f"""
<h1>開運日をスマホのカレンダーに自動表示する</h1>
<p class="lead">一粒万倍日・天赦日・寅の日・大安などを、GoogleカレンダーやiPhoneのカレンダーに<strong>無料で自動表示</strong>できます。一度登録すれば、新しい日程も自動で追加されます。</p>
{"".join(rows)}
<section class="prose"><h2>登録のしかた</h2>
<h3>Googleカレンダー（Android・パソコン）</h3>
<ol><li>上の「Googleカレンダーに追加」を押します。</li><li>確認画面で「追加」を押すと、他のカレンダーの一覧に表示されます。</li><li>うまくいかない場合は、パソコンのGoogleカレンダーで「他のカレンダー」の＋ →「URLで追加」にURLを貼り付けます。</li></ol>
<h3>iPhone・iPad・Mac</h3>
<ol><li>「iPhone・Macに追加」を押します。</li><li>「照会」または「登録」を選ぶと、カレンダーアプリに表示されます。</li><li>手動で登録する場合は、設定 → カレンダー → アカウント → アカウントを追加 → その他 →「照会するカレンダーを追加」にURLを入力します。</li></ol>
<p class="small muted">登録を解除したいときは、カレンダーアプリの設定からこのカレンダーを削除してください。</p>
</section>
"""
        return "/subscribe/", s.page(path="/subscribe/", title="開運日をGoogleカレンダー・iPhoneに自動表示する方法",
                                     description="一粒万倍日・天赦日・寅の日・大安などの開運日を、GoogleカレンダーやiPhoneのカレンダーに無料で自動表示できます。登録方法も解説。",
                                     body=body, crumbs=[("カレンダーに登録", "/subscribe/")])

    # ------------------------------------------------------------ 運営系
    def about(self) -> tuple[str, str]:
        s = self.site
        cfg = s.cfg
        body = f"""
<h1>運営者情報</h1>
<div class="table-wrap"><table class="rule"><tbody>
<tr><th scope="row">サイト名</th><td>{esc(s.name)}</td></tr>
<tr><th scope="row">URL</th><td>{esc(s.base_url)}/</td></tr>
<tr><th scope="row">運営者</th><td>{esc(cfg.get("operator", ""))}</td></tr>
<tr><th scope="row">お問い合わせ</th><td><a href="{s.url('/contact/')}">お問い合わせページ</a></td></tr>
</tbody></table></div>
<section class="prose"><h2>このサイトについて</h2>
<p>{esc(s.name)}は、日本の暦の吉日・凶日を、目的に合わせて調べられる無料のツールです。結婚や引っ越し、財布の新調など、日取りを決めるときの参考にしていただくことを目的としています。</p>
<h2>暦の計算方法</h2>
<p>太陽の位置（二十四節気）と月の満ち欠け（新月・満月）は、天文学の標準的なアルゴリズム（J. Meeus『Astronomical Algorithms』、VSOP87理論）で計算しています。計算結果は国立天文台が毎年発表する「暦要項」の二十四節気・朔弦望・国民の祝日と照合し、時刻が1分以内で一致することを確認しています。</p>
<p>旧暦は、新月の日を月の始まりとし、中気（雨水・春分など）を含むかどうかで月の名前と閏月を決める一般的な方法で求めています。六曜や不成就日は旧暦の日付から、一粒万倍日・天赦日・三隣亡・母倉日は節月（立春・啓蟄などの節入りで切り替わる月）と日の干支から決めています。</p>
<p>暦注には流派によって決まり方が異なるものがあります。当サイトで採用している決まり方は、各解説ページに掲載しています。</p>
</section>
"""
        return "/about/", s.page(path="/about/", title="運営者情報", description=f"{s.name}の運営者情報と、暦の計算方法について。",
                                 body=body, crumbs=[("運営者情報", "/about/")])

    def contact(self) -> tuple[str, str]:
        s = self.site
        cfg = s.cfg
        if cfg.get("contact_url"):
            how = f'<p><a class="btn" href="{esc(cfg["contact_url"])}" target="_blank" rel="noopener">お問い合わせフォームを開く</a></p>'
        elif cfg.get("contact_email"):
            how = f'<p>メール：<a href="mailto:{esc(cfg["contact_email"])}">{esc(cfg["contact_email"])}</a></p>'
        else:
            how = "<p>お問い合わせ窓口は現在準備中です。</p>"
        body = f"""
<h1>お問い合わせ</h1>
<p>{esc(s.name)}へのご意見・ご感想、掲載内容の誤りのご指摘などは、以下からお寄せください。</p>
{how}
<p class="small muted">内容によってはお返事できない場合や、お時間をいただく場合があります。暦注の解釈に関する個別のご相談にはお答えしていません。</p>
"""
        return "/contact/", s.page(path="/contact/", title="お問い合わせ", description=f"{s.name}へのお問い合わせ。",
                                   body=body, crumbs=[("お問い合わせ", "/contact/")])

    def privacy(self) -> tuple[str, str]:
        s = self.site
        a = s.cfg.get("affiliate", {})
        amazon = (f"<p>{esc(s.name)}は、Amazon.co.jpを宣伝しリンクすることによってサイトが紹介料を獲得できる手段を提供することを目的に設定されたアフィリエイトプログラムである、Amazonアソシエイト・プログラムの参加者です。"
                  f"Amazonのアソシエイトとして、{esc(s.name)}は適格販売により収入を得ています。</p>") if a.get("amazon_tag") else ""
        body = f"""
<h1>プライバシーポリシー・免責事項</h1>
<section class="prose">
<h2>個人情報の取り扱い</h2>
<p>当サイトでは、お問い合わせの際に名前やメールアドレス等の個人情報をお伺いする場合があります。取得した個人情報は、お問い合わせへの回答や必要な連絡のためにのみ利用し、法令に基づく場合を除き、本人の同意なく第三者に提供することはありません。</p>
<h2>広告の配信について</h2>
<p>当サイトは第三者配信の広告サービス「Google アドセンス」を利用する場合があります。広告配信事業者は、ユーザーの興味に応じた広告を表示するためにCookie（クッキー）を使用することがあります。Cookieを無効にする方法や、Googleによる広告でのCookieの使用については<a href="https://policies.google.com/technologies/ads?hl=ja" target="_blank" rel="noopener">Googleのポリシーと規約</a>をご覧ください。パーソナライズ広告は<a href="https://myadcenter.google.com/" target="_blank" rel="noopener">マイアドセンター</a>から無効にできます。</p>
<h2>アフィリエイトについて</h2>
<p>当サイトは、商品やサービスを紹介するアフィリエイトプログラムに参加する場合があります。紹介リンクには「PR」と表記しています。リンク先での購入・契約に関するお問い合わせは、各販売事業者へお願いいたします。</p>
{amazon}
<h2>アクセス解析について</h2>
<p>当サイトでは、サイトの改善のためにアクセス解析ツール（Google アナリティクス、Cloudflare Web Analytics 等）を利用する場合があります。これらはトラフィックデータの収集のためにCookie等を使用することがありますが、個人を特定する情報は含まれません。Google アナリティクスによるデータ収集は、<a href="https://tools.google.com/dlpage/gaoptout?hl=ja" target="_blank" rel="noopener">オプトアウトアドオン</a>で無効にできます。</p>
<h2>免責事項</h2>
<p>当サイトに掲載している吉日・凶日などの暦注は、古くからの言い伝えや慣習にもとづくものであり、その効果を保証するものではありません。暦注には流派による違いがあり、他の暦と日付が異なる場合があります。重要な日取りを決める際は、関係者や専門家にもご確認ください。</p>
<p>当サイトの情報の正確性には万全を期していますが、掲載内容によって生じたいかなる損害についても責任を負いかねます。リンク先の外部サイトの内容についても責任を負いません。</p>
<h2>著作権</h2>
<p>当サイトの文章・画像等の著作権は運営者に帰属します。無断転載はご遠慮ください。</p>
<h2>改定</h2>
<p>本ポリシーの内容は、法令の変更等に応じて予告なく改定することがあります。</p>
<p class="muted small">制定日：{s.today.year}年{s.today.month}月{s.today.day}日</p>
</section>
"""
        return "/privacy/", s.page(path="/privacy/", title="プライバシーポリシー・免責事項",
                                   description=f"{s.name}のプライバシーポリシー、広告・アフィリエイト・アクセス解析、免責事項について。",
                                   body=body, crumbs=[("プライバシーポリシー", "/privacy/")])

    def not_found(self) -> tuple[str, str]:
        s = self.site
        body = f"""
<h1>ページが見つかりません</h1>
<p>お探しのページは移動または削除された可能性があります。</p>
<p><a class="btn" href="{s.url('/')}">トップページへ</a> <a class="btn ghost" href="{s.url('/search/')}">吉日検索へ</a></p>
"""
        return "/404.html", s.page(path="/404.html", title="ページが見つかりません", description="ページが見つかりません。",
                                   body=body, noindex=True)
