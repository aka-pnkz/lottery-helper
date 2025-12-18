from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd


def _html_table(df: pd.DataFrame, max_rows: int = 200) -> str:
    if df is None or df.empty:
        return "<p><i>Sem dados.</i></p>"
    view = df.head(max_rows).copy()
    return view.to_html(index=False, escape=True)


def build_html_report(
    *,
    title: str,
    subtitle: str,
    generated_at: datetime | None,
    summary: dict[str, str],
    tables: list[tuple[str, pd.DataFrame]],
) -> bytes:
    ts = generated_at or datetime.now()
    summary_html = "".join([f"<li><b>{k}:</b> {v}</li>" for k, v in summary.items()])

    tables_html = ""
    for name, df in tables:
        tables_html += f"<h3>{name}</h3>"
        tables_html += _html_table(df)

    html = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8"/>
<title>{title}</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 24px; }}
h1 {{ margin-bottom: 0; }}
h2 {{ margin-top: 6px; color: #444; font-weight: normal; }}
table {{ border-collapse: collapse; width: 100%; margin: 10px 0 24px 0; }}
th, td {{ border: 1px solid #ddd; padding: 8px; font-size: 12px; }}
th {{ background: #f4f4f4; text-align: left; }}
small {{ color: #666; }}
</style>
</head>
<body>
<h1>{title}</h1>
<h2>{subtitle}</h2>
<small>Gerado em: {ts.isoformat(sep=" ", timespec="seconds")}</small>

<h3>Resumo</h3>
<ul>{summary_html}</ul>

{tables_html}

</body></html>
"""
    return html.encode("utf-8")


def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    # UTF-8 com BOM (Excel-friendly)
    return df.to_csv(index=False).encode("utf-8-sig")


def df_to_md_bytes(title: str, dfs: list[tuple[str, pd.DataFrame]], *, max_rows: int = 200) -> bytes:
    """
    Gera um markdown simples com seções e tabelas.
    Observação: DataFrame.to_markdown depende de 'tabulate' instalado.
    """
    out = f"# {title}\n\n"
    for section, df in dfs:
        out += f"## {section}\n\n"
        if df is None or df.empty:
            out += "_Sem dados._\n\n"
        else:
            view = df.head(max_rows)
            out += view.to_markdown(index=False, tablefmt="pipe")
            out += "\n\n"
    return out.encode("utf-8")


def df_to_json_bytes(df: pd.DataFrame, *, orient: str = "records") -> bytes:
    """
    JSON em UTF-8, preservando acentos.
    """
    return df.to_json(orient=orient, force_ascii=False).encode("utf-8")
