"""暦注の表示情報と、目的別の吉日スコア。

スコアは「一般的な言い伝え」をもとにした目安。ここを書き換えるとサイトと検索ツールの両方に反映される。
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .calendar import DayInfo


@dataclass(frozen=True)
class Mark:
    key: str
    name: str
    reading: str
    short: str          # カレンダーのマス用の短い表記
    kind: str           # good / bad
    summary: str
    slug: str | None    # 解説ページ（/koyomi/<slug>/）


MARKS: dict[str, Mark] = {m.key: m for m in [
    Mark("tensha", "天赦日", "てんしゃにち", "天赦", "good",
         "暦の上で最上の大吉日。年に5〜7回しかない特別な日", "tenshanichi"),
    Mark("ichiryu", "一粒万倍日", "いちりゅうまんばいび", "万倍", "good",
         "一粒の籾が万倍に実るように、始めたことが大きく育つ日", "ichiryumanbaibi"),
    Mark("tora", "寅の日", "とらのひ", "寅", "good",
         "出ていったお金が戻ってくるとされる金運の日。旅行にも吉", "toranohi"),
    Mark("mi", "巳の日", "みのひ", "巳", "good",
         "弁財天の縁日。金運・財運や芸事の上達にご利益があるとされる", "minohi"),
    Mark("tsuchinotomi", "己巳の日", "つちのとみのひ", "己巳", "good",
         "60日に一度の特別な巳の日。弁財天のご利益が特に強いとされる", "minohi"),
    Mark("kinoene", "甲子の日", "きのえねのひ", "甲子", "good",
         "干支の始まりの日。新しいことを始めるのに良い。大黒天の縁日", "kinoenenohi"),
    Mark("tenon", "天恩日", "てんおんにち", "天恩", "good",
         "天の恩恵を受けられる日。お祝い事に吉", "tenonnichi"),
    Mark("daimyo", "大明日", "だいみょうにち", "大明", "good",
         "太陽の光が隅々まで照らす日。建築・移転・旅行に吉", "daimyonichi"),
    Mark("bosou", "母倉日", "ぼそうにち", "母倉", "good",
         "母が子を慈しむように天が人を慈しむ日。特に婚姻に吉", "bosounichi"),
    Mark("fujoju", "不成就日", "ふじょうじゅび", "不成就", "bad",
         "何事も成就しないとされる日。新しいことや願い事は避ける", "fujojubi"),
    Mark("sanrinbo", "三隣亡", "さんりんぼう", "三隣亡", "bad",
         "建築の大凶日。棟上げや地鎮祭は避けるのが一般的", "sanrinbo"),
]}

# 表示順（良い日 → 注意したい日）
MARK_ORDER = ["tensha", "ichiryu", "tora", "mi", "tsuchinotomi", "kinoene",
              "tenon", "daimyo", "bosou", "fujoju", "sanrinbo"]
# 「開運日」としてまとめて扱う主要な吉日
KAIUN_KEYS = ["tensha", "ichiryu", "tora", "mi", "tsuchinotomi", "kinoene"]

ROKUYO_KEYS = {"大安": "taian", "赤口": "shakku", "先勝": "sensho",
               "友引": "tomobiki", "先負": "senbu", "仏滅": "butsumetsu"}
ROKUYO_INFO = {
    "大安": ("たいあん", "終日吉。何をするにも良い日とされる"),
    "友引": ("ともびき", "朝と夕方は吉、昼は凶。お祝い事に良く、葬儀は避ける"),
    "先勝": ("せんしょう", "午前は吉、午後は凶。急ぎの用事や訴訟に良い"),
    "先負": ("せんぶ", "午前は凶、午後は吉。勝負事や急用は避けて静かに過ごす"),
    "赤口": ("しゃっこう", "正午（11時〜13時ごろ）だけ吉で、ほかは凶"),
    "仏滅": ("ぶつめつ", "六曜の中で最も凶とされる日"),
}


@dataclass(frozen=True)
class Purpose:
    key: str
    name: str            # 例: 財布を買う・使い始める
    short: str           # 例: 財布
    title_word: str      # ページタイトル用（例: 財布を買う日・使い始める日）
    weights: dict[str, int]
    reasons: dict[str, str]
    tips: list[str] = field(default_factory=list)
    products: list[str] = field(default_factory=list)   # アフィリエイトの検索キーワード
    rest_day_default: bool = False


PURPOSES: list[Purpose] = [
    Purpose(
        "saifu", "財布を買う・使い始める", "財布", "財布を買う日・使い始める日",
        {"tensha": 5, "ichiryu": 4, "tora": 4, "mi": 3, "tsuchinotomi": 3, "kinoene": 2,
         "taian": 2, "tenon": 1, "daimyo": 1, "fujoju": -5, "butsumetsu": -2, "shakku": -1},
        {"tora": "出ていったお金が戻ってくる", "ichiryu": "入ったお金が万倍に増える",
         "mi": "弁財天の金運のご利益", "tsuchinotomi": "巳の日よりさらに強い金運",
         "tensha": "最上の吉日", "fujoju": "何事も成就しない"},
        ["購入日と使い始める日は別でもかまいません。吉日に買って、別の吉日に使い始める人も多くいます。",
         "春に買う財布は「張る（春）財布」と呼ばれ、お金でふくらむ縁起物として人気です。",
         "新しい財布には、使い始める前にお札を多めに入れて一晩置くと良い、という言い伝えもあります。"],
        ["開運 財布 長財布", "ミニ財布 本革"],
    ),
    Purpose(
        "takarakuji", "宝くじを買う", "宝くじ", "宝くじを買う日",
        {"tensha": 5, "ichiryu": 4, "tora": 3, "mi": 3, "tsuchinotomi": 3, "kinoene": 3,
         "taian": 2, "tenon": 1, "fujoju": -5, "butsumetsu": -1},
        {"ichiryu": "一粒が万倍になる", "tora": "使ったお金が戻ってくる",
         "mi": "弁財天の金運", "kinoene": "大黒天の縁日", "fujoju": "願いが成就しない"},
        ["ジャンボ宝くじは発売期間が決まっています。期間内の吉日を探すときは、検索ツールで期間を絞り込むと便利です。",
         "宝くじはあくまで運試し。買いすぎないよう、予算を決めて楽しみましょう。"],
        ["宝くじ 入れ 金運"],
    ),
    Purpose(
        "nyuseki", "入籍・結婚式", "入籍", "入籍・結婚式におすすめの日",
        {"tensha": 5, "taian": 5, "ichiryu": 3, "tenon": 3, "bosou": 3, "daimyo": 2,
         "tomobiki": 2, "sensho": 1, "tora": -3, "butsumetsu": -4, "shakku": -3, "fujoju": -5},
        {"taian": "終日吉で結婚式の定番", "bosou": "婚姻に特に良いとされる",
         "ichiryu": "幸せが万倍に広がる", "tomobiki": "幸せを友に分ける",
         "tora": "「出戻る」に通じるため避ける人が多い", "butsumetsu": "六曜で最も凶"},
        ["友引は「幸せのおすそ分け」として結婚式に人気があります（葬儀は避ける日）。",
         "寅の日は「出戻る」に通じるとして、入籍や結婚式を避ける人が多い日です。",
         "婚姻届は24時間受け付けている役所もあります。事前に窓口の時間を確認しておくと安心です。"],
        ["結婚指輪", "婚姻届 おしゃれ"],
        rest_day_default=True,
    ),
    Purpose(
        "hikkoshi", "引っ越し・入居", "引っ越し", "引っ越しに良い日",
        {"taian": 4, "tensha": 4, "daimyo": 3, "ichiryu": 2, "tenon": 2, "bosou": 1,
         "sensho": 1, "tomobiki": 1, "butsumetsu": -3, "shakku": -3, "sanrinbo": -2, "fujoju": -3},
        {"daimyo": "移転・旅立ちに良いとされる", "taian": "終日吉",
         "sanrinbo": "建築の凶日で、引っ越しも避ける人がいる", "shakku": "火の元に注意とされる日"},
        ["先勝の日は午前中、先負の日は午後に荷物を運び込むと良いとされます。",
         "吉日の土日は引っ越し料金が高くなりがちです。平日の吉日を選ぶと費用を抑えやすくなります。"],
        ["引っ越し 段ボール", "引越し 挨拶 ギフト"],
    ),
    Purpose(
        "nousha", "納車・車の購入", "納車", "納車に良い日",
        {"taian": 4, "tensha": 4, "ichiryu": 2, "tora": 2, "daimyo": 2, "sensho": 1,
         "tomobiki": 1, "butsumetsu": -3, "shakku": -3, "fujoju": -3},
        {"tora": "千里を行って千里を帰る＝無事に帰ってくる", "taian": "終日吉",
         "shakku": "「赤」が火や血を連想させる"},
        ["赤口は火や血を連想させるため、車に関することは避ける人が多い日です。",
         "納車の日にお守りを用意したり、交通安全の祈祷を受けたりする人もいます。"],
        ["交通安全 お守り 車", "ドライブレコーダー"],
    ),
    Purpose(
        "kaigyo", "開業・開店・新しいことを始める", "開業", "開業・開店・起業に良い日",
        {"tensha": 5, "ichiryu": 5, "taian": 3, "kinoene": 3, "tenon": 2, "daimyo": 1,
         "tora": 1, "fujoju": -5, "butsumetsu": -2, "shakku": -2},
        {"ichiryu": "始めたことが大きく育つ", "kinoene": "干支の始まりで物事のスタートに良い",
         "tensha": "最上の吉日", "fujoju": "何事も成就しない"},
        ["開業届の提出日、オープン日、サービス公開日など「始まり」の日を吉日に合わせると、気持ちよくスタートできます。",
         "習い事やダイエット、貯金など、個人の新しい挑戦を始める日にもおすすめです。"],
        ["開運 印鑑 法人", "名刺入れ 本革"],
    ),
    Purpose(
        "keiyaku", "契約・印鑑登録・申し込み", "契約", "契約・印鑑登録に良い日",
        {"tensha": 5, "taian": 4, "ichiryu": 3, "tenon": 2, "daimyo": 1, "kinoene": 1,
         "fujoju": -5, "butsumetsu": -2, "shakku": -2},
        {"taian": "終日吉", "ichiryu": "物事が大きく実る", "fujoju": "物事がまとまらない"},
        ["住宅ローンなど「お金を借りる」契約は、一粒万倍日を避けたほうが良いという考え方もあります（借金が万倍になるため）。",
         "実印を作るなら、彫り上がりを受け取る日や印鑑登録の日を吉日に合わせる人もいます。"],
        ["実印 開運", "印鑑ケース"],
    ),
    Purpose(
        "sanpai", "神社参拝・金運祈願", "参拝", "神社参拝・金運祈願に良い日",
        {"tensha": 4, "tsuchinotomi": 4, "mi": 3, "tora": 3, "kinoene": 3, "ichiryu": 2,
         "taian": 1, "tenon": 1, "fujoju": -1},
        {"mi": "弁財天の縁日", "tsuchinotomi": "弁財天のご利益が特に強い",
         "tora": "毘沙門天の縁日", "kinoene": "大黒天の縁日"},
        ["巳の日・己巳の日は弁財天、寅の日は毘沙門天、甲子の日は大黒天と、日によってご縁のある神仏が違います。",
         "縁日には特別なお守りや御朱印を授与する寺社もあります。事前に確認してから出かけましょう。"],
        ["御朱印帳", "お守り袋"],
    ),
    Purpose(
        "ryoko", "旅行・出発", "旅行", "旅行・出発に良い日",
        {"tora": 4, "daimyo": 3, "tensha": 3, "taian": 2, "ichiryu": 1, "sensho": 1,
         "butsumetsu": -1, "shakku": -1, "fujoju": -2},
        {"tora": "千里を行って千里を帰る", "daimyo": "旅立ちに良いとされる"},
        ["寅の日は「千里を行って千里を帰る」虎にちなみ、旅行の出発日に良いとされています。"],
        ["スーツケース 軽量", "トラベル ポーチ"],
    ),
    Purpose(
        "kenchiku", "地鎮祭・上棟式・家づくり", "家づくり", "地鎮祭・上棟式に良い日",
        {"taian": 4, "tensha": 4, "daimyo": 3, "ichiryu": 2, "tenon": 1, "sensho": 1,
         "sanrinbo": -6, "fujoju": -4, "butsumetsu": -3, "shakku": -3, "doyo": -2},
        {"daimyo": "建築に良いとされる", "sanrinbo": "建築の大凶日",
         "doyo": "土を動かす作業を避ける期間"},
        ["三隣亡は「三軒隣まで亡ぼす」といわれ、建築関係では特に避けられる日です。",
         "土用の期間は土を動かす作業（地鎮祭・基礎工事の着工など）を避ける習わしがあります。",
         "日取りは施工会社や神社と相談して決めるのが一般的です。候補日をいくつか出しておくとスムーズです。"],
        ["地鎮祭 お供え", "上棟式 ご祝儀袋"],
    ),
]
PURPOSE_BY_KEY = {p.key: p for p in PURPOSES}


# 天赦日は凶日を打ち消す大吉日とされるため、六曜の凶（仏滅・赤口）は減点しない
TENSHA_CANCELS = {"butsumetsu", "shakku"}


def day_keys(day: DayInfo) -> list[str]:
    """スコア計算に使うキー（暦注 + 六曜 + 土用）。"""
    keys = list(day.marks) + [ROKUYO_KEYS[day.rokuyo_name]]
    if day.doyo:
        keys.append("doyo")
    return keys


def score(day: DayInfo, purpose: Purpose) -> int:
    keys = day_keys(day)
    if "tensha" in keys:
        keys = [k for k in keys if k not in TENSHA_CANCELS]
    return sum(purpose.weights.get(k, 0) for k in keys)


def rank_label(value: int) -> tuple[str, str]:
    """スコア → (記号, 説明)。"""
    if value >= 8:
        return "◎", "最良"
    if value >= 5:
        return "○", "良い"
    if value >= 2:
        return "△", "まずまず"
    if value <= -3:
        return "✕", "避けたい"
    return "－", "普通"


def is_saikyo(day: DayInfo) -> bool:
    """最強開運日: 天赦日と一粒万倍日が重なる日。"""
    return "tensha" in day.marks and "ichiryu" in day.marks


def kaiun_overlap(day: DayInfo) -> list[str]:
    """その日に重なっている主要な吉日の名前（大安を含む）。"""
    names = [MARKS[k].name for k in KAIUN_KEYS if k in day.marks]
    if "tsuchinotomi" in day.marks and "巳の日" in names:
        names.remove("巳の日")
    if day.rokuyo_name == "大安":
        names.append("大安")
    return names
