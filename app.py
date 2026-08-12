from pathlib import Path

import pandas as pd
import streamlit as st

from utils import (
    TYPE_ORDER,
    apply_text_filter,
    load_all_data,
    type_badges_html,
)
from type_chart import matchup_for_types

BASE = Path(__file__).resolve().parent

st.set_page_config(
    page_title="PokeQ",
    page_icon="⚡",
    layout="wide",
)

css_path = BASE / "assets" / "style.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

summary, quick, main = load_all_data(BASE / "data")

st.title("⚡ PokeQ")
st.caption("Pokémon GO Query")

# -----------------------------
# Sidebar filters
# -----------------------------
with st.sidebar:
    st.header("查詢條件")

    keyword = st.text_input(
        "Pokémon 名稱",
        placeholder="例如：妙蛙種子、超夢",
    )

    st.divider()

    st.subheader("屬性")
    attr_mode = st.radio(
        "屬性條件",
        ["any", "all", "not"],
        horizontal=True,
        key="attr_mode",
    )
    attr_selected = st.multiselect(
        "選擇屬性",
        TYPE_ORDER,
        key="attr_selected",
    )

    st.divider()

    st.subheader("Quick Move")
    quick_mode = st.radio(
        "Quick 條件",
        ["any", "all", "not"],
        horizontal=True,
        key="quick_mode",
    )
    quick_selected = st.multiselect(
        "選擇 Quick Move 屬性",
        TYPE_ORDER,
        key="quick_selected",
    )

    st.divider()

    st.subheader("Main Move")
    main_mode = st.radio(
        "Main 條件",
        ["any", "all", "not"],
        horizontal=True,
        key="main_mode",
    )
    main_selected = st.multiselect(
        "選擇 Main Move 屬性",
        TYPE_ORDER,
        key="main_selected",
    )

# -----------------------------
# Apply filters
# -----------------------------
result = summary.copy()

if keyword:
    result = result[
        result["名字"].astype(str).str.contains(
            keyword,
            case=False,
            regex=False,
            na=False,
        )
    ]

result = apply_text_filter(result, "屬性", attr_selected, attr_mode)
result = apply_text_filter(result, "quick", quick_selected, quick_mode)
result = apply_text_filter(result, "main", main_selected, main_mode)

# -----------------------------
# Layout
# -----------------------------
left, right = st.columns([1.65, 1.0], gap="large")

with left:
    st.subheader(f"搜尋結果 · {len(result)}")

    sort_options = ["原始順序", "攻擊", "防禦", "耐力", "名字", "編號"]
    sort_col = st.selectbox("排序", sort_options, index=0)
    descending = st.checkbox("由大到小", value=True)

    display = result.copy()
    if sort_col != "原始順序":
        display = display.sort_values(
            sort_col,
            ascending=not descending,
            na_position="last",
        )

    show_cols = [
        c for c in
        ["編號", "名字", "屬性", "攻擊", "防禦", "耐力", "里程", "進化", "quick", "main"]
        if c in display.columns
    ]

    st.dataframe(
        display[show_cols],
        use_container_width=True,
        hide_index=True,
        height=680,
    )

with right:
    st.subheader("Pokémon 詳細資料")

    if result.empty:
        st.info("沒有符合條件的 Pokémon。")
    else:
        names = result["名字"].astype(str).tolist()
        selected_name = st.selectbox("選擇 Pokémon", names)

        row = result[result["名字"].astype(str) == selected_name].iloc[0]

        title_left, title_right = st.columns([1, 0.7])

        with title_left:
            st.markdown(f"## {selected_name}")
            st.markdown(
                type_badges_html(row.get("屬性", "")),
                unsafe_allow_html=True,
            )

        with title_right:
            number = str(row.get("編號", "")).replace("#", "").strip()
            if number.isdigit():
                sprite_url = (
                    "https://raw.githubusercontent.com/PokeAPI/sprites/"
                    f"master/sprites/pokemon/other/official-artwork/{int(number)}.png"
                )
                st.image(sprite_url, width=170)

        st.write("")

        c1, c2, c3 = st.columns(3)
        c1.metric("攻擊", int(row["攻擊"]) if pd.notna(row.get("攻擊")) else "-")
        c2.metric("防禦", int(row["防禦"]) if pd.notna(row.get("防禦")) else "-")
        c3.metric("耐力", int(row["耐力"]) if pd.notna(row.get("耐力")) else "-")

        extra1, extra2 = st.columns(2)
        extra1.metric("夥伴里程", int(row["里程"]) if pd.notna(row.get("里程")) else "-")
        evo = row.get("進化")
        extra2.metric("進化糖果", int(evo) if pd.notna(evo) else "-")

        st.divider()

        st.markdown("#### Quick Move")
        q = quick[quick["名字"].astype(str) == selected_name].copy()
        if q.empty:
            st.caption("無 Quick Move 資料")
        else:
            qcols = [c for c in ["招名", "屬性", "傷害", "CP", "EPS"] if c in q.columns]
            st.dataframe(
                q[qcols],
                use_container_width=True,
                hide_index=True,
            )

        st.markdown("#### Main Move")
        m = main[main["名字"].astype(str) == selected_name].copy()
        if m.empty:
            st.caption("無 Main Move 資料")
        else:
            mcols = [c for c in ["招名", "屬性", "傷害"] if c in m.columns]
            st.dataframe(
                m[mcols],
                use_container_width=True,
                hide_index=True,
            )

        st.divider()
        st.markdown("#### 屬性相剋")

        attrs = [
            x.strip()
            for x in str(row.get("屬性", "")).split(",")
            if x.strip()
        ]

        matchup = matchup_for_types(attrs)
        if matchup.empty:
            st.caption("無法計算屬性相剋")
        else:
            st.dataframe(
                matchup,
                use_container_width=True,
                hide_index=True,
            )

st.caption("Data source: data/summary.parquet, data/quick.parquet, data/main.parquet")
