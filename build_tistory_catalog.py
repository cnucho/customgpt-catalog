import os
import yaml
import html

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CATALOG_DIR = os.path.join(BASE_DIR, "catalog")
TISTORY_DIR = os.path.join(BASE_DIR, "tistory")
OUT_PATH = os.path.join(TISTORY_DIR, "tistory_catalog.html")

os.makedirs(TISTORY_DIR, exist_ok=True)

def load_yaml(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception:
        return None

def normalize_entry(raw):
    if not isinstance(raw, dict):
        return None
    if "catalog_entry" in raw:
        return raw["catalog_entry"]
    return raw

def esc(x):
    return html.escape(str(x)) if x else ""

items = []

for fn in os.listdir(CATALOG_DIR):
    if not fn.endswith(".yaml"):
        continue

    raw = load_yaml(os.path.join(CATALOG_DIR, fn))
    entry = normalize_entry(raw)
    if not entry:
        continue

    gpt_id = entry.get("gpt_id")
    name_en = entry.get("name_en")
    url = entry.get("url")

    if not gpt_id or not name_en or not url:
        continue

    name_ko = entry.get("name_ko")
    ko_policy = entry.get("name_ko_policy", "none")

    display_name = name_en
    if name_ko:
        if ko_policy == "auto":
            display_name = f"{name_en} · (자동번역) {name_ko}"
        else:
            display_name = f"{name_en} · {name_ko}"

    desc = entry.get("one_line_ko") or entry.get("one_line_en") or ""

    # 외부 안내 페이지
    links = [f"<a href='{esc(url)}' target='_blank'>GPT 바로가기</a>"]

    if entry.get("tistory_url"):
        links.append(f"<a href='{esc(entry['tistory_url'])}' target='_blank'>티스토리 설명</a>")
    if entry.get("github_url"):
        links.append(f"<a href='{esc(entry['github_url'])}' target='_blank'>GitHub 안내</a>")

    items.append({
        "name_en": name_en.lower(),
        "display": display_name,
        "desc": desc,
        "links": " | ".join(links)
    })

# 알파벳순 정렬 (영문 기준)
items.sort(key=lambda x: x["name_en"])

rows = []
for idx, it in enumerate(items, start=1):
    rows.append(f"""
<li style="margin:0 0 16px 0; padding:0 0 12px 0; border-bottom:1px solid #ddd;">
  <strong>{idx}. {esc(it['display'])}</strong><br/>
  <span style="color:#555; font-size:0.95em;">{esc(it['desc'])}</span><br/>
  {it['links']}
</li>
""")

html_out = f"""
<div style="font-family:system-ui, -apple-system, 'Segoe UI', sans-serif;">
  <h3>GPT Catalog</h3>
  <ul style="list-style:none; padding:0; margin:0;">
    {''.join(rows) if rows else "<li>항목이 없습니다.</li>"}
  </ul>
</div>
"""

with open(OUT_PATH, "w", encoding="utf-8") as f:
    f.write(html_out)

print("[OK] tistory_catalog.html generated")
print("[OK] items:", len(items))
