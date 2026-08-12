# PokeQ

Pokémon GO query web app built with Streamlit.

## Project structure

```text
PokeQ/
├── app.py
├── utils.py
├── type_chart.py
├── requirements.txt
├── assets/
│   └── style.css
└── data/
    ├── summary.parquet
    ├── quick.parquet
    └── main.parquet
```

## Streamlit deployment

- Repository: `wilsony0917/PokeQ`
- Branch: `main`
- Main file path: `app.py`

The app reads only the three Parquet files under `data/`.
