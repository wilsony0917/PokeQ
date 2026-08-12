from pathlib import Path

import pandas as pd
import streamlit as st

TYPE_ORDER = [
    "一般", "火", "水", "電", "草", "冰",
    "格鬥", "毒", "地面", "飛行", "超能", "蟲",
    "岩石", "幽靈", "龍", "惡", "鋼", "妖精",
]

TYPE_COLORS = {
    "一般": "#A8A77A",
    "火": "#EE8130",
    "水": "#6390F0",
    "電": "#F7D02C",
    "草": "#7AC74C",
    "冰": "#96D9D6",
    "格鬥": "#C22E28",
    "毒": "#A33EA1",
    "地面": "#E2BF65",
    "飛行": "#A98FF3",
    "超能": "#F95587",
    "蟲": "#A6B91A",
    "岩石": "#B6A136",
    "幽靈": "#735797",
    "龍": "#6F35FC",
    "惡": "#705746",
    "鋼": "#B7B7CE",
    "妖精": "#D685AD",
}


@st.cache_data(show_spinner=False)
def load_all_data(data_dir):
    data_dir = Path(data_dir)

    summary = pd.read_parquet(data_dir / "summary.parquet")
    quick = pd.read_parquet(data_dir / "quick.parquet")
    main = pd.read_parquet(data_dir / "main.parquet")

    required_summary = {
        "編號", "名字", "屬性", "攻擊", "防禦", "耐力",
        "里程", "進化", "quick", "main"
    }
    required_quick = {"招名", "屬性", "傷害", "CP", "EPS", "名字"}
    required_main = {"招名", "屬性", "傷害", "名字"}

    for label, df, required in [
        ("summary", summary, required_summary),
        ("quick", quick, required_quick),
        ("main", main, required_main),
    ]:
        missing = required - set(df.columns)
        if missing:
            raise ValueError(
                f"{label}.parquet 缺少欄位：{', '.join(sorted(missing))}"
            )

    for col in ["名字", "屬性", "quick", "main"]:
        summary[col] = summary[col].fillna("").astype(str)

    for df in [quick, main]:
        for col in ["名字", "招名", "屬性"]:
            df[col] = df[col].fillna("").astype(str)

    return summary, quick, main


def apply_text_filter(df, column, selected, mode):
    if not selected:
        return df

    series = df[column].fillna("").astype(str)

    checks = pd.concat(
        [
            series.str.split(",").apply(
                lambda values, target=t: target in [v.strip() for v in values]
            )
            for t in selected
        ],
        axis=1,
    )

    if mode == "all":
        mask = checks.all(axis=1)
    elif mode == "not":
        mask = ~checks.any(axis=1)
    else:
        mask = checks.any(axis=1)

    return df[mask]


def type_badges_html(value):
    if pd.isna(value):
        return ""

    parts = [x.strip() for x in str(value).split(",") if x.strip()]
    badges = []

    for item in parts:
        color = TYPE_COLORS.get(item, "#777777")
        badges.append(
            f'<span class="type-badge" style="background:{color};">{item}</span>'
        )

    return "".join(badges)
