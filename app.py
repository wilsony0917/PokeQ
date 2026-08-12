from pathlib import Path

import pandas as pd
import streamlit as st

from utils import TYPE_ORDER, apply_text_filter, load_all_data, type_badges_html
from type_chart import matchup_for_types

BASE = Path(__file__).resolve().parent

st.set_page_config(page_title="PokeQ", page_icon="⚡", layout="wide")

css_path = BASE / "assets" / "style.css"
if css_path.exists():
    st.markdown(
        f"<style>{css_path.read_text(encoding='utf-8')}</style>",
        unsafe_allow_html=True,
    )

summary, quick, main = load_all_data(BASE / "data")

st.title("⚡ PokeQ")
st.caption("Pokémon GO Query")

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

display = result.copy()

if "selected_name" not in st.session_state:
    st.session_state.selected_name = None

if result.empty:
    selected_name = None
else:
    valid_names = set(result["名字"].astype(str))
    if st.session_state.selected_name not in valid_names:
        st.session_state.selected_name = str(result.iloc[0]["名字"])
    selected_name = st.session_state.selected_name

# Selected Pokémon summary moved above the result table.
if selected_name is not None:
    row = result[result["名字"].astype(str) == selected_name].iloc[0]

    summary_left, summary_right = st.columns([4.8, 1.2], gap="small")

    with summary_left:
        st.markdown(f"## {selected_name}")
        st.markdown(
            type_badges_html(row.get("屬性", "")),
            unsafe_allow_html=True,
        )

    with summary_right:
        number = str(row.get("編號", "")).replace("#", "").strip()
        if number.isdigit():
            sprite_url = (
                "https://raw.githubusercontent.com/PokeAPI/sprites/"
                f"master/sprites/pokemon/other/official-artwork/{int(number)}.png"
            )
            st.image(sprite_url, width=150)

st.write("")

left, right = st.columns([1.65, 1.0], gap="large")

with left:
    st.subheader(f"搜尋結果 · {len(result)}")

    show_cols = [
        c for c in
        ["編號", "名字", "屬性", "攻擊", "防禦", "耐力", "里程", "進化", "quick", "main"]
        if c in display.columns
    ]

    # Click ANY CELL in the table to update the selected Pokémon immediately.
    # single-cell is used intentionally: Streamlit's single-row mode selects
    # through the checkbox at the far left, while users naturally click cells.
    event = st.dataframe(
        display[show_cols],
        width="stretch",
        hide_index=True,
        height=680,
        on_select="rerun",
        selection_mode="single-cell",
        key="pokemon_table",
    )

    selected_cells = event.selection.cells
    if selected_cells:
        # Each selected cell is (original_row_position, column_name).
        # Streamlit preserves the original row position even after browser sorting.
        pos = selected_cells[0][0]
        if 0 <= pos < len(display):
            clicked_name = str(display.iloc[pos]["名字"])
            if clicked_name != st.session_state.selected_name:
                st.session_state.selected_name = clicked_name
                st.rerun()

with right:
    # Quick/Main moved upward to align with the result table.
    if selected_name is None:
        st.info("沒有符合條件的 Pokémon。")
    else:
        st.markdown("### Quick Move")
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

        st.markdown("### Main Move")
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
        st.markdown("### 屬性相剋")

        row = result[result["名字"].astype(str) == selected_name].iloc[0]
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
