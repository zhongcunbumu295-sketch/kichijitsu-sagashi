"""日ごとの暦情報: 旧暦・六曜・干支・節月・二十四節気・雑節・祝日・選日（暦注）。

暦注の決まり方は流派で違うものがある。このサイトで採用している定義:
  - 一粒万倍日・天赦日・三隣亡・母倉日: 節月（節入りの日から切り替わる月）で判定
  - 不成就日・六曜: 旧暦の月日で判定
  - 大明日: 25干支説 / 母倉日: 土用の月（辰・未・戌・丑月）は巳・午の日
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

from .astro import (JST, jde_to_jst, jst_to_jde, moon_phases, solar_longitude_events,
                    solar_term_jde)

STEMS = "甲乙丙丁戊己庚辛壬癸"
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
ROKUYO = ["大安", "赤口", "先勝", "友引", "先負", "仏滅"]
WEEKDAYS = "月火水木金土日"

SEKKI = {
    0: "春分", 15: "清明", 30: "穀雨", 45: "立夏", 60: "小満", 75: "芒種",
    90: "夏至", 105: "小暑", 120: "大暑", 135: "立秋", 150: "処暑", 165: "白露",
    180: "秋分", 195: "寒露", 210: "霜降", 225: "立冬", 240: "小雪", 255: "大雪",
    270: "冬至", 285: "小寒", 300: "大寒", 315: "立春", 330: "雨水", 345: "啓蟄",
}
# 節月の名前（0 = 寅月 = 立春から）
SETSUGETSU = "寅卯辰巳午未申酉戌亥子丑"
LUNAR_MONTH_NAMES = ["", "睦月", "如月", "弥生", "卯月", "皐月", "水無月",
                     "文月", "葉月", "長月", "神無月", "霜月", "師走"]

# ---------------------------------------------------------------- 選日の定義
# 節月 → 一粒万倍日になる十二支
_ICHIRYU = {0: {1, 6}, 1: {2, 9}, 2: {0, 3}, 3: {3, 4}, 4: {5, 6}, 5: {9, 6},
            6: {0, 7}, 7: {3, 8}, 8: {9, 6}, 9: {9, 10}, 10: {11, 0}, 11: {3, 0}}
# 季節（節月 // 3）→ 天赦日の干支: 春 戊寅 / 夏 甲午 / 秋 戊申 / 冬 甲子
_TENSHA = {0: 14, 1: 30, 2: 44, 3: 0}
# 節月 → 三隣亡の十二支（1・4・7・10月 亥 / 2・5・8・11月 寅 / 3・6・9・12月 午）
_SANRINBO = {m: (11, 2, 6)[m % 3] for m in range(12)}
# 旧暦の月 → 不成就日
_FUJOJU = {1: {3, 11, 19, 27}, 2: {2, 10, 18, 26}, 3: {1, 9, 17, 25},
           4: {4, 12, 20, 28}, 5: {5, 13, 21, 29}, 6: {6, 14, 22, 30}}
_TENON = {0, 1, 2, 3, 4, 15, 16, 17, 18, 19, 45, 46, 47, 48, 49}
_DAIMYO = {54, 5, 6, 7, 8, 9, 13, 15, 18, 20, 23, 28, 31, 38, 40, 41, 42, 43,
           45, 46, 47, 52, 55, 56, 57}
# 節月 → 母倉日の十二支（春=亥子 / 夏=寅卯 / 秋=辰戌丑未 / 冬=申酉 / 土用の月=巳午）
_BOSOU = {0: {11, 0}, 1: {11, 0}, 3: {2, 3}, 4: {2, 3}, 6: {4, 10, 1, 7},
          7: {4, 10, 1, 7}, 9: {8, 9}, 10: {8, 9}, 2: {5, 6}, 5: {5, 6},
          8: {5, 6}, 11: {5, 6}}


@dataclass
class DayInfo:
    date: date
    kanshi: int                 # 日の干支（0 = 甲子）
    rokuyo: int                 # ROKUYO の添字
    lunar_month: int
    lunar_day: int
    lunar_leap: bool
    setsugetsu: int             # 0 = 寅月
    sekki: str | None = None    # この日に入る二十四節気
    sekki_time: str | None = None
    zassetsu: list[str] = field(default_factory=list)
    holiday: str | None = None
    moon: str | None = None     # "新月" / "満月"
    moon_age: float = 0.0       # 正午の月齢
    doyo: bool = False          # 土用の期間中
    marks: list[str] = field(default_factory=list)

    @property
    def kanshi_name(self) -> str:
        return STEMS[self.kanshi % 10] + BRANCHES[self.kanshi % 12]

    @property
    def branch(self) -> int:
        return self.kanshi % 12

    @property
    def rokuyo_name(self) -> str:
        return ROKUYO[self.rokuyo]

    @property
    def weekday_name(self) -> str:
        return WEEKDAYS[self.date.weekday()]

    @property
    def lunar_name(self) -> str:
        leap = "閏" if self.lunar_leap else ""
        return f"{leap}{self.lunar_month}月{self.lunar_day}日"

    @property
    def is_rest_day(self) -> bool:
        return self.date.weekday() >= 5 or self.holiday is not None


def kanshi_of(d: date) -> int:
    jdn = d.toordinal() + 1721425
    return (jdn + 49) % 60


def japanese_holidays(year: int, shunbun: date, shubun: date) -> dict[date, str]:
    """国民の祝日・振替休日・国民の休日（2020年以降の祝日法）。"""
    def nth_monday(month: int, n: int) -> date:
        first = date(year, month, 1)
        return first + timedelta(days=(-first.weekday()) % 7 + 7 * (n - 1))

    base = {
        date(year, 1, 1): "元日", nth_monday(1, 2): "成人の日",
        date(year, 2, 11): "建国記念の日", date(year, 2, 23): "天皇誕生日",
        shunbun: "春分の日", date(year, 4, 29): "昭和の日",
        date(year, 5, 3): "憲法記念日", date(year, 5, 4): "みどりの日",
        date(year, 5, 5): "こどもの日", nth_monday(7, 3): "海の日",
        date(year, 8, 11): "山の日", nth_monday(9, 3): "敬老の日",
        shubun: "秋分の日", nth_monday(10, 2): "スポーツの日",
        date(year, 11, 3): "文化の日", date(year, 11, 23): "勤労感謝の日",
    }
    result = dict(base)
    for d in sorted(base):
        if d.weekday() == 6:
            n = d + timedelta(days=1)
            while n in result:
                n += timedelta(days=1)
            result[n] = "振替休日"
    for d in sorted(base):
        mid = d + timedelta(days=1)
        if d + timedelta(days=2) in base and mid not in result and mid.weekday() != 6:
            result[mid] = "国民の休日"
    return result


class Koyomi:
    """start〜end の暦をまとめて計算する。"""

    def __init__(self, start: date, end: date):
        self.start, self.end = start, end
        margin_start = start - timedelta(days=420)
        margin_end = end + timedelta(days=60)

        events = solar_longitude_events(margin_start, margin_end)
        self.solar_events = [(lon, dt) for lon, dt in events]
        self._sekki_by_date = {dt.date(): (SEKKI[lon], dt) for lon, dt in events}
        # 節入り（黄経 15+30n 度）→ 節月の切り替わり
        self._setsu = [(dt.date(), ((lon - 315) // 30) % 12)
                       for lon, dt in events if lon % 30 == 15]
        chuki = [(dt.date(), lon) for lon, dt in events if lon % 30 == 0]
        self._lunar_months = self._build_lunar_months(margin_start, margin_end, chuki)
        self._new_moons = moon_phases(margin_start, margin_end)
        self._full_moon_dates = {dt.date() for dt in moon_phases(margin_start, margin_end, full=True)}
        self._zassetsu, self._doyo_ranges = self._build_zassetsu(events)
        self._holidays: dict[date, str] = {}
        by_lon_year = {(dt.year, lon): dt.date() for lon, dt in events}
        for y in range(start.year, end.year + 1):
            self._holidays.update(japanese_holidays(y, by_lon_year[(y, 0)], by_lon_year[(y, 180)]))

    # ------------------------------------------------------------ 旧暦
    @staticmethod
    def _build_lunar_months(margin_start, margin_end, chuki):
        new_moon_dates = [dt.date() for dt in moon_phases(margin_start, margin_end)]
        months = []
        for s, e in zip(new_moon_dates, new_moon_dates[1:]):
            inside = [lon for d, lon in chuki if s <= d < e]
            if len(inside) > 1:
                raise ValueError(f"中気を2つ含む月があります（{s}）。2033年問題の対応が必要です。")
            if inside:
                num = (inside[0] // 30 + 2) % 12 or 12
                months.append([s, e, num, False])
            elif months:
                months.append([s, e, months[-1][2], True])
        return months

    def lunar_date(self, d: date) -> tuple[int, int, bool]:
        for s, e, num, leap in self._lunar_months:
            if s <= d < e:
                return num, (d - s).days + 1, leap
        raise ValueError(f"{d} は計算範囲外です")

    def setsugetsu(self, d: date) -> int:
        current = None
        for sd, idx in self._setsu:
            if sd <= d:
                current = idx
            else:
                break
        if current is None:
            raise ValueError(f"{d} は計算範囲外です")
        return current

    # ------------------------------------------------------------ 雑節
    def _build_zassetsu(self, events):
        z: dict[date, list[str]] = {}

        def add(d: date, name: str):
            z.setdefault(d, []).append(name)

        risshun = {dt.year: dt.date() for lon, dt in events if lon == 315}
        for y, d in risshun.items():
            add(d - timedelta(days=1), "節分")
            add(d + timedelta(days=87), "八十八夜")
            add(d + timedelta(days=209), "二百十日")
            add(d + timedelta(days=219), "二百二十日")
        doyo_ranges = []
        ritsu = sorted(dt.date() for lon, dt in events if lon in (315, 45, 135, 225))
        for lon, dt in events:
            if lon in (0, 180):
                d = dt.date()
                add(d - timedelta(days=3), "彼岸入り")
                add(d, "彼岸の中日")
                add(d + timedelta(days=3), "彼岸明け")
        # 土用入り（黄経 27, 117, 207, 297 度）・入梅（80度）・半夏生（100度）は15度刻みにないので個別に求める
        for y in range(self.start.year - 1, self.end.year + 2):
            for lon, approx_month in ((297, 1), (27, 4), (117, 7), (207, 10), (80, 6), (100, 7)):
                guess = jst_to_jde(datetime(y, approx_month, 15, tzinfo=JST))
                d = jde_to_jst(solar_term_jde(lon, guess)).date()
                if lon == 80:
                    add(d, "入梅")
                elif lon == 100:
                    add(d, "半夏生")
                else:
                    next_ritsu = next((r for r in ritsu if r > d), None)
                    if next_ritsu is None:
                        continue
                    add(d, "土用入り")
                    end = next_ritsu - timedelta(days=1)
                    doyo_ranges.append((d, end))
                    add(end, "土用明け")
                    cur = d
                    while cur <= end:
                        if kanshi_of(cur) % 12 == 1:
                            add(cur, "土用の丑の日")
                        cur += timedelta(days=1)
        return z, doyo_ranges

    # ------------------------------------------------------------ 1日分
    def day(self, d: date) -> DayInfo:
        k = kanshi_of(d)
        lm, ld, leap = self.lunar_date(d)
        sg = self.setsugetsu(d)
        info = DayInfo(date=d, kanshi=k, rokuyo=(lm + ld) % 6, lunar_month=lm,
                       lunar_day=ld, lunar_leap=leap, setsugetsu=sg)
        if d in self._sekki_by_date:
            name, dt = self._sekki_by_date[d]
            # 暦要項と同じく分単位に四捨五入して表示する
            info.sekki, info.sekki_time = name, (dt + timedelta(seconds=30)).strftime("%H:%M")
        info.zassetsu = list(self._zassetsu.get(d, []))
        info.holiday = self._holidays.get(d)
        info.doyo = any(s <= d <= e for s, e in self._doyo_ranges)
        noon = datetime(d.year, d.month, d.day, 12, tzinfo=JST)
        last_new = max(dt for dt in self._new_moons if dt <= noon)
        info.moon_age = round((noon - last_new).total_seconds() / 86400, 1)
        if any(dt.date() == d for dt in self._new_moons):
            info.moon = "新月"
        elif d in self._full_moon_dates:
            info.moon = "満月"

        branch = k % 12
        marks = []
        if k == _TENSHA[sg // 3]:
            marks.append("tensha")
        if branch in _ICHIRYU[sg]:
            marks.append("ichiryu")
        if branch == 2:
            marks.append("tora")
        if branch == 5:
            marks.append("mi")
        if k == 5:
            marks.append("tsuchinotomi")
        if k == 0:
            marks.append("kinoene")
        if k in _TENON:
            marks.append("tenon")
        if k in _DAIMYO:
            marks.append("daimyo")
        if branch in _BOSOU[sg]:
            marks.append("bosou")
        if ld in _FUJOJU[(lm - 1) % 6 + 1]:
            marks.append("fujoju")
        if branch == _SANRINBO[sg]:
            marks.append("sanrinbo")
        info.marks = marks
        return info

    def days(self, start: date | None = None, end: date | None = None) -> list[DayInfo]:
        cur, last = start or self.start, end or self.end
        out = []
        while cur <= last:
            out.append(self.day(cur))
            cur += timedelta(days=1)
        return out
