"""複数のページで使う表示部品（カレンダー、日付リスト、おすすめ日の抽出）。"""
from __future__ import annotations

from datetime import date

from koyomi.calendar import DayInfo
from koyomi.marks import (MARKS, ROKUYO_INFO, Purpose, is_saikyo, kaiun_overlap, rank_label,
                          score)

from .html import Site, badges, esc, md

WEEK_HEAD = ["日", "月", "火", "水", "木", "金", "土"]


def day_link(site: Site, d: date) -> str:
    return site.url(f"/calendar/{d.year}/{d.month:02d}/#d-{d.isoformat()}")


def month_grid(site: Site, days: list[DayInfo]) -> str:
    """日曜はじまりの月カレンダー。"""
    first = days[0].date
    lead_blank = (first.weekday() + 1) % 7
    cells = ['<td class="blank"></td>'] * lead_blank
    for d in days:
        cls = ["day"]
        wd = d.date.weekday()
        if d.holiday or wd == 6:
            cls.append("sun")
        elif wd == 5:
            cls.append("sat")
        if is_saikyo(d):
            cls.append("saikyo")
        elif "tensha" in d.marks:
            cls.append("tensha")
        marks = "".join(f'<span class="cm m-{k}" title="{MARKS[k].name}">{MARKS[k].short}</span>'
                        for k in d.marks)
        rk_cls = {"大安": " rk-good", "仏滅": " rk-bad", "赤口": " rk-bad"}.get(d.rokuyo_name, "")
        extra = ""
        if d.holiday:
            extra += f'<span class="hol">{esc(d.holiday)}</span>'
        if d.sekki:
            extra += f'<span class="sekki">{esc(d.sekki)}</span>'
        if d.moon:
            extra += f'<span class="moon">{"●" if d.moon == "新月" else "○"}{d.moon}</span>'
        cells.append(
            f'<td class="{" ".join(cls)}" id="d-{d.date.isoformat()}" data-date="{d.date.isoformat()}">'
            f'<span class="dn">{d.date.day}</span><span class="rk{rk_cls}">{d.rokuyo_name}</span>'
            f'{extra}<span class="cms">{marks}</span></td>')
    while len(cells) % 7:
        cells.append('<td class="blank"></td>')
    rows = "".join("<tr>" + "".join(cells[i:i + 7]) + "</tr>" for i in range(0, len(cells), 7))
    head = "".join(f'<th scope="col" class="{"sun" if i == 0 else "sat" if i == 6 else ""}">{w}</th>'
                   for i, w in enumerate(WEEK_HEAD))
    return (f'<div class="cal-wrap"><table class="cal"><caption class="sr">{first.year}年{first.month}月の暦</caption>'
            f'<thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table></div>'
            + legend())


def legend() -> str:
    items = "".join(f'<span class="cm m-{k}">{MARKS[k].short}</span>{MARKS[k].name}'
                    for k in ["tensha", "ichiryu", "tora", "mi", "tsuchinotomi", "kinoene",
                              "tenon", "daimyo", "bosou", "fujoju", "sanrinbo"])
    return f'<p class="legend small">{items}</p>'


def date_table(site: Site, days: list[DayInfo], note_fn=None) -> str:
    """日付・六曜・重なる暦注の一覧表（閲覧日より前の行はJSで薄く表示）。"""
    rows = []
    for d in days:
        note = note_fn(d) if note_fn else ""
        rest = ' <span class="rest">休</span>' if d.is_rest_day else ""
        rows.append(f'<tr data-date="{d.date.isoformat()}"><td class="nowrap">'
                    f'<a href="{day_link(site, d.date)}">{md(d.date)}</a>{rest}</td>'
                    f'<td>{badges(d)}{note}</td></tr>')
    if not rows:
        return '<p class="muted">該当する日はありません。</p>'
    return (f'<div class="table-wrap"><table class="list"><thead><tr><th scope="col">日付</th>'
            f'<th scope="col">六曜・重なる暦注</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>')


def by_month_table(site: Site, year: int, days: list[DayInfo], pred, highlight=None) -> str:
    """月ごとに該当日を並べる表（大安など日数が多いもの向け）。"""
    rows = []
    for m in range(1, 13):
        hits = [d for d in days if d.date.month == m and pred(d)]
        cells = []
        for d in hits:
            cls = ' class="hl"' if highlight and highlight(d) else ""
            cells.append(f'<a{cls} href="{day_link(site, d.date)}" data-date="{d.date.isoformat()}">'
                         f'{d.date.day}日<small>（{"月火水木金土日"[d.date.weekday()]}）</small></a>')
        rows.append(f'<tr><th scope="row"><a href="{site.url(f"/calendar/{year}/{m:02d}/")}">{m}月</a></th>'
                    f'<td class="days">{" ".join(cells) or "－"}</td></tr>')
    return (f'<div class="table-wrap"><table class="bymonth"><tbody>{"".join(rows)}</tbody></table></div>')


def special_days(days: list[DayInfo]) -> list[DayInfo]:
    """最強開運日、または主要な吉日（大安を含む）が3つ以上重なる日。"""
    return [d for d in days if is_saikyo(d) or len(kaiun_overlap(d)) >= 3]


def overlap_note(d: DayInfo) -> str:
    names = kaiun_overlap(d)
    label = "最強開運日" if is_saikyo(d) else f"{len(names)}つの吉日が重なる日"
    return f'<span class="note">{label}：{"・".join(names)}</span>'


def best_days(days: list[DayInfo], purpose: Purpose, per_month: int = 5) -> list[tuple[DayInfo, int]]:
    """目的別のおすすめ日を月ごとに抽出する。"""
    result = []
    months = sorted({(d.date.year, d.date.month) for d in days})
    for ym in months:
        scored = [(d, score(d, purpose)) for d in days if (d.date.year, d.date.month) == ym]
        # 「良い」以上の日を優先し、なければ「まずまず」の日から選ぶ
        good = [x for x in scored if x[1] >= 5] or [x for x in scored if x[1] >= 2]
        top = sorted(good, key=lambda x: (-x[1], x[0].date))[:per_month]
        result.extend(sorted(top, key=lambda x: x[0].date))
    return result


def best_table(site: Site, picks: list[tuple[DayInfo, int]], purpose: Purpose) -> str:
    rows = []
    for d, s in picks:
        sym, label = rank_label(s)
        reasons = [purpose.reasons[k] for k in d.marks if k in purpose.reasons and purpose.weights.get(k, 0) > 0]
        rest = ' <span class="rest">休</span>' if d.is_rest_day else ""
        rows.append(f'<tr data-date="{d.date.isoformat()}"><td class="nowrap">'
                    f'<a href="{day_link(site, d.date)}">{d.date.year}年{md(d.date)}</a>{rest}</td>'
                    f'<td class="rank r{"3" if s >= 8 else "2" if s >= 5 else "1"}">{sym}<span class="small">{label}</span></td>'
                    f'<td>{badges(d)}<span class="note">{esc("・".join(dict.fromkeys(reasons)))}</span></td></tr>')
    return (f'<div class="table-wrap"><table class="list"><thead><tr><th scope="col">日付</th>'
            f'<th scope="col">評価</th><th scope="col">六曜・暦注</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table></div>')


ROKUYO_BY_KEY = {"taian": "大安", "tomobiki": "友引", "sensho": "先勝", "senbu": "先負",
                 "shakku": "赤口", "butsumetsu": "仏滅"}


def key_name_and_summary(key: str) -> tuple[str, str]:
    if key in MARKS:
        return MARKS[key].name, MARKS[key].summary
    if key in ROKUYO_BY_KEY:
        name = ROKUYO_BY_KEY[key]
        return name, ROKUYO_INFO[name][1]
    return "土用の期間", "土を掘る・動かす作業を避ける期間"


def weights_table(purpose: Purpose) -> str:
    rows = []
    for key, w in sorted(purpose.weights.items(), key=lambda kv: -kv[1]):
        name, summary = key_name_and_summary(key)
        stars = "★" * min(w, 5) if w > 0 else "✕" * min(-w // 2 + 1, 3)
        cls = "good" if w > 0 else "bad"
        rows.append(f'<tr><th scope="row">{name}</th><td class="{cls}">{stars}</td>'
                    f'<td>{esc(purpose.reasons.get(key, summary))}</td></tr>')
    return (f'<div class="table-wrap"><table class="rule"><thead><tr><th scope="col">暦注</th>'
            f'<th scope="col">重み</th><th scope="col">理由</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>'
            '<p class="small muted">※天赦日は凶日を打ち消す大吉日とされるため、天赦日と重なる仏滅・赤口は減点していません。</p>')


def next_box(label: str, attrs: str, fallback: str) -> str:
    return f'<p class="next-box" {attrs}><span class="next-label">次の{esc(label)}</span><span class="next-body">{fallback}</span></p>'


def first_after(days: list[DayInfo], today: date, pred) -> DayInfo | None:
    return next((d for d in days if d.date >= today and pred(d)), None)


def countdown_text(d: DayInfo | None, today: date) -> str:
    if d is None:
        return "計算範囲内にありません"
    diff = (d.date - today).days
    when = "今日" if diff == 0 else f"あと{diff}日"
    return f"{d.date.year}年{md(d.date)}（{when}）"
