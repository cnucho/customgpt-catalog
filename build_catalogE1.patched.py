
# ===============================
# build_catalogE1.patched.py
# ===============================

import os, yaml, html

SITE_DIR = "site"
DETAILS_DIR = os.path.join(SITE_DIR, "details")
EN_DIR = os.path.join(SITE_DIR, "en")

def esc(x):
    return html.escape(str(x)) if x is not None else ""

# -------------------------------
# Name display rules (NO TRANSLATION)
# -------------------------------

def display_name_ko(e):
    if e.get("name_ko") and e.get("name_en"):
        return f"{esc(e['name_ko'])} ({esc(e['name_en'])})"
    return esc(e.get("name_ko") or e.get("name_en") or e.get("_id",""))

def display_name_en(e):
    return esc(e.get("name_en") or e.get("name") or e.get("_id",""))

# -------------------------------
# Index rendering
# -------------------------------

def render_index(entries, lang="ko"):
    rows = []
    for e in entries:
        name = display_name_ko(e) if lang=="ko" else display_name_en(e)
        gpt_url = esc(e.get("url",""))
        detail = f"details/{e['_id']}_{lang}.html" if lang=="ko" else f"details/{e['_id']}_en.html"

        btns = []
        if gpt_url:
            btns.append(f"<a class='btn btn-small' href='{gpt_url}' target='_blank'>GPT</a>")
        btns.append(f"<a class='btn btn-small' href='{detail}'>상세</a>")

        rows.append(f"""
        <li>
          <strong>{name}</strong>
          <div class='btnbar'>{"".join(btns)}</div>
        </li>
        """)

    return f"""
    <html>
    <head>
    <style>
      body {{ font-family: sans-serif; }}
      .btnbar {{ display:flex; gap:6px; margin-top:6px; }}
      .btn {{ text-decoration:none; border-radius:8px; background:#f2f2f2; color:#222; }}
      .btn-small {{ font-size:11px; padding:4px 8px; }}
    </style>
    </head>
    <body>
      <ul>
        {''.join(rows)}
      </ul>
    </body>
    </html>
    """

# -------------------------------
# Detail rendering
# -------------------------------

def render_detail(e, lang="ko"):
    name = display_name_ko(e) if lang=="ko" else display_name_en(e)
    gpt_url = esc(e.get("url",""))

    return f"""
    <html>
    <body>
      <h1>{name}</h1>
      {"<a href='"+gpt_url+"' target='_blank'>GPT 바로가기</a>" if gpt_url else ""}
    </body>
    </html>
    """

# -------------------------------
# Build
# -------------------------------

def build():
    os.makedirs(DETAILS_DIR, exist_ok=True)
    os.makedirs(EN_DIR, exist_ok=True)

    entries = []
    for fn in os.listdir("catalog"):
        if fn.endswith(".yml") or fn.endswith(".yaml"):
            with open(os.path.join("catalog", fn), encoding="utf-8") as f:
                e = yaml.safe_load(f)
                entries.append(e)

    # index
    with open(os.path.join(SITE_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(render_index(entries, "ko"))

    with open(os.path.join(EN_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(render_index(entries, "en"))

    # details
    for e in entries:
        with open(os.path.join(DETAILS_DIR, f"{e['_id']}_ko.html"), "w", encoding="utf-8") as f:
            f.write(render_detail(e, "ko"))
        with open(os.path.join(DETAILS_DIR, f"{e['_id']}_en.html"), "w", encoding="utf-8") as f:
            f.write(render_detail(e, "en"))

if __name__ == "__main__":
    build()
