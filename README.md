# PokeQ

Pokémon GO query web app built with Streamlit.

## This version

- The Pokémon table is clickable.
- Clicking a row immediately changes the selected Pokémon.
- Removed the separate Pokémon dropdown.
- Removed the extra sort dropdown and descending checkbox.
- Removed the duplicated stat cards.
- Moved the selected Pokémon name/type/artwork above the result table.
- Moved Quick Move and Main Move upward to align with the result table.

## v3.1 selection fix

The result table now uses `selection_mode="single-cell"`.
Clicking any cell in a Pokémon row immediately updates the selected Pokémon.
This removes the need to click the row-selection checkbox.
