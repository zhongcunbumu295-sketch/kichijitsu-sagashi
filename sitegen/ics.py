"""カレンダー購読用の iCalendar（.ics）ファイル。"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from koyomi.calendar import DayInfo
from koyomi.marks import KAIUN_KEYS, MARKS, is_saikyo, kaiun_overlap

ICON = {"tensha": "🌟", "ichiryu": "🌾", "tora": "🐯", "mi": "🐍", "tsuchinotomi": "🐍",
        "kinoene": "🐭", "fujoju": "⚠"}

# (ファイル名, カレンダー名, 説明, 判定関数, 表示する暦注)
FEEDS = [
    ("kaiun.ics", "開運日（すべて）", "天赦日・一粒万倍日・寅の日・巳の日・己巳の日・甲子の日・大安",
     lambda d: bool(kaiun_overlap(d)), KAIUN_KEYS + ["taian"]),
    ("special.ics", "特別な開運日だけ", "天赦日と、主要な吉日が3つ以上重なる日（最強開運日など）",
     lambda d: "tensha" in d.marks or len(kaiun_overlap(d)) >= 3, KAIUN_KEYS + ["taian"]),
    ("ichiryu.ics", "一粒万倍日", "一粒万倍日だけを表示します", lambda d: "ichiryu" in d.marks, ["ichiryu"]),
    ("tensha.ics", "天赦日", "天赦日だけを表示します", lambda d: "tensha" in d.marks, ["tensha"]),
    ("tora.ics", "寅の日", "寅の日だけを表示します", lambda d: "tora" in d.marks, ["tora"]),
    ("mi.ics", "巳の日・己巳の日", "巳の日と己巳の日を表示します", lambda d: "mi" in d.marks, ["mi", "tsuchinotomi"]),
    ("taian.ics", "大安", "大安の日を表示します", lambda d: d.rokuyo_name == "大安", ["taian"]),
    ("fujoju.ics", "不成就日（注意日）", "何事も成就しないとされる不成就日を表示します", lambda d: "fujoju" in d.marks, ["fujoju"]),
]


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def _fold(line: str) -> str:
    """RFC 5545: 1行75オクテットまで。マルチバイト文字の途中では折り返さない。"""
    chunks, buf, limit = [], b"", 75
    for ch in line:
        b = ch.encode("utf-8")
        if len(buf) + len(b) > limit:
            chunks.append(buf)
            buf, limit = b"", 74
        buf += b
    chunks.append(buf)
    return "\r\n ".join(c.decode("utf-8") for c in chunks)


def _summary(d: DayInfo, keys: list[str]) -> str:
    if is_saikyo(d) and "tensha" in keys:
        return "🌟最強開運日（" + "・".join(kaiun_overlap(d)) + "）"
    names = []
    for k in keys:
        if k == "taian":
            if d.rokuyo_name == "大安":
                names.append("大安")
        elif k in d.marks:
            if k == "mi" and "tsuchinotomi" in d.marks and "tsuchinotomi" in keys:
                continue
            names.append(ICON.get(k, "") + MARKS[k].name)
    return "・".join(names)


def build_feed(site_name: str, base_url: str, feed, days: list[DayInfo], stamp: datetime) -> str:
    fname, title, desc, pred, keys = feed
    domain = base_url.split("://", 1)[-1].split("/", 1)[0]
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", f"PRODID:-//{site_name}//koyomi//JA",
             "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
             f"X-WR-CALNAME:{_escape(title + '｜' + site_name)}", f"X-WR-CALDESC:{_escape(desc)}",
             "X-WR-TIMEZONE:Asia/Tokyo", "REFRESH-INTERVAL;VALUE=DURATION:P1D", "X-PUBLISHED-TTL:P1D"]
    ts = stamp.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    for d in days:
        if not pred(d):
            continue
        url = f"{base_url}/calendar/{d.date.year}/{d.date.month:02d}/#d-{d.date.isoformat()}"
        notes = [f"{MARKS[k].name}：{MARKS[k].summary}" for k in d.marks if k in MARKS]
        notes.insert(0, f"六曜：{d.rokuyo_name}")
        lines += ["BEGIN:VEVENT",
                  f"UID:{d.date:%Y%m%d}-{fname.split('.')[0]}@{domain}",
                  f"DTSTAMP:{ts}",
                  f"DTSTART;VALUE=DATE:{d.date:%Y%m%d}",
                  f"DTEND;VALUE=DATE:{d.date + timedelta(days=1):%Y%m%d}",
                  f"SUMMARY:{_escape(_summary(d, keys))}",
                  f"DESCRIPTION:{_escape(chr(10).join(notes + ['', url]))}",
                  f"URL:{url}",
                  "TRANSP:TRANSPARENT",
                  "END:VEVENT"]
    lines.append("END:VCALENDAR")
    return "\r\n".join(_fold(line) for line in lines) + "\r\n"


def feed_range(days: list[DayInfo], today: date) -> list[DayInfo]:
    """購読カレンダーには、先月から2年先までを入れる。"""
    start, end = today - timedelta(days=31), today + timedelta(days=731)
    return [d for d in days if start <= d.date <= end]
