from __future__ import annotations

from html import escape

LOGO_URL = "https://www.bentondrones.com/cdn/shop/files/BENTON_DRONES_WEBSITE_LOGO.png?v=1715201940&width=500"

PRIMARY_OLIVE = "#809948"
OLIVE_DARK = "#6f853d"
OLIVE_DEEP = "#5a6f30"
PAGE_BG = "#f7f7f3"
LINK_BLUE = "#6184d8"
ACCENT_BLUE = "#0000ff"
CREAM = "#fffce7"
PALE_BLUE = "#e7ecff"
PALE_GREEN = "#f0f7f4"
BLACK = "#000000"
WHITE = "#ffffff"


def branded_page(title: str, body: str, show_nav: bool = False) -> bytes:
    nav_html = ""
    if show_nav:
        nav_html = f"""
        <nav class="benton-nav">
          <a class="logo" href="/overview">
            <img src="{LOGO_URL}" alt="Benton Drones logo" loading="lazy">
          </a>
          <div class="nav-links">
            <a href="/overview">Overview</a>
            <a href="/admin">Admin</a>
            <a href="/admin-logout">Logout</a>
          </div>
        </nav>
        """
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Jost:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {{
      --olive: {PRIMARY_OLIVE};
      --olive-dark: {OLIVE_DARK};
      --olive-deep: {OLIVE_DEEP};
      --page-bg: {PAGE_BG};
      --link-blue: {LINK_BLUE};
      --accent-blue: {ACCENT_BLUE};
      --cream: {CREAM};
      --pale-blue: {PALE_BLUE};
      --pale-green: {PALE_GREEN};
      --black: {BLACK};
      --white: {WHITE};

      --md-sys-color-primary: {PRIMARY_OLIVE};
      --md-sys-color-on-primary: {WHITE};
      --md-sys-color-primary-container: {PALE_GREEN};
      --md-sys-color-on-primary-container: #1b1b1b;
      --md-sys-color-secondary: {LINK_BLUE};
      --md-sys-color-on-secondary: {WHITE};
      --md-sys-color-tertiary: {ACCENT_BLUE};
      --md-sys-color-surface: {WHITE};
      --md-sys-color-surface-container-low: #fbfbf8;
      --md-sys-color-surface-container: #f5f5f0;
      --md-sys-color-surface-container-high: #efefe9;
      --md-sys-color-background: {PAGE_BG};
      --md-sys-color-on-surface: #1b1b1b;
      --md-sys-color-on-surface-variant: #44464f;
      --md-sys-color-outline: #d7d3c5;
      --md-sys-color-outline-variant: #ede8d8;
      --md-sys-color-error: #b3261e;
      --md-sys-color-on-error: {WHITE};
      --md-sys-color-error-container: #f9dedc;

      --el-1: 0 1px 2px rgba(0,0,0,0.04), 0 1px 4px rgba(0,0,0,0.06);
      --el-2: 0 2px 4px rgba(0,0,0,0.05), 0 6px 16px rgba(0,0,0,0.07);
      --el-3: 0 4px 8px rgba(0,0,0,0.06), 0 12px 28px rgba(0,0,0,0.08);
      --md-elevation-1: var(--el-1);
      --md-elevation-2: var(--el-2);
      --md-elevation-3: var(--el-3);

      --radius-card: 16px;
      --radius-button: 10px;
      --radius-input: 10px;
      --radius-table: 12px;
      --radius-chip: 999px;
    }}
    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; }}
    body {{
      font-family: 'Jost', sans-serif;
      font-weight: 500;
      letter-spacing: 0.02rem;
      margin: 0;
      background: var(--md-sys-color-background);
      color: #1b1b1b;
      line-height: 1.65;
      font-size: 1.05rem;
      -webkit-font-smoothing: antialiased;
    }}

    /* Top App Bar — premium glass nav */
    .benton-nav {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      height: 72px;
      padding: 0 32px;
      background: rgba(255,255,255,0.88);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--md-sys-color-outline);
      box-shadow: 0 1px 3px rgba(0,0,0,0.04);
      position: sticky;
      top: 0;
      z-index: 100;
    }}
    .benton-nav .logo img {{
      height: 44px; width: auto;
      transition: transform 0.2s ease, opacity 0.2s ease;
    }}
    .benton-nav .logo:hover img {{ transform: scale(1.03); opacity: 0.92; }}
    .benton-nav .nav-links {{ display: flex; gap: 4px; align-items: center; }}
    .benton-nav .nav-links a {{
      color: var(--md-sys-color-on-surface-variant);
      text-decoration: none;
      font-weight: 600;
      text-transform: uppercase;
      font-size: 0.78rem;
      letter-spacing: 0.08rem;
      padding: 10px 16px;
      border-radius: var(--radius-chip);
      transition: background 0.2s ease, color 0.2s ease;
    }}
    .benton-nav .nav-links a:hover {{
      background: var(--md-sys-color-primary-container);
      color: var(--olive-deep);
    }}
    .benton-nav .nav-links a.active {{
      background: var(--md-sys-color-primary);
      color: var(--md-sys-color-on-primary);
    }}
    .benton-nav a.logo {{ padding: 0; }}
    .benton-nav a.logo:hover {{ background: transparent; }}

    main {{
      max-width: 1080px;
      margin: 0 auto;
      padding: 48px 24px 80px;
    }}

    /* Typography */
    h1 {{
      color: var(--md-sys-color-primary);
      font-size: 2.4rem; font-weight: 700;
      letter-spacing: 0.01rem; line-height: 1.15;
      margin-top: 0; margin-bottom: 8px;
    }}
    h2 {{
      color: var(--md-sys-color-primary);
      font-size: 1.7rem; font-weight: 700;
      letter-spacing: 0.01rem; line-height: 1.2;
      margin-top: 48px; margin-bottom: 12px;
    }}
    h3 {{
      color: var(--md-sys-color-primary);
      font-size: 1.3rem; font-weight: 600;
      line-height: 1.3; margin-top: 0; margin-bottom: 8px;
    }}
    p {{ margin: 0 0 12px; }}
    a {{ color: var(--md-sys-color-secondary); text-decoration: none; transition: opacity 0.2s ease; }}
    a:hover {{ text-decoration: underline; opacity: 0.88; }}

    /* Cards — softer shadows, hover lift */
    form, .card {{
      background: var(--md-sys-color-surface);
      padding: 28px;
      border: 1px solid var(--md-sys-color-outline);
      border-radius: var(--radius-card);
      box-shadow: var(--el-1);
      transition: transform 0.22s ease, box-shadow 0.22s ease;
    }}
    .card:hover {{ transform: translateY(-2px); box-shadow: var(--el-2); }}
    .card + .card {{ margin-top: 24px; }}
    .card.accent {{ border-top: 4px solid var(--md-sys-color-primary); }}

    /* Forms */
    label {{
      display: block; margin-top: 20px;
      font-size: 0.78rem; font-weight: 700;
      letter-spacing: 0.08rem; text-transform: uppercase;
      color: var(--olive-deep);
    }}
    input, textarea, select {{
      width: 100%; padding: 14px 16px; margin-top: 8px;
      border: 1px solid var(--md-sys-color-outline);
      border-radius: var(--radius-input);
      font-family: 'Jost', sans-serif;
      font-size: 1rem; font-weight: 500; letter-spacing: 0.02rem;
      background: var(--md-sys-color-surface); color: #1b1b1b;
      transition: border-color 0.2s ease, box-shadow 0.2s ease;
    }}
    input:focus, textarea:focus, select:focus {{
      outline: none;
      border-color: var(--md-sys-color-primary);
      box-shadow: 0 0 0 3px var(--md-sys-color-primary-container);
    }}
    input[type="checkbox"] {{
      width: 20px; height: 20px; margin-right: 10px;
      vertical-align: middle; accent-color: var(--md-sys-color-primary);
    }}
    .helper {{ font-size: 0.82rem; color: var(--md-sys-color-on-surface-variant); margin-top: 6px; }}

    /* Buttons — subtle gradient, premium feel */
    button, .button {{
      display: inline-flex; align-items: center; justify-content: center;
      margin-top: 24px; padding: 16px 28px; border: none;
      border-radius: var(--radius-button);
      background: linear-gradient(180deg, #8ba855 0%, {PRIMARY_OLIVE} 100%);
      color: var(--md-sys-color-on-primary);
      font-family: 'Jost', sans-serif;
      font-weight: 600; letter-spacing: 0.08rem;
      text-decoration: none; cursor: pointer;
      text-transform: uppercase; font-size: 0.82rem;
      transition: transform 0.2s ease, box-shadow 0.2s ease;
      box-shadow: var(--el-1);
    }}
    button:hover, .button:hover {{ transform: translateY(-1px); box-shadow: var(--el-2); text-decoration: none; }}
    button:active, .button:active {{ transform: translateY(0); box-shadow: var(--el-1); }}
    button.secondary, .button.secondary {{
      background: transparent; color: var(--md-sys-color-secondary);
      border: 1.5px solid var(--md-sys-color-secondary); box-shadow: none;
    }}
    button.secondary:hover, .button.secondary:hover {{ background: var(--pale-blue); border-color: var(--md-sys-color-secondary); }}
    button.text, .button.text {{
      background: transparent; color: var(--md-sys-color-tertiary);
      box-shadow: none; padding: 8px 12px; margin-top: 8px;
    }}
    button:focus-visible, .button:focus-visible {{
      outline: 2px solid var(--md-sys-color-primary); outline-offset: 2px;
    }}

    /* Messages */
    .error {{
      background: var(--md-sys-color-error-container);
      border: 1px solid var(--md-sys-color-error);
      color: var(--md-sys-color-error);
      padding: 16px 20px; border-radius: var(--radius-card);
      margin-bottom: 16px; font-size: 0.95rem;
    }}
    .success {{
      background: var(--md-sys-color-primary-container);
      border: 1px solid var(--md-sys-color-primary);
      padding: 28px; border-radius: var(--radius-card);
    }}

    /* Tables — cleaner, subtle separators */
    table {{
      width: 100%; border-collapse: collapse;
      background: var(--md-sys-color-surface);
      border: 1px solid var(--md-sys-color-outline);
      border-radius: var(--radius-table); overflow: hidden;
      box-shadow: var(--el-1);
    }}
    th, td {{ border-bottom: 1px solid var(--md-sys-color-outline-variant); padding: 16px 18px; text-align: left; }}
    th {{
      background: var(--md-sys-color-surface-container);
      color: var(--olive-deep); font-weight: 700;
      font-size: 0.78rem; letter-spacing: 0.08rem; text-transform: uppercase;
    }}
    tr:last-child td {{ border-bottom: none; }}
    tr:hover td {{ background: var(--md-sys-color-surface-container-low); }}

    /* Layout */
    .two-col {{ display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }}

    /* Waiver box — cleaner scroll area */
    .waiver-box {{
      background: var(--md-sys-color-surface-container-low);
      border: 1px solid var(--md-sys-color-outline);
      border-radius: 12px; padding: 24px;
      max-height: 240px; overflow-y: auto; white-space: pre-wrap;
      font-size: 0.92rem; line-height: 1.65; letter-spacing: 0.01rem; margin-top: 10px;
    }}
    .waiver-box::-webkit-scrollbar {{ width: 8px; }}
    .waiver-box::-webkit-scrollbar-track {{ background: transparent; }}
    .waiver-box::-webkit-scrollbar-thumb {{ background: var(--md-sys-color-outline); border-radius: 4px; }}

    /* Analytics metric cards */
    .analytics {{
      display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 20px; margin-bottom: 32px;
    }}
    .metric {{
      background: var(--md-sys-color-surface);
      border: 1px solid var(--md-sys-color-outline);
      border-top: 4px solid var(--md-sys-color-primary);
      border-radius: var(--radius-card); padding: 24px; text-align: center;
      box-shadow: var(--el-1);
      transition: transform 0.22s ease, box-shadow 0.22s ease;
    }}
    .metric:hover {{ transform: translateY(-2px); box-shadow: var(--el-2); }}
    .metric .value {{ font-size: 2.2rem; font-weight: 700; color: var(--md-sys-color-primary); line-height: 1.1; }}
    .metric .label {{
      font-size: 0.75rem; font-weight: 700; letter-spacing: 0.08rem;
      text-transform: uppercase; color: var(--md-sys-color-on-surface-variant); margin-top: 8px;
    }}

    /* Map */
    #map {{
      height: 420px; border: 1px solid var(--md-sys-color-outline);
      border-radius: var(--radius-card); margin-top: 16px; box-shadow: var(--el-1);
    }}

    /* Breakdown chips */
    .breakdown {{ margin-top: 12px; }}
    .breakdown span {{
      display: inline-block;
      background: var(--md-sys-color-surface-container-low);
      color: var(--md-sys-color-on-surface); padding: 7px 16px; margin: 4px 6px 0 0;
      font-size: 0.78rem; font-weight: 600; letter-spacing: 0.06rem;
      text-transform: uppercase; border: 1px solid var(--md-sys-color-secondary);
      border-radius: var(--radius-chip); transition: background 0.2s ease;
    }}
    .breakdown span:hover {{ background: var(--pale-blue); }}

    /* Responsive */
    @media (max-width: 600px) {{
      .two-col {{ grid-template-columns: 1fr; }}
      .benton-nav {{ height: 60px; padding: 0 16px; }}
      .benton-nav .logo img {{ height: 36px; }}
      .benton-nav .nav-links a {{ padding: 8px 12px; font-size: 0.72rem; }}
      main {{ padding: 32px 16px 64px; }}
      h1 {{ font-size: 1.8rem; }}
      h2 {{ font-size: 1.4rem; }}
    }}

    /* Accessibility */
    @media (prefers-reduced-motion: reduce) {{
      * {{ transition: none !important; animation: none !important; }}
      .card:hover, .metric:hover {{ transform: none; }}
    }}
  </style>
</head>
<body>
  {nav_html}
  <main>{body}</main>
</body>
</html>"""
    return html.encode("utf-8")
