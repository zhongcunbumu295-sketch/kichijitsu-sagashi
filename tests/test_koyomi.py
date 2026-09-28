"""暦計算の検証。実行: python -m unittest discover -s tests

- 二十四節気・朔望・祝日・雑節: 国立天文台「暦要項」（tests/naoj_reference.json）と照合
- 2026年の選日: 複数の暦サイトで一致している日付と照合
"""
import json
import unittest
from datetime import date, datetime
from pathlib import Path

from koyomi.astro import JST, moon_phases, solar_longitude_events
from koyomi.calendar import Koyomi, kanshi_of

REF = json.loads(Path(__file__).with_name("naoj_reference.json").read_text(encoding="utf-8"))
YEARS = sorted(int(y) for y in REF)
KOYOMI = Koyomi(date(YEARS[0], 1, 1), date(YEARS[-1], 12, 31))


def parse(ts: str) -> datetime:
    return datetime.strptime(ts, "%Y-%m-%d %H:%M").replace(tzinfo=JST)


def dates_with(mark: str, year: int) -> list[date]:
    return [d.date for d in KOYOMI.days(date(year, 1, 1), date(year, 12, 31)) if mark in d.marks]


def md(year: int, table: dict[int, list[int]]) -> list[date]:
    return [date(year, m, d) for m, days in sorted(table.items()) for d in days]


class AstronomyTest(unittest.TestCase):
    def test_solar_terms_match_naoj(self):
        events = solar_longitude_events(date(YEARS[0], 1, 1), date(YEARS[-1], 12, 31))
        calc = {(dt.year, lon): dt for lon, dt in events}
        for y in YEARS:
            for name, lon, ts in REF[str(y)]["solar_terms"]:
                ref = parse(ts)
                diff = (calc[(ref.year, lon)] - ref).total_seconds()
                # 暦要項の時刻は分単位に丸めてあるので ±30秒 + 計算誤差を許容
                self.assertLessEqual(abs(diff), 45, f"{name} {ts}: {diff:.0f}秒ずれ")

    def test_moon_phases_match_naoj(self):
        for full, label in ((False, "朔"), (True, "望")):
            calc = moon_phases(date(YEARS[0], 1, 1), date(YEARS[-1], 12, 31), full=full)
            refs = [parse(ts) for y in YEARS for p, ts in REF[str(y)]["moon_phases"] if p == label]
            self.assertEqual(len(calc), len(refs), label)
            for c, r in zip(calc, refs):
                diff = (c - r).total_seconds()
                self.assertLessEqual(abs(diff), 45, f"{label} {r}: {diff:.0f}秒ずれ")


class CalendarTest(unittest.TestCase):
    def test_holidays_match_naoj(self):
        for y in YEARS:
            expected = {date.fromisoformat(d) for d, _ in REF[str(y)]["holidays"]}
            actual = {d.date for d in KOYOMI.days(date(y, 1, 1), date(y, 12, 31)) if d.holiday}
            self.assertEqual(actual, expected, y)

    def test_zassetsu_match_naoj(self):
        names = {"土用": "土用入り", "彼岸": "彼岸入り"}
        for y in YEARS:
            for name, d, _ in REF[str(y)]["zassetsu"]:
                info = KOYOMI.day(date.fromisoformat(d))
                self.assertIn(names.get(name, name), info.zassetsu, f"{name} {d}")

    def test_kanshi_anchor(self):
        self.assertEqual(KOYOMI.day(date(2026, 10, 1)).kanshi_name, "戊申")
        self.assertEqual(kanshi_of(date(2000, 1, 1)), 54)  # 戊午

    def test_lunar_new_year(self):
        # 旧正月（旧暦1月1日）
        for y, d in ((2025, date(2025, 1, 29)), (2026, date(2026, 2, 17)), (2027, date(2027, 2, 7))):
            info = KOYOMI.day(d)
            self.assertEqual((info.lunar_month, info.lunar_day, info.lunar_leap), (1, 1, False), y)
            self.assertEqual(info.rokuyo_name, "先勝")

    def test_leap_month_2025(self):
        # 2025年は閏6月（7月25日から）
        info = KOYOMI.day(date(2025, 7, 25))
        self.assertEqual((info.lunar_month, info.lunar_day, info.lunar_leap), (6, 1, True))


class Senjitsu2026Test(unittest.TestCase):
    """2026年の選日。複数の暦サイトで一致する日付。"""

    def test_ichiryu(self):
        expected = md(2026, {1: [1, 2, 5, 14, 17, 26, 29], 2: [8, 13, 20, 25],
                             3: [4, 5, 12, 17, 24, 29], 4: [8, 11, 20, 23],
                             5: [2, 5, 6, 17, 18, 29, 30], 6: [12, 13, 24, 25],
                             7: [6, 7, 10, 19, 22, 31], 8: [3, 13, 18, 25, 30],
                             9: [6, 7, 14, 19, 26], 10: [1, 11, 14, 23, 26],
                             11: [4, 7, 8, 19, 20], 12: [1, 2, 15, 16, 27, 28]})
        self.assertEqual(dates_with("ichiryu", 2026), expected)

    def test_tensha(self):
        expected = md(2026, {3: [5], 5: [4, 20], 7: [19], 10: [1], 12: [16]})
        self.assertEqual(dates_with("tensha", 2026), expected)

    def test_fujoju(self):
        expected = md(2026, {1: [1, 9, 17, 24], 2: [1, 9, 19, 27], 3: [7, 15, 20, 28],
                             4: [5, 13, 17, 25], 5: [3, 11, 20, 28], 6: [5, 13, 19, 27],
                             7: [5, 13, 19, 27], 8: [4, 12, 15, 23, 31], 9: [8, 12, 20, 28],
                             10: [6, 11, 19, 27], 11: [4, 12, 20, 28], 12: [6, 13, 21, 29]})
        self.assertEqual(dates_with("fujoju", 2026), expected)

    def test_sanrinbo(self):
        expected = md(2026, {1: [4, 8, 20], 2: [1, 6, 18], 3: [2, 5, 17, 29], 4: [14, 26],
                             5: [13, 25], 6: [9, 21], 7: [3, 7, 19, 31], 8: [17, 29],
                             9: [13, 25], 10: [7, 11, 23], 11: [4, 9, 21], 12: [3, 18, 30]})
        self.assertEqual(dates_with("sanrinbo", 2026), expected)

    def test_bosou(self):
        expected = md(2026, {1: [7, 8, 19, 20, 31], 2: [1, 6, 7, 18, 19],
                             3: [2, 3, 14, 15, 26, 27], 4: [13, 14, 25, 26],
                             5: [5, 16, 17, 28, 29], 6: [9, 10, 21, 22],
                             7: [3, 4, 7, 18, 19, 30, 31],
                             8: [7, 10, 13, 16, 19, 22, 25, 28, 31],
                             9: [3, 6, 9, 12, 15, 18, 21, 24, 27, 30],
                             10: [3, 6, 10, 11, 22, 23], 11: [3, 4, 7, 18, 19, 30],
                             12: [1, 12, 13, 24, 25]})
        self.assertEqual(dates_with("bosou", 2026), expected)

    def test_tenon_count_and_samples(self):
        tenon = dates_with("tenon", 2026)
        self.assertEqual(len(tenon), 91)
        for d in md(2026, {1: [5, 6, 7, 8, 9], 2: [4, 8, 19, 23], 12: [16, 20, 31]}):
            self.assertIn(d, tenon)

    def test_daimyo_count_and_january(self):
        daimyo = dates_with("daimyo", 2026)
        self.assertEqual(len(daimyo), 152)
        self.assertEqual([d for d in daimyo if d.month == 1],
                         md(2026, {1: [3, 5, 8, 10, 13, 18, 21, 28, 30, 31]}))

    def test_rokuyo_taian_sep_dec(self):
        expected = md(2026, {9: [4, 10, 14, 20, 26], 10: [2, 8, 13, 19, 25, 31],
                             11: [6, 10, 16, 22, 28], 12: [4, 9, 15, 21, 27]})
        taian = [d.date for d in KOYOMI.days(date(2026, 9, 1), date(2026, 12, 31))
                 if d.rokuyo_name == "大安"]
        self.assertEqual(taian, expected)

    def test_tensha_and_saikyo_2027(self):
        tensha = dates_with("tensha", 2027)
        self.assertEqual(tensha, md(2027, {2: [28], 4: [29], 5: [15], 7: [14], 9: [26], 12: [11]}))
        ichiryu = set(dates_with("ichiryu", 2027))
        self.assertEqual([d for d in tensha if d in ichiryu], md(2027, {7: [14], 9: [26], 12: [11]}))

    def test_tora_mi_sep_dec(self):
        days = KOYOMI.days(date(2026, 9, 1), date(2026, 12, 31))
        self.assertEqual([d.date for d in days if "tora" in d.marks],
                         md(2026, {9: [1, 13, 25], 10: [7, 19, 31], 11: [12, 24], 12: [6, 18, 30]}))
        self.assertEqual([d.date for d in days if "tsuchinotomi" in d.marks],
                         md(2026, {10: [22], 12: [21]}))
        self.assertEqual([d.date for d in days if "mi" in d.marks and "tsuchinotomi" not in d.marks],
                         md(2026, {9: [4, 16, 28], 10: [10], 11: [3, 15, 27], 12: [9]}))


if __name__ == "__main__":
    unittest.main()
