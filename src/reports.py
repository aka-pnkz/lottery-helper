from __future__ import annotations

from datetime import datetime
from typing import Any

import io
import json
import zipfile

import pandas as pd


def make_zip_bytes(files: list[tuple[str, bytes]]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name, data in files:
            zf.writestr(name, data)
    return buf.getvalue()


def _html_table(df: pd.DataFrame, max_rows: int = 200) -> str:
    if df is None or df.empty:
        return "<p><em>Sem dados.</em></p>"
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

    summary_html = "".join([f"<li><b>{k}:</b> {v}</li>" for k, v in summary.items()]) if summary else "<li><em>Sem dados.</em></li>"

    tables_html = []
    for name, df in tables:
        tables_html.append(f"<h3>{name}</h3>")
        tables_html.append(_html_table(df))

    html = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
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
<small>Gerado em {ts.isoformat(sep=" ", timespec="seconds")}</small>

<h3>Resumo</h3>
<ul>{summary_html}</ul>

{''.join(tables_html)}
</body>
</html>
"""
    return html.encode("utf-8")


def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    if df is None:
        df = pd.DataFrame()
    # UTF-8 com BOM (mais “Excel-friendly”)
    return df.to_csv(index=False).encode("utf-8-sig")


def df_to_md_bytes(title: str, dfs: list[tuple[str, pd.DataFrame]], max_rows: int = 200) -> bytes:
    """
    Observação: DataFrame.to_markdown depende de tabulate instalado.
    """
    out = [f"# {title}", ""]
    for section, df in dfs:
        out.append(f"## {section}")
        out.append("")
        if df is None or df.empty:
            out.append("*Sem dados.*")
            out.append("")
        else:
            view = df.head(max_rows)
            out.append(view.to_markdown(index=False, tablefmt="pipe"))
            out.append("")
    return "\n".join(out).encode("utf-8")


def df_to_json_bytes(df: pd.DataFrame, orient: str = "records") -> bytes:
    if df is None:
        payload: Any = []
        return json.dumps(payload, ensure_ascii=False).encode("utf-8")
    return df.to_json(orient=orient, force_ascii=False).encode("utf-8")
