import pandas as pd

TYPE_ORDER = [
    "一般", "火", "水", "電", "草", "冰",
    "格鬥", "毒", "地面", "飛行", "超能", "蟲",
    "岩石", "幽靈", "龍", "惡", "鋼", "妖精",
]

_RAW = [
    "111111111111231121",
    "122100111110212101",
    "102121110111012111",
    "110221113011112111",
    "120121120212012121",
    "122102110011110121",
    "011110121222031002",
    "111101122111221130",
    "101021101312011101",
    "111201011110211121",
    "111111001121111321",
    "121101221201121022",
    "101110212010111121",
    "311111111101101211",
    "111111111111110123",
    "111111211101101212",
    "122210111111011120",
    "121111021111110021",
]


def type_table():
    grid = [list(row) for row in _RAW]
    df = pd.DataFrame(grid, index=TYPE_ORDER, columns=TYPE_ORDER).astype(int)
    return pow(0.625, (df - 1))


_TABLE = type_table()


def matchup_for_types(types):
    types = [t for t in types if t in _TABLE.index]
    if not types:
        return pd.DataFrame()

    attack = _TABLE.loc[types].T.prod(axis=1).round(2)
    defense = _TABLE[types].prod(axis=1).round(2)

    out = pd.concat([attack, defense], axis=1)
    out.columns = ["攻擊倍數", "受傷倍數"]
    out.index.name = "屬性"

    return out.reset_index()
