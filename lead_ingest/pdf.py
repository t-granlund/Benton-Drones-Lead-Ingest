"""PDF / HTML print rendering for completed consent forms.

render_signup_html() returns a standalone HTML print view (no deps).
try_render_pdf() attempts to use fpdf2 if installed, returning None otherwise.
"""
from __future__ import annotations

from html import escape
from typing import Any

from lead_ingest.branded_template import (
    CREAM,
    LOGO_URL,
    PRIMARY_OLIVE,
    WHITE,
)
from lead_ingest.models import CONSENT_TEXT, CONSENT_VERSION, SIGNATURE_DISCLAIMER, WAIVER_TEXT, WAIVER_VERSION


def _row_to_dict(row: Any) -> dict[str, Any]:
    if isinstance(row, dict):
        return row
    return dict(row) if row else {}


def render_signup_html(
    signup: Any,
    consent: Any | None = None,
    signature: Any | None = None,
) -> bytes:
    """Return an HTML print view styled for Benton Drones.

    Includes logo, lead details, consent text, signature info, timestamp, IP/UA.
    Optimized for browser print-to-PDF (Ctrl+P).
    """
    s = _row_to_dict(signup)
    c = _row_to_dict(consent)
    sig = _row_to_dict(signature)

    name = f"{s.get('first_name', '')} {s.get('last_name', '')}".strip()

    def row(label: str, value: str) -> str:
        return f"<tr><th>{escape(label)}</th><td>{escape(value or '-')}</td></tr>"

    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Consent Form — {escape(name)} — Benton Drones</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Jost:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {{
      --olive: {PRIMARY_OLIVE};
      --olive-dark: #6f853d;
      --olive-deep: #5a6f30;
      --md-sys-color-primary: {PRIMARY_OLIVE};
      --md-sys-color-on-primary: {WHITE};
      --md-sys-color-primary-container: #f0f7f4;
      --md-sys-color-surface: {WHITE};
      --md-sys-color-surface-container: #f5f5f0;
      --md-sys-color-surface-container-low: #fbfbf8;
      --md-sys-color-outline: #d7d3c5;
      --md-sys-color-outline-variant: #ede8d8;
      --el-1: 0 1px 2px rgba(0,0,0,0.04), 0 1px 4px rgba(0,0,0,0.06);
      --el-2: 0 2px 4px rgba(0,0,0,0.05), 0 6px 16px rgba(0,0,0,0.07);
      --md-elevation-1: var(--el-1);
      --md-elevation-2: var(--el-2);
      --cream: {CREAM};
    }}
    * {{ box-sizing: border-box; }}
    body {{
      font-family: 'Jost', sans-serif;
      font-weight: 500;
      letter-spacing: 0.02rem;
      margin: 0;
      padding: 40px;
      color: #1b1b1b;
      background: var(--md-sys-color-surface);
      line-height: 1.65;
      font-size: 1.05rem;
      -webkit-font-smoothing: antialiased;
    }}
    .print-header {{
      display: flex;
      align-items: center;
      gap: 20px;
      border-bottom: 3px solid var(--md-sys-color-primary);
      padding-bottom: 20px;
      margin-bottom: 28px;
    }}
    .print-header img {{ height: 56px; width: auto; }}
    .print-header h1 {{
      margin: 0;
      font-size: 1.5rem;
      font-weight: 700;
      color: var(--md-sys-color-primary);
      letter-spacing: 0.01rem;
      line-height: 1.2;
    }}
    .print-header .subtitle {{
      margin: 2px 0 0;
      font-size: 0.82rem;
      font-weight: 600;
      letter-spacing: 0.08rem;
      text-transform: uppercase;
      color: var(--olive-deep);
    }}
    .section {{
      border: 1px solid var(--md-sys-color-outline);
      border-top: 4px solid var(--md-sys-color-primary);
      border-radius: 12px;
      padding: 24px;
      margin-bottom: 20px;
      background: var(--md-sys-color-surface);
      box-shadow: var(--el-1);
    }}
    .section h2 {{
      margin: 0 0 14px;
      font-size: 0.82rem;
      font-weight: 700;
      color: var(--olive-deep);
      text-transform: uppercase;
      letter-spacing: 0.08rem;
    }}
    table {{ width: 100%; border-collapse: collapse; }}
    th {{
      text-align: left;
      width: 35%;
      padding: 12px 14px;
      background: var(--md-sys-color-surface-container);
      color: var(--olive-deep);
      font-weight: 700;
      font-size: 0.78rem;
      letter-spacing: 0.08rem;
      text-transform: uppercase;
      border-bottom: 1px solid var(--md-sys-color-outline-variant);
    }}
    td {{
      padding: 12px 14px;
      border-bottom: 1px solid var(--md-sys-color-outline-variant);
    }}
    .waiver-text {{
      white-space: pre-wrap;
      background: var(--md-sys-color-surface-container-low);
      border: 1px solid var(--md-sys-color-outline);
      border-radius: 10px;
      padding: 20px;
      font-size: 0.9rem;
      line-height: 1.65;
      letter-spacing: 0.01rem;
    }}
    .signature-block {{
      margin-top: 32px;
      border-top: 3px solid var(--md-sys-color-primary);
      padding-top: 24px;
    }}
    .signature-line {{
      display: inline-block;
      border-bottom: 1.5px solid #1b1b1b;
      min-width: 240px;
      padding-bottom: 4px;
      margin-bottom: 8px;
      font-weight: 600;
    }}
    .footer {{
      margin-top: 32px;
      padding-top: 12px;
      border-top: 1px solid var(--md-sys-color-outline);
      font-size: 0.8rem;
      color: #667;
    }}
    @media print {{
      body {{ padding: 16px; }}
      .no-print {{ display: none; }}
      .section {{ box-shadow: none; border-radius: 8px; }}
    }}
    .no-print {{
      margin-bottom: 16px;
      display: flex;
      gap: 12px;
      align-items: center;
    }}
    .no-print button {{
      display: inline-block;
      padding: 16px 28px;
      background: linear-gradient(180deg, #8ba855 0%, {PRIMARY_OLIVE} 100%);
      color: var(--md-sys-color-on-primary);
      border: none;
      border-radius: 10px;
      font-family: 'Jost', sans-serif;
      font-weight: 600;
      cursor: pointer;
      text-transform: uppercase;
      letter-spacing: 0.08rem;
      font-size: 0.82rem;
      box-shadow: var(--el-1);
      transition: transform 0.2s ease, box-shadow 0.2s ease;
    }}
    .no-print button:hover {{ transform: translateY(-1px); box-shadow: var(--el-2); }}
    .no-print button:active {{ transform: translateY(0); box-shadow: var(--el-1); }}
    .no-print button:focus-visible {{ outline: 2px solid var(--md-sys-color-primary); outline-offset: 2px; }}
    .no-print a {{
      color: var(--md-sys-color-primary);
      font-weight: 700;
      text-decoration: none;
      font-size: 0.85rem;
      letter-spacing: 0.06rem;
      text-transform: uppercase;
    }}
    @media (prefers-reduced-motion: reduce) {{ * {{ transition: none !important; animation: none !important; }} }}
  </style>
</head>
<body>
  <div class="no-print">
    <button onclick="window.print()">Print this page</button>
    <a href="/admin/lead/{s.get('id', '')}" style="color:{PRIMARY_OLIVE};font-weight:700;text-decoration:none">Back to lead</a>
  </div>
  <div class="print-header">
    <img src="{LOGO_URL}" alt="Benton Drones logo">
    <div>
      <h1>Consent & Waiver Form</h1>
      <p class="subtitle">Benton Drones &mdash; Lead Ingest System</p>
    </div>
  </div>

  <div class="section">
    <h2>Lead details</h2>
    <table>
      {row("Name", name)}
      {row("Email", s.get("email", ""))}
      {row("Phone", s.get("phone", ""))}
      {row("Address", s.get("full_address", ""))}
      {row("Campaign", s.get("campaign", ""))}
      {row("Source", s.get("source", ""))}
      {row("Signup ID", str(s.get("id", "")))}
      {row("Created", s.get("created_at", ""))}
    </table>
  </div>

  <div class="section">
    <h2>Consent record</h2>
    <table>
      {row("Consent version", c.get("consent_version", CONSENT_VERSION))}
      {row("Consent text", CONSENT_TEXT)}
      {row("Accepted at", c.get("accepted_at", ""))}
      {row("IP address", c.get("ip_address", ""))}
      {row("User agent", c.get("user_agent", ""))}
    </table>
  </div>

  <div class="section">
    <h2>Signature & waiver</h2>
    <table>
      {row("Typed name", sig.get("full_name_typed", ""))}
      {row("Signed at", sig.get("signed_at", ""))}
      {row("Waiver version", sig.get("waiver_version", WAIVER_VERSION))}
      {row("IP address", sig.get("ip_address", ""))}
      {row("User agent", sig.get("user_agent", ""))}
      {row("Disclaimer", SIGNATURE_DISCLAIMER)}
    </table>
  </div>

  <div class="section">
    <h2>Waiver text ({sig.get("waiver_version", WAIVER_VERSION)})</h2>
    <div class="waiver-text">{escape(WAIVER_TEXT)}</div>
  </div>

  <div class="signature-block">
    <p>Signature: <span class="signature-line">{escape(sig.get("full_name_typed", ""))}</span></p>
    <p>Date: {escape(sig.get("signed_at", ""))}</p>
  </div>

  <div class="footer">
    <p>Benton Drones — Lead Ingest System. Generated on {escape(s.get("created_at", ""))}.</p>
  </div>
</body>
</html>"""
    return html.encode("utf-8")


def _sanitize_pdf_text(text: str) -> str:
    """Replace non-latin-1 characters with ASCII equivalents for fpdf2 core fonts.

    fpdf2's built-in Helvetica only supports latin-1. The waiver text contains
    em-dashes and other Unicode punctuation that would crash the encoder.
    """
    replacements = {
        "\u2014": "--",   # em-dash
        "\u2013": "-",     # en-dash
        "\u201c": '"',      # left double quote
        "\u201d": '"',      # right double quote
        "\u2018": "'",       # left single quote
        "\u2019": "'",       # right single quote
        "\u2026": "...",    # ellipsis
        "\u00a0": " ",      # non-breaking space
        "\u00a9": "(c)",    # copyright
        "\u2122": "(TM)",   # trademark
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text.encode("latin-1", "replace").decode("latin-1")


def try_render_pdf(
    signup: Any,
    consent: Any | None = None,
    signature: Any | None = None,
) -> bytes | None:
    """Attempt to generate a PDF using fpdf2.

    Returns PDF bytes if fpdf2 is available, or None if not installed.
    Raises no exception — returns None on any failure.
    """
    try:
        from fpdf import FPDF
    except ImportError:
        return None

    s = _row_to_dict(signup)
    c = _row_to_dict(consent)
    sig = _row_to_dict(signature)

    try:
        pdf = FPDF(orientation="P", unit="mm", format="A4")
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        # Header
        pdf.set_font("Helvetica", "B", 16)
        pdf.set_text_color(r=0x80, g=0x99, b=0x48)  # olive
        pdf.cell(0, 10, text="Benton Drones", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 12)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 8, text="Consent & Waiver Form", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

        name = _sanitize_pdf_text(f"{s.get('first_name', '')} {s.get('last_name', '')}".strip())

        def section_title(title: str):
            pdf.ln(3)
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_fill_color(0xFF, 0xFC, 0xE7)  # cream
            pdf.cell(0, 7, text=_sanitize_pdf_text(title), new_x="LMARGIN", new_y="NEXT", fill=True)

        def field_row(label: str, value: str):
            value = _sanitize_pdf_text(value or "-")
            if len(value) > 90:
                value = value[:87] + "..."
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(50, 6, text=_sanitize_pdf_text(label), border="B")
            pdf.set_font("Helvetica", "", 10)
            pdf.cell(0, 6, text=value, border="B", new_x="LMARGIN", new_y="NEXT")

        # Lead details
        section_title("Lead details")
        field_row("Name", name)
        field_row("Email", s.get("email", ""))
        field_row("Phone", s.get("phone", ""))
        field_row("Address", s.get("full_address", ""))
        field_row("Campaign", s.get("campaign", ""))
        field_row("Source", s.get("source", ""))
        field_row("Signup ID", str(s.get("id", "")))
        field_row("Created", s.get("created_at", ""))

        # Consent record
        section_title("Consent record")
        field_row("Consent version", c.get("consent_version", CONSENT_VERSION))
        field_row("Accepted at", c.get("accepted_at", ""))
        field_row("IP address", c.get("ip_address", ""))
        field_row("User agent", c.get("user_agent", ""))

        # Signature & waiver
        section_title("Signature & waiver")
        field_row("Typed name", sig.get("full_name_typed", ""))
        field_row("Signed at", sig.get("signed_at", ""))
        field_row("Waiver version", sig.get("waiver_version", WAIVER_VERSION))
        field_row("IP address", sig.get("ip_address", ""))
        field_row("User agent", sig.get("user_agent", ""))

        # Waiver text
        section_title("Waiver text")
        pdf.set_font("Helvetica", "", 9)
        for line in WAIVER_TEXT.split("\n"):
            pdf.multi_cell(0, 5, text=_sanitize_pdf_text(line))

        # Footer
        pdf.ln(6)
        pdf.set_font("Helvetica", "I", 8)
        pdf.set_text_color(0x66, 0x66, 0x66)
        pdf.cell(0, 5, text="Benton Drones - Lead Ingest System", new_x="LMARGIN", new_y="NEXT")

        return bytes(pdf.output())
    except Exception:
        return None
