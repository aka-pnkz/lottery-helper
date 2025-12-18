from __future__ import annotations

from datetime import datetime
from typing import Any

import json
import pandas as pd


def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    """
    CSV em UTF-8 com BOM (utf-8-sig) para abrir bem no Excel (PT-BR).
    """
    if df is None:
        df = pd.DataFrame()
    return df.to_csv(index=False).encode("utf-8-sig")


def df_to_md_bytes(
    title: str,
    dfs: list[tuple[str, pd.DataFrame]],
    *,
    max_rows: int = 200,
) -> bytes:
    """
    Gera um relatório em Markdown contendo múltiplas tabelas.
    Requer 'tabulate' instalado para DataFrame.to_markdown().
    """
    lines: list[str] = []
    lines.append(f"# {title}")
    lines.append("")

    for section_title, df in dfs:
        lines.append(f"## {section_title}")
        lines.append("")
        if df is None or df.empty:
            lines.append("*Sem dados.*")
            lines.append("")
            continue

        view = df.head(max_rows).copy()
        lines.append(view.to_markdown(index=False))
        lines.append("")

    return "\n".join(lines).encode("utf-8")


def df_to_json_bytes(df: pd.DataFrame) -> bytes:
    """
    JSON em UTF-8 (sem escapar acentos), no formato 'records'.
    """
    if df is None or df.empty:
        payload: list[dict[str, Any]] = []
    else:
        payload = df.to_dict(orient="records")

    return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")


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

    if summary:
        summary_html = "".join(
            [f"<tr><th>{k}</th><td>{v}</td></tr>" for k, v in summary.items()]
        )
    else:
        summary_html = "<tr><td><em>Sem dados.</em></td></tr>"

    tables_html = []
    for section_title, df in tables:
        tables_html.append(f"<h2>{section_title}</h2>")
        tables_html.append(_html_table(df))

    html = f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title}</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
      margin: 24px;
      color: #111;
    }}
    .muted {{ color: #555; }}
    table {{
      border-collapse: collapse;
      width: 100%;
      margin: 12px 0 24px 0;
      font-size: 14px;
    }}
    th, td {{
      border: 1px solid #ddd;
      padding: 8px 10px;
      text-align: left;
      vertical-align: top;
    }}
    th {{ background: #f6f6f6; }}
    code, pre {{
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
    }}
  </style>
</head>
<body>
  <h1>{title}</h1>
  <p class="muted">{subtitle}</p>
  <p class="muted">Gerado em: {ts.strftime("%Y-%m-%d %H:%M:%S")}</p>

  <h2>Resumo</h2>
  <table>
    <tbody>
      {summary_html}
    </tbody>
  </table>

  {"".join(tables_html)}
</body>
</html>
"""
    return html.encode("utf-8")
