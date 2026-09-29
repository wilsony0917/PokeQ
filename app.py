from pathlib import Path

import pandas as pd
import streamlit as st

from utils import TYPE_ORDER, apply_text_filter, load_all_data
from type_chart import matchup_for_types

BASE = Path(__file__).resolve().parent
VERSION = "v4.6"

st.set_page_config(page_title=f"PokeQ {VERSION}", page_icon="⚡", layout="wide")

css_path = BASE / "assets" / "style.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)

summary, quick, main = load_all_data(BASE / "data")


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def get_selected_cell(event):
    """Return (row_index, column_name) from a Streamlit dataframe selection event.

    Supports the tuple/list shape used by some Streamlit versions and the
    dict/object-like shape used by others.
    """
    try:
        cells = event.selection.cells
    except Exception:
        return None, None

    if not cells:
        return None, None

    cell = cells[0]

    # Newer/alternate shape: {"row": 0, "column": "招名"}
    if isinstance(cell, dict):
        return cell.get("row"), cell.get("column")

    # Tuple/list shape: [0, "招名"] or (0, "招名")
    if isinstance(cell, (list, tuple)) and len(cell) >= 2:
        return cell[0], cell[1]

    return None, None


def set_move_filter(move_kind, move_name):
    st.session_state.move_filter_kind = move_kind
    st.session_state.move_filter_name = str(move_name)
    st.session_state.selected_name = None
    st.rerun()


# ------------------------------------------------------------
# Session state
# ------------------------------------------------------------
if "selected_name" not in st.session_state:
    st.session_state.selected_name = None

if "move_filter_kind" not in st.session_state:
    st.session_state.move_filter_kind = None

if "move_filter_name" not in st.session_state:
    st.session_state.move_filter_name = None


# ------------------------------------------------------------
# Sidebar
# ------------------------------------------------------------
with st.sidebar:
    st.markdown(
        f'<div class="pokeq-title"><span class="pokeq-bolt">⚡</span>'
        f'<span class="pokeq-name">PokeQ</span><span class="pokeq-version">{VERSION}</span></div>'
        f'<div class="pokeq-subtitle">Pokémon GO Query</div>',
        unsafe_allow_html=True,
    )

    image_slot = st.empty()

    st.header("查詢條件")
    keyword = st.text_input("Pokémon 名稱", placeholder="例如：妙蛙種子、超夢", label_visibility="collapsed")

    st.divider()
    st.subheader("屬性")
    attr_mode = st.radio("屬性條件", ["any", "all", "not"], horizontal=True, key="attr_mode", label_visibility="collapsed")
    attr_selected = st.multiselect("選擇屬性", TYPE_ORDER, key="attr_selected", label_visibility="collapsed")

    st.divider()
    st.subheader("Quick Move")
    quick_mode = st.radio("Quick 條件", ["any", "all", "not"], horizontal=True, key="quick_mode", label_visibility="collapsed")
    quick_selected = st.multiselect("選擇 Quick Move 屬性", TYPE_ORDER, key="quick_selected", label_visibility="collapsed")

    st.divider()
    st.subheader("Main Move")
    main_mode = st.radio("Main 條件", ["any", "all", "not"], horizontal=True, key="main_mode", label_visibility="collapsed")
    main_selected = st.multiselect("選擇 Main Move 屬性", TYPE_ORDER, key="main_selected", label_visibility="collapsed")

    # Show active reverse move search and allow the user to clear it.
    if st.session_state.move_filter_name:
        st.divider()
        move_label = "Quick Move" if st.session_state.move_filter_kind == "quick" else "Main Move"
        st.caption(f"招式反查：{move_label}")
        st.markdown(f"**{st.session_state.move_filter_name}**")
        if st.button("清除招式篩選", use_container_width=True):
            st.session_state.move_filter_kind = None
            st.session_state.move_filter_name = None
            st.session_state.selected_name = None
            st.rerun()


# ------------------------------------------------------------
# Filter
# ------------------------------------------------------------
result = summary.copy()

if keyword:
    result = result[result["名字"].astype(str).str.contains(keyword, case=False, regex=False, na=False)]

result = apply_text_filter(result, "屬性", attr_selected, attr_mode)
result = apply_text_filter(result, "quick", quick_selected, quick_mode)
result = apply_text_filter(result, "main", main_selected, main_mode)

# Reverse search by clicking a move in the Quick/Main table.
move_kind = st.session_state.move_filter_kind
move_name = st.session_state.move_filter_name

if move_kind == "quick" and move_name:
    matched_names = set(
        quick.loc[quick["招名"].astype(str) == str(move_name), "名字"]
        .astype(str)
        .dropna()
        .unique()
    )
    result = result[result["名字"].astype(str).isin(matched_names)]

elif move_kind == "main" and move_name:
    matched_names = set(
        main.loc[main["招名"].astype(str) == str(move_name), "名字"]
        .astype(str)
        .dropna()
        .unique()
    )
    result = result[result["名字"].astype(str).isin(matched_names)]

display = result.copy()

if result.empty:
    selected_name = None
else:
    valid_names = set(result["名字"].astype(str))
    if st.session_state.selected_name not in valid_names:
        st.session_state.selected_name = str(result.iloc[0]["名字"])
    selected_name = st.session_state.selected_name


# ------------------------------------------------------------
# Sidebar artwork
# ------------------------------------------------------------
if selected_name is not None:
    row = result[result["名字"].astype(str) == selected_name].iloc[0]
    number = str(row.get("編號", "")).replace("#", "").strip()

    if number.isdigit():
        sprite_url = (
            "https://raw.githubusercontent.com/PokeAPI/sprites/"
            f"master/sprites/pokemon/other/official-artwork/{int(number)}.png"
        )
        with image_slot.container():
            st.image(sprite_url, width=145)


# ------------------------------------------------------------
# Main layout
# Left side = Quick + Main + Search results
# Right side = full-height type matchup
# ------------------------------------------------------------
left_area, matchup_area = st.columns([1.75, 1.0], gap="large")

with left_area:
    quick_col, main_col = st.columns(2, gap="medium")

    if selected_name is None:
        with quick_col:
            st.info("沒有符合條件的 Pokémon。")
    else:
        row = result[result["名字"].astype(str) == selected_name].iloc[0]

        with quick_col:
            st.markdown("### Quick Move")
            q = quick[quick["名字"].astype(str) == selected_name].copy()
            if q.empty:
                st.caption("無 Quick Move 資料")
            else:
                qcols = [c for c in ["招名", "屬性", "傷害", "CP", "EPS"] if c in q.columns]
                q_display = q[qcols].reset_index(drop=True)

                q_event = st.dataframe(
                    q_display,
                    width="stretch",
                    hide_index=True,
                    height=330,
                    on_select="rerun",
                    selection_mode="single-cell",
                    key=f"quick_move_table_{selected_name}",
                )

                q_row, q_col = get_selected_cell(q_event)
                if q_row is not None and q_col == "招名":
                    try:
                        q_row = int(q_row)
                        if 0 <= q_row < len(q_display):
                            clicked_move = str(q_display.iloc[q_row]["招名"])
                            if not (
                                st.session_state.move_filter_kind == "quick"
                                and st.session_state.move_filter_name == clicked_move
                            ):
                                set_move_filter("quick", clicked_move)
                    except (TypeError, ValueError):
                        pass

        with main_col:
            st.markdown("### Main Move")
            m = main[main["名字"].astype(str) == selected_name].copy()
            if m.empty:
                st.caption("無 Main Move 資料")
            else:
                mcols = [c for c in ["招名", "屬性", "傷害"] if c in m.columns]
                m_display = m[mcols].reset_index(drop=True)

                m_event = st.dataframe(
                    m_display,
                    width="stretch",
                    hide_index=True,
                    height=330,
                    on_select="rerun",
                    selection_mode="single-cell",
                    key=f"main_move_table_{selected_name}",
                )

                m_row, m_col = get_selected_cell(m_event)
                if m_row is not None and m_col == "招名":
                    try:
                        m_row = int(m_row)
                        if 0 <= m_row < len(m_display):
                            clicked_move = str(m_display.iloc[m_row]["招名"])
                            if not (
                                st.session_state.move_filter_kind == "main"
                                and st.session_state.move_filter_name == clicked_move
                            ):
                                set_move_filter("main", clicked_move)
                    except (TypeError, ValueError):
                        pass

    st.markdown('<div class="search-gap"></div>', unsafe_allow_html=True)

    if move_name:
        move_label = "Quick Move" if move_kind == "quick" else "Main Move"
        st.subheader(f"搜尋結果 · {len(result)} · {move_label}: {move_name}")
    else:
        st.subheader(f"搜尋結果 · {len(result)}")

    # quick/main intentionally removed from the search-result table.
    show_cols = [
        c for c in ["編號", "名字", "屬性", "攻擊", "防禦", "耐力", "里程", "進化"]
        if c in display.columns
    ]

    event = st.dataframe(
        display[show_cols],
        width="stretch",
        hide_index=True,
        height=650,
        on_select="rerun",
        selection_mode="single-cell",
        key="pokemon_table",
    )

    selected_cells = event.selection.cells
    if selected_cells:
        p_row, _ = get_selected_cell(event)
        try:
            p_row = int(p_row)
            if 0 <= p_row < len(display):
                clicked_name = str(display.iloc[p_row]["名字"])
                if clicked_name != st.session_state.selected_name:
                    # Selecting another Pokémon exits move reverse-search mode.
                    # This also prevents the previous move-cell selection from
                    # being interpreted as a click on the new Pokémon's move table.
                    st.session_state.move_filter_kind = None
                    st.session_state.move_filter_name = None
                    st.session_state.selected_name = clicked_name
                    st.rerun()
        except (TypeError, ValueError):
            pass

with matchup_area:
    st.markdown("### 屬性相剋")

    if selected_name is None:
        st.caption("無法計算屬性相剋")
    else:
        row = result[result["名字"].astype(str) == selected_name].iloc[0]
        attrs = [x.strip() for x in str(row.get("屬性", "")).split(",") if x.strip()]
        matchup = matchup_for_types(attrs)

        if matchup.empty:
            st.caption("無法計算屬性相剋")
        else:
            # Tall enough to show all 18 types without vertical scrolling.
            st.dataframe(matchup, width="stretch", hide_index=True, height=705)

st.caption("Data source: data/summary.parquet, data/quick.parquet, data/main.parquet")
