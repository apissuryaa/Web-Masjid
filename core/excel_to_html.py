import pandas as pd
from pathlib import Path

LIKELY_AMOUNT_COLS = ['total', 'jumlah', 'debit', 'kredit', 'saldo', 'nominal', 'amount', 'nilai']

def list_sheets(xlsx_path: Path):
    xl = pd.ExcelFile(xlsx_path)
    return xl.sheet_names

def sheet_to_html(xlsx_path: Path, sheet_name: str, thousands='.', decimal=','):
    df = pd.read_excel(xlsx_path, sheet_name=sheet_name, header=0)
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            df[col] = df[col].map(lambda x:
                f"{x:,.2f}".replace(',', '_').replace('.', decimal).replace('_', thousands)
                if pd.notna(x) else x)
    return df.to_html(classes="min-w-full text-sm border border-gray-200",
                      index=False, escape=False, na_rep="", border=0)

def quick_summary(xlsx_path: Path, sheet_name: str):
    """Coba cari kolom jumlah/nominal & hitung total; fallback: total semua kolom numerik."""
    df = pd.read_excel(xlsx_path, sheet_name=sheet_name, header=0)
    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    if not numeric_cols:
        return None
    # cari kolom yang namanya mirip jumlah
    pick = None
    low = [c.lower() for c in df.columns]
    for key in LIKELY_AMOUNT_COLS:
        for idx, col in enumerate(low):
            if key in col and df.columns[idx] in numeric_cols:
                pick = df.columns[idx]; break
        if pick: break
    if pick is None:
        # fallback: sum semua numeric, gabung sebagai "Total Numerik"
        total = float(df[numeric_cols].sum(numeric_only=True).sum())
        return {'label': 'Total Numerik', 'value': total}
    else:
        total = float(df[pick].sum(numeric_only=True))
        return {'label': f"Total {pick}", 'value': total}
