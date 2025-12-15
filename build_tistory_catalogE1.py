import os
import yaml
import re
import html

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CATALOG_DIR = os.path.join(BASE_DIR, "catalog")
TISTORY_DIR = os.path.join(BASE_DIR, "tistory")

OUT_KO = os.path.join(TISTORY_DIR, "index_ko.html")
OUT_EN = os.path.join(TISTORY_DIR, "index_en.html")

os.makedirs(TISTORY_DIR, exist_ok=True)

# === Configure this to your GitHub Pages base (NO trailing slash) ===
GITHUB_PAGES_BASE = "https://cnucho.github.io/customgpt-catalog"

HANGUL_RE = re.compile(r"[가-힣]")
SAFE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$", re.IGNORECASE)

def esc(s):
    return html.escape(str(s)) if s is not None else ""

def slugify(text: str) -> str:
    t = (text or "").lower()
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    return t or "item"

def sanitize_id(raw_id: str) -> str:
    if not raw_id:
        return "item"
    s = str(raw_id).strip()
    return s if SAFE_ID_RE.match(s) else slugify(s)

def sanitize_filename(name: str) -> str:
    s = str(name or "").strip()
    s = re.sub(r'[<>:"/\\|?*]', "_", s)
    s = re.sub(r"\s+", "_", s).strip("._ ")
    return s or "item"

def load_yaml_safe(path: str):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"[SKIP] {os.path.basename(path)}")
        print(f"       {e}")
        return None

def normalize_entry(data: dict) -> dict:
    if not isinstance(data, dict):
        return {}
    if "catalog_entry" in data and isinstance(data["catalog_entry"], dict):
        return data["catalog_entry"]
    if "gpt" in data and isinstance(data["gpt"], dict):
        return data["gpt"]
    return data

def guess_lang(entry: dict, filename: str) -> str:
    """Decide language ONLY by filename markers.
    - EN if token 'en' appears as a filename part (e.g., _en, -en, .en.)
    - KO if token 'ko', 'kr', or 'kor' appears as a filename part
    If no marker is found, defaults to 'en'.
    """
    fn = (filename or "").lower()

    if re.search(r"(^|[_\-.])(en)([_\-.]|$)", fn):
        return "en"
    if re.search(r"(^|[_\-.])(ko|kr|kor)([_\-.]|$)", fn):
        return "ko"
    return "en"
def display_name(e):
    name_en = e.get("name_en") or e.get("name") or ""
    name_ko = e.get("name_ko") or ""
    if e.get("_lang") == "ko":
        # show Korean first; keep EN as suffix if present
        if name_ko and name_en:
            return f"{name_ko} · {name_en}"
        return name_ko or name_en
    # EN page
    if name_en and name_ko:
        return f"{name_en} · {name_ko}"
    return name_en or name_ko

def one_line(e, lang):
    return (
        e.get(f"one_line_{lang}")
        or e.get("one_line")
        or e.get("one_line_ko")
        or e.get("one_line_en")
        or ""
    )

def detail_url(e, lang):
    """
    Links to the GitHub Pages detail page produced by build_catalog.py:
      KO:  {BASE}/details/{id}_ko.html
      EN:  {BASE}/en/details/{id}_en.html
    Must replicate the same id logic used by the builder:
      id = sanitize_id(gpt_id) else slugify(name...)
      duplicate ids get suffixed -2, -3 ... (handled by pre-pass).
    """
    item_id = e.get("_id")
    if not item_id:
        return ""
    detail_basename = sanitize_filename(f"{item_id}_{lang}.html")
    if lang == "ko":
        return f"{GITHUB_PAGES_BASE}/details/{detail_basename}"
    return f"{GITHUB_PAGES_BASE}/en/details/{detail_basename}"

def render(title, entries, lang):
    rows = []
    idx = 1
    for e in entries:
        url = e.get("url") or ""
        if not url:
            continue

        gpt_link = f"<a class='btn' href='{esc(url)}' target='_blank' rel='noopener noreferrer'>GPT 바로가기</a>"
        durl = detail_url(e, lang)
        detail_link = f"<a class='btn' href='{esc(durl)}' target='_blank' rel='noopener noreferrer'>상세정보</a>" if durl else ""

        # optional external guides stored in yaml
        tistory_url = e.get("tistory_url") or ""
        github_url = e.get("github_url") or ""
        extra = []
        if tistory_url:
            extra.append(f"<a class='btn ghost' href='{esc(tistory_url)}' target='_blank' rel='noopener noreferrer'>티스토리</a>")
        if github_url:
            extra.append(f"<a class='btn ghost' href='{esc(github_url)}' target='_blank' rel='noopener noreferrer'>GitHub</a>")
        extra_html = " ".join(extra)

        rows.append(f"""
<li class="item">
  <div class="title"><strong>{idx}. {esc(display_name(e))}</strong></div>
  <div class="meta">{esc(one_line(e, lang))}</div>
  <div class="links">
    {gpt_link}
    {detail_link}
    {extra_html}
  </div>
</li>
""")
        idx += 1

    ko_index = f"{GITHUB_PAGES_BASE}/index.html"
    en_index = f"{GITHUB_PAGES_BASE}/en/index.html"

    topbar = f"""
<div class="topbar">
  <div class="pill">Total: {len(entries)}</div>
  <div class="toplinks">
    <a class="btn ghost" href="{esc(ko_index)}" target="_blank" rel="noopener noreferrer">GitHub 목록(KO)</a>
    <a class="btn ghost" href="{esc(en_index)}" target="_blank" rel="noopener noreferrer">GitHub 목록(EN)</a>
  </div>
</div>
"""

    return f"""
<div class="wrap">
<style>
  .wrap {{ font-family:system-ui,-apple-system,Segoe UI,sans-serif; line-height:1.4; }}
  .topbar {{ display:flex; justify-content:space-between; align-items:center; gap:10px; margin:0 0 10px 0; }}
  .pill {{ font-size:12px; color:#333; background:#f3f3f3; padding:6px 10px; border-radius:999px; }}
  .toplinks {{ display:flex; gap:8px; flex-wrap:wrap; justify-content:flex-end; }}
  ul {{ list-style:none; padding:0; margin:0; }}
  .item {{ margin:0 0 14px 0; padding:12px 0; border-bottom:1px solid #ddd; }}
  .title {{ margin-bottom:6px; }}
  .meta {{ color:#555; margin-bottom:10px; }}
  .links {{ display:flex; gap:8px; flex-wrap:wrap; }}
  .btn {{ display:inline-block; font-size:13px; padding:6px 10px; border-radius:8px; border:1px solid #ccc; text-decoration:none; }}
  .btn:hover {{ opacity:0.85; }}
  .ghost {{ background:#fafafa; }}
</style>

{topbar}
<h3>{esc(title)}</h3>
<ul>
{''.join(rows) if rows else '<li>항목 없음</li>'}
</ul>
</div>
"""

# =========================
# Pass 1: LOAD + LANG + ID (aligned with builder)
# =========================
all_entries = []

if not os.path.isdir(CATALOG_DIR):
    raise SystemExit(f"[ERR] catalog folder not found: {CATALOG_DIR}")

for fn in sorted(os.listdir(CATALOG_DIR)):
    if not (fn.lower().endswith(".yml") or fn.lower().endswith(".yaml")):
        continue

    raw = load_yaml_safe(os.path.join(CATALOG_DIR, fn))
    if raw is None:
        continue

    entry = normalize_entry(raw)
    if not entry:
        continue

    entry["_src_fn"] = fn
    entry["_lang"] = guess_lang(entry, fn)

    gpt_id = entry.get("gpt_id")
    base_name = entry.get("name_en") or entry.get("name") or entry.get("name_ko") or fn
    raw_id = gpt_id if gpt_id else slugify(base_name)
    entry["_id"] = sanitize_id(raw_id)

    all_entries.append(entry)

# duplicate id suffixing (must match detail filename behavior)
seen = {}
for e in all_entries:
    base = e["_id"]
    n = seen.get(base, 0) + 1
    seen[base] = n
    if n > 1:
        e["_id"] = f"{base}-{n}"

# Split
ko_entries = [e for e in all_entries if e["_lang"] == "ko"]
en_entries = [e for e in all_entries if e["_lang"] == "en"]

# Sort (stable)
def sort_key(e):
    return (str(e.get("name_en") or e.get("name") or e.get("name_ko") or e.get("_id") or "").lower(),
            str(e.get("name_ko") or "").lower())
ko_entries.sort(key=sort_key)
en_entries.sort(key=sort_key)

with open(OUT_KO, "w", encoding="utf-8") as f:
    f.write(render("GPT Catalog (KO)", ko_entries, "ko"))

with open(OUT_EN, "w", encoding="utf-8") as f:
    f.write(render("GPT Catalog (EN)", en_entries, "en"))

print("[OK] Tistory KO:", len(ko_entries))
print("[OK] Tistory EN:", len(en_entries))
print("[OK] Output:", OUT_KO)
print("[OK] Output:", OUT_EN)
