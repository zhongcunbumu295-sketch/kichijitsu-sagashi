"""国立天文台「暦要項」から検証用データを取得して tests/naoj_reference.json を作る。

暦要項は毎年2月に翌年分が発表される。新しい年を検証対象に加えるときに実行する:
    python tests/fetch_naoj.py 2025 2026 2027 2028
"""
import html
import json
import re
import sys
import urllib.request
from pathlib import Path

BASE = "https://eco.mtk.nao.ac.jp/koyomi/yoko/{y}/rekiyou{yy}{n}.html"
OUT = Path(__file__).with_name("naoj_reference.json")


def fetch_lines(year: int, n: int) -> list[str]:
    url = BASE.format(y=year, yy=str(year)[2:], n=n)
    with urllib.request.urlopen(url, timeout=30) as res:
        text = res.read().decode("cp932", errors="replace")
    text = re.sub(r"(?s)<script.*?</script>|<style.*?</style>", "", text)
    text = re.sub(r"</(tr|p|h\d|li|caption)>", "\n", text)
    text = re.sub(r"</t[dh]>", " | ", text)
    text = html.unescape(re.sub(r"<[^>]+>", "", text))
    return [line.strip() for line in text.splitlines() if line.strip()]


def parse_year(year: int) -> dict:
    holidays = []
    for line in fetch_lines(year, 1):
        m = re.match(r"^(\S+)\s*\|\s*(\d+)月\s*(\d+)日", line)
        if m and m.group(1) != "名称":
            holidays.append([f"{year}-{int(m.group(2)):02d}-{int(m.group(3)):02d}", m.group(1)])
        for mm, dd in re.findall(r"(\d+)月\s*(\d+)日", line if "休日になる" in line else ""):
            holidays.append([f"{year}-{int(mm):02d}-{int(dd):02d}", "休日"])

    terms, zassetsu = [], []
    for line in fetch_lines(year, 2):
        m = re.match(r"^(\S+)\s*\|\s*(\d*)度?\s*\|\s*(\d+)月\s*(\d+)日\s*\|\s*(?:(\d+)時\s*(\d+)分)?", line)
        if not m:
            continue
        name, deg, mm, dd, hh, mi = m.groups()
        day = f"{year}-{int(mm):02d}-{int(dd):02d}"
        time = f"{int(hh):02d}:{int(mi):02d}" if hh else None
        if deg and name not in ("土用", "入梅", "半夏生"):
            terms.append([name, int(deg), f"{day} {time}"])
        else:
            zassetsu.append([name, day, time])

    phases = []
    for line in fetch_lines(year, 3):
        m = re.match(r"^(朔|上弦|望|下弦)\s*\|\s*(\d+)月\s*(\d+)日\s*\|\s*(\d+)時\s*(\d+)分", line)
        if m:
            p, mm, dd, hh, mi = m.groups()
            phases.append([p, f"{year}-{int(mm):02d}-{int(dd):02d} {int(hh):02d}:{int(mi):02d}"])

    return {"holidays": holidays, "solar_terms": terms, "zassetsu": zassetsu, "moon_phases": phases}


def main() -> None:
    years = [int(a) for a in sys.argv[1:]] or [2025, 2026, 2027]
    data = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    for y in years:
        data[str(y)] = parse_year(y)
        d = data[str(y)]
        print(y, "祝日", len(d["holidays"]), "節気", len(d["solar_terms"]),
              "雑節", len(d["zassetsu"]), "月相", len(d["moon_phases"]))
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
