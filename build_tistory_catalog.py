import os, yaml, re, html
from urllib.parse import quote

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CATALOG_DIR = os.path.join(BASE_DIR, "catalog")
OUT_PATH = os.path.join(BASE_DIR, "tistory_catalog.html")

# 네 GitHub Pages 주소
PAGES_BASE = "https://cnucho.github.io/customgpt-catalog"

# 티스토리 목록 글 주소 (여기로 돌아오게 함)
TISTORY_LIST_URL = "https://skcho.tistory.com/129"

HANGUL = re.compile(r"[가-힣]")

def esc(x):
    return html.escape(str(x)) if x else ""

def slugify(text: str) -> str:
    t = (text or "").lower()
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    return t or "item"

def load_yaml(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except:
        return None

def is_korean(entry, filename):
    fn = filename.lower()
    if fn.endswith("_ko.yaml") or fn.endswith("_kr.yaml") or "_ko_" in fn or "_kr_" in fn:
        return True
    lang = str(entry.get("language", "")).lower()
    if lang in ("ko", "kr", "korean"):
        return True
    name = entry.get("name_ko") or entry.get("name") or ""
    return bool(HANGUL.search(str(name)))

items = []

for fn in os.listdir(CATALOG_DIR):
    if not fn.lower().endswith(".yaml"):
        continue

    raw = load_yaml(os.path.join(CATALOG_DIR, fn))
    if not isinstance(raw, dict):
        continue

    entry = raw.get("catalog_entry", raw)
    if not isinstance(entry, dict):
        continue

    if not is_korean(entry, fn):
        continue

    name = entry.get("name_ko") or entry.get("name") or ""
    desc = entry.get("one_line_ko") or entry.get("one_line") or ""
    url = entry.get("url") or ""

    base_name_for_slug = entry.get("name_en") or entry.get("name") or entry.get("name_ko") or name
    slug = slugify(base_name_for_slug)

    # 티스토리로 돌아오는 back 파라미터 포함
    back = quote(TISTORY_LIST_URL, safe="")
    detail_url = f"{PAGES_BASE}/details/{slug}_ko.html?back={back}"

    items.append({"name": name, "desc": desc, "url": url, "detail": detail_url})

# 보기 좋게 이름순 정렬
items.sort(key=lambda x: x["name"])

rows = []
for it in items:
    rows.append(f"""
<li data-text="{esc(it['name'] + ' ' + it['desc'])}"
    style="margin:0 0 14px 0; padding:0 0 12px 0; border-bottom:1px solid #ddd;">
  <strong>{esc(it['name'])}</strong><br/>
  <span style="color:#555; font-size:0.92em;">{esc(it['desc'])}</span><br/>
  <a href="{esc(it['url'])}" target="_blank" rel="noopener noreferrer">GPT 바로가기</a>
  &nbsp;|&nbsp;
  <a href="{esc(it['detail'])}" target="_blank" rel="noopener noreferrer">상세 보기</a>
</li>
""")

html_out = f"""
<div style="font-family:system-ui, -apple-system, 'Segoe UI', sans-serif;">
  <h3>연구·조사·분석용 커스텀 GPT 목록</h3>
  <input id="q" placeholder="검색어 입력"
         style="width:100%; padding:8px; margin:8px 0 14px 0;"/>
  <ul id="list" style="list-style:none; padding:0; margin:0;">
    {''.join(rows) if rows else "<li>항목이 없습니다.</li>"}
  </ul>
</div>

<script>
const q = document.getElementById('q');
const items = document.querySelectorAll('#list li');
q.addEventListener('input', () => {{
  const v = q.value.toLowerCase().trim();
  items.forEach(li => {{
    li.style.display = li.dataset.text.toLowerCase().includes(v) ? '' : 'none';
  }});
}});
</script>
"""

with open(OUT_PATH, "w", encoding="utf-8") as f:
    f.write(html_out)

print("Tistory catalog created:", OUT_PATH)
print("Items:", len(items))
