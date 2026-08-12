import os
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="PokeQ",
    page_icon="⚡",
    layout="wide",
)

# -----------------------------
# Basic settings
# -----------------------------
DATA_FILE = "pokemon_info.xlsx"

TYPE_COLORS = {
    "一": "#A8A77A", "一般": "#A8A77A",
    "火": "#EE8130", "水": "#6390F0", "電": "#F7D02C",
    "草": "#7AC74C", "冰": "#96D9D6", "格": "#C22E28",
    "格鬥": "#C22E28", "毒": "#A33EA1", "地": "#E2BF65",
    "地面": "#E2BF65", "飛": "#A98FF3", "飛行": "#A98FF3",
    "超": "#F95587", "超能": "#F95587", "蟲": "#A6B91A",
    "岩": "#B6A136", "岩石": "#B6A136", "幽": "#735797",
    "幽靈": "#735797", "龍": "#6F35FC", "惡": "#705746",
    "鋼": "#B7B7CE", "精": "#D685AD", "妖精": "#D685AD",
}

TYPE_NAMES = ["一", "火", "水", "電", "草", "冰", "格", "毒", "地",
              "飛", "超", "蟲", "岩", "幽", "龍", "惡", "鋼", "精"]


def type_badge(t):
    if pd.isna(t) or str(t).strip() == "":
        return ""
    t = str(t).strip()
    c = TYPE_COLORS.get(t, "#777777")
    return (
        f'<span style="display:inline-block;background:{c};color:white;'
        f'padding:4px 10px;border-radius:14px;margin-right:6px;'
        f'font-weight:700">{t}</span>'
    )


def split_types(value):
    if pd.isna(value):
        return []
    return [x.strip() for x in str(value).replace("、", ",").split(",") if x.strip()]


@st.cache_data
def load_data(path):
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"找不到 {path}。請確認 app.py 與 pokemon_info.xlsx 位於同一個 GitHub repository 根目錄。"
        )

    xls = pd.ExcelFile(path)

    if "全列表" not in xls.sheet_names:
        raise ValueError(
            "pokemon_info.xlsx 找不到「全列表」工作表。"
            f"目前工作表：{', '.join(xls.sheet_names)}"
        )

    df = pd.read_excel(path, sheet_name="全列表")
    df.columns = [str(c).strip() for c in df.columns]

    # Clean strings
    for c in ["#", "V", "Name", "屬性1", "屬性2", "專剋", "弱點"]:
        if c in df.columns:
            df[c] = df[c].fillna("").astype(str).str.strip()

    # Numeric columns
    for c in ["耐力", "攻擊", "防守", "平均", "Max_CP", "Qty", "Qty.1"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    # Optional matchup sheet
    matchup = None
    if "攻守" in xls.sheet_names:
        matchup = pd.read_excel(path, sheet_name="攻守", header=None)

    return df, matchup


def mode_filter(series, selected, mode):
    """Filter comma-separated text fields with Any / All / Not."""
    if not selected:
        return pd.Series(True, index=series.index)

    values = series.fillna("").astype(str)

    checks = pd.concat(
        [values.apply(lambda s, x=x: x in split_types(s)) for x in selected],
        axis=1,
    )

    if mode == "All":
        return checks.all(axis=1)
    if mode == "Not":
        return ~checks.any(axis=1)
    return checks.any(axis=1)


def type_filter(df, selected, mode):
    if not selected:
        return pd.Series(True, index=df.index)

    checks = []
    for t in selected:
        checks.append((df["屬性1"] == t) | (df["屬性2"] == t))

    checks = pd.concat(checks, axis=1)

    if mode == "All":
        return checks.all(axis=1)
    if mode == "Not":
        return ~checks.any(axis=1)
    return checks.any(axis=1)


# -----------------------------
# Load workbook
# -----------------------------
try:
    df, matchup = load_data(DATA_FILE)
except Exception as e:
    st.error("資料載入失敗")
    st.exception(e)
    st.stop()


# -----------------------------
# Header
# -----------------------------
st.title("⚡ PokeQ")
st.caption("Pokémon GO Query")

# -----------------------------
# Sidebar filters
# -----------------------------
with st.sidebar:
    st.header("查詢條件")

    keyword = st.text_input(
        "Pokémon 名稱",
        placeholder="例如：超夢、洛奇亞",
    )

    st.divider()

    st.subheader("屬性")
    type_mode = st.radio(
        "屬性條件",
        ["Any", "All", "Not"],
        horizontal=True,
        key="type_mode",
    )
    selected_types = st.multiselect(
        "選擇屬性",
        TYPE_NAMES,
    )

    st.divider()

    st.subheader("專剋")
    atk_mode = st.radio(
        "專剋條件",
        ["Any", "All", "Not"],
        horizontal=True,
        key="atk_mode",
    )
    selected_attack = st.multiselect(
        "選擇可剋屬性",
        TYPE_NAMES,
        key="attack_types",
    )

    st.divider()

    st.subheader("弱點")
    weak_mode = st.radio(
        "弱點條件",
        ["Any", "All", "Not"],
        horizontal=True,
        key="weak_mode",
    )
    selected_weak = st.multiselect(
        "選擇弱點",
        TYPE_NAMES,
        key="weak_types",
    )

    st.divider()

    max_cp_min = int(df["Max_CP"].min()) if "Max_CP" in df and df["Max_CP"].notna().any() else 0
    max_cp_max = int(df["Max_CP"].max()) if "Max_CP" in df and df["Max_CP"].notna().any() else 6000

    cp_range = st.slider(
        "Max CP",
        min_value=max_cp_min,
        max_value=max_cp_max,
        value=(max_cp_min, max_cp_max),
    )

    only_v = st.checkbox("只顯示 V 標記")


# -----------------------------
# Apply filters
# -----------------------------
result = df.copy()

if keyword:
    result = result[
        result["Name"].str.contains(keyword, case=False, regex=False, na=False)
    ]

result = result[type_filter(result, selected_types, type_mode)]

if "專剋" in result.columns:
    result = result[mode_filter(result["專剋"], selected_attack, atk_mode)]

if "弱點" in result.columns:
    result = result[mode_filter(result["弱點"], selected_weak, weak_mode)]

if "Max_CP" in result.columns:
    result = result[
        result["Max_CP"].between(cp_range[0], cp_range[1], inclusive="both")
    ]

if only_v and "V" in result.columns:
    result = result[result["V"].ne("")]


# -----------------------------
# Main layout
# -----------------------------
left, right = st.columns([1.65, 1])

with left:
    st.subheader(f"搜尋結果 · {len(result)}")

    show_cols = [
        c for c in
        ["#", "V", "Name", "屬性1", "屬性2", "專剋", "弱點",
         "耐力", "攻擊", "防守", "平均", "Max_CP"]
        if c in result.columns
    ]

    display_df = result[show_cols].copy()

    sort_col = st.selectbox(
        "排序",
        ["原始順序"] + [c for c in ["Max_CP", "攻擊", "防守", "耐力", "平均", "Name"] if c in display_df.columns],
        index=0,
    )

    descending = st.checkbox("由大到小", value=True)

    if sort_col != "原始順序":
        display_df = display_df.sort_values(
            sort_col,
            ascending=not descending,
            na_position="last",
        )

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=610,
    )

with right:
    st.subheader("Pokémon 詳細資料")

    if result.empty:
        st.info("沒有符合條件的 Pokémon。")
    else:
        names = result["Name"].dropna().astype(str).tolist()
        selected_name = st.selectbox("選擇 Pokémon", names)

        row = result[result["Name"] == selected_name].iloc[0]

        st.markdown(f"## {selected_name}")

        badges = type_badge(row.get("屬性1", "")) + type_badge(row.get("屬性2", ""))
        st.markdown(badges, unsafe_allow_html=True)

        st.write("")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("攻擊", int(row["攻擊"]) if pd.notna(row.get("攻擊")) else "-")
        m2.metric("防守", int(row["防守"]) if pd.notna(row.get("防守")) else "-")
        m3.metric("耐力", int(row["耐力"]) if pd.notna(row.get("耐力")) else "-")
        m4.metric("Max CP", int(row["Max_CP"]) if pd.notna(row.get("Max_CP")) else "-")

        if pd.notna(row.get("平均")):
            st.metric("平均能力", f'{row["平均"]:.1f}')

        st.divider()

        c1, c2 = st.columns(2)

        with c1:
            st.markdown("#### ⚔️ 專剋")
            atk = split_types(row.get("專剋", ""))
            if atk:
                st.markdown("".join(type_badge(x) for x in atk), unsafe_allow_html=True)
            else:
                st.caption("—")

        with c2:
            st.markdown("#### 🛡️ 弱點")
            weak = split_types(row.get("弱點", ""))
            if weak:
                st.markdown("".join(type_badge(x) for x in weak), unsafe_allow_html=True)
            else:
                st.caption("—")

        st.divider()

        info = {}
        for c in ["#", "V", "Qty", "Qty.1"]:
            if c in row.index and str(row[c]).strip() not in ["", "nan"]:
                info[c] = row[c]

        if info:
            st.markdown("#### 基本資料")
            st.json(info, expanded=False)


st.caption("Data source: pokemon_info.xlsx in this GitHub repository")
