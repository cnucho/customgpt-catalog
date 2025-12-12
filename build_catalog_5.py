import os
import yaml
import re
import html

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CATALOG_DIR = os.path.join(BASE_DIR, "catalog")
SITE_DIR = os.path.join(BASE_DIR, "site")

DETAILS_KO_DIR = os.path.join(SITE_DIR, "details")
EN_DIR = os.path.join(SITE_DIR, "en")
DETAILS_EN_DIR = os.path.join(EN_DIR, "details")

HANGUL_RE = re.compile(r"[가-힣]")

def slugify(text: str) -> str:
    t = (text or "").lower()
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    return t or "item"

def esc(s) -> str:
    return html.escape(str(s)) if s is not None else ""

def load_yaml_safe(path: str):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"[SKIP] {os.path.basename(path)}")
        print(f"       {e}")
        return None

def normalize_entry(data: dict) -> dict:
    # catalog_entry: {...} 로 감싼 형식 지원
    if not isinstance(data, dict):
        return {}
    if "catalog_entry" in data and isinstance(data["catalog_entry"], dict):
        return data["catalog_entry"]
    if "gpt" in data and isinstance(data["gpt"], dict):
        return data["gpt"]
    return data

def get_list(entry: dict, key: str):
    v = entry.get(key, [])
    return v if isinstance(v, list) else ([] if v is None else [v])

def guess_lang(entry: dict, filename: str) -> str:
    fn = filename.lower()
    if fn.endswith("_en.yaml") or fn.endswith("-en.yaml") or "_en_" in fn:
        return "en"
    if fn.endswith("_ko.yaml") or fn.endswith("_kr.yaml") or fn.endswith("-ko.yaml") or fn.endswith("-kr.yaml") or "_ko_" in fn or "_kr_" in fn:
        return "ko"

    lang = (entry.get("language") or entry.get("lang") or "").lower().strip()
    if lang in ("ko", "kr", "kor", "korean"):
        return "ko"
    if lang in ("en", "eng", "english"):
        return "en"

    # 둘 다 없으면 이름 보고 추정
    name = entry.get("name_ko") or entry.get("name") or entry.get("name_en") or ""
    if HANGUL_RE.search(str(name)):
        return "ko"
    return "en"

def render_detail_page(entry: dict, lang: str) -> str:
    name = entry.get(f"name_{lang}") or entry.get("name") or entry.get("name_en") or entry.get("name_ko") or ""
    one_line = entry.get(f"one_line_{lang}") or entry.get("one_line") or entry.get(f"description_{lang}") or entry.get("description") or ""
    url = entry.get("url") or ""

    tags = get_list(entry, "tags")
    functions = get_list(entry, "functions")
    target_users = get_list(entry, "target_users")
    ideal_use_cases = get_list(entry, "ideal_use_cases")
    limitations = get_list(entry, "limitations")
    example_commands = get_list(entry, "example_commands")
    additional_features = get_list(entry, "additional_features")

    def ul(items):
        if not items:
            return "<p>-</p>"
        lis = "\n".join(f"<li>{esc(x)}</li>" for x in items)
        return f"<ul>{lis}</ul>"

    url_html = f"<a href='{esc(url)}' target='_blank' rel='noopener noreferrer'>{esc(url)}</a>" if url else "-"

    title = esc(name)
    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; line-height: 1.5; }}
    .meta {{ color: #555; font-size: 14px; }}
    h1 {{ margin-bottom: 6px; }}
    h2 {{ margin-top: 22px; }}
  </style>
</head>
<body>
  <p class="meta"><a href="../index.html">← Back to index</a></p>
  <h1>{title}</h1>
  <p>{esc(one_line)}</p>

  <h2>URL</h2>
  <p>{url_html}</p>

  <h2>Tags</h2>
  {ul(tags)}

  <h2>Functions</h2>
  {ul(functions)}

  <h2>Target users</h2>
  {ul(target_users)}

  <h2>Ideal use cases</h2>
  {ul(ideal_use_cases)}

  <h2>Limitations</h2>
  {ul(limitations)}

  <h2>Example commands</h2>
  {ul(example_commands)}

  <h2>Additional features</h2>
  {ul(additional_features)}
</body>
</html>
"""

def render_index(entries, lang: str, title: str, details_prefix: str, extra_link_html: str) -> str:
    li = []
    for e in entries:
        slug = e["_slug"]
        name = e.get(f"name_{lang}") or e.get("name") or e.get("name_en") or e.get("name_ko") or slug
        one = e.get(f"one_line_{lang}") or e.get("one_line") or ""
        tags = " ".join(get_list(e, "tags"))
        href = f"{details_prefix}/{slug}_{lang}.html"
        li.append(
            f"<li data-name='{esc(name)}' data-tags='{esc(tags)}' data-one='{esc(one)}'>"
            f"<a href='{href}'>{esc(name)}</a>"
            f"<div class='meta'>{esc(one)}</div>"
            f"</li>"
        )

    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; }}
    input {{ width: 100%; padding: 10px; font-size: 16px; }}
    ul {{ list-style: none; padding: 0; }}
    li {{ padding: 10px 0; border-bottom: 1px solid #eee; }}
    .meta {{ color: #555; font-size: 13px; margin-top: 4px; }}
    .topbar {{ display: flex; gap: 12px; align-items: center; margin-bottom: 12px; }}
    .pill {{ font-size: 12px; color: #333; background: #f3f3f3; padding: 6px 10px; border-radius: 999px; text-decoration: none; }}
  </style>
</head>
<body>
  <div class="topbar">
    <div class="pill">Total: {len(entries)}</div>
    {extra_link_html}
  </div>

  <h1>{esc(title)}</h1>
  <p>Search by name / tags / description</p>
  <input id="q" placeholder="type to filter..." />

  <ul id="list">
    {''.join(li) if li else "<li>(No entries)</li>"}
  </ul>

<script>
  const q = document.getElementById('q');
  const list = document.getElementById('list');
  const items = Array.from(list.querySelectorAll('li'));

  function apply() {{
    const s = (q.value || '').toLowerCase().trim();
    for (const li of items) {{
      const hay = (li.dataset.name + " " + li.dataset.tags + " " + li.dataset.one).toLowerCase();
      li.style.display = hay.includes(s) ? '' : 'none';
    }}
  }}
  q.addEventListener('input', apply);
</script>
</body>
</html>
"""

def build():
    os.makedirs(DETAILS_KO_DIR, exist_ok=True)
    os.makedirs(DETAILS_EN_DIR, exist_ok=True)
    os.makedirs(EN_DIR, exist_ok=True)

    all_entries = []
    for fn in sorted(os.listdir(CATALOG_DIR)):
        if not fn.lower().endswith(".yaml"):
            continue
        raw = load_yaml_safe(os.path.join(CATALOG_DIR, fn))
        if raw is None:
            continue
        entry = normalize_entry(raw)
        if not entry:
            continue

        entry["_src_fn"] = fn
        entry["_lang"] = guess_lang(entry, fn)

        base_name = entry.get("name_en") or entry.get("name") or entry.get("name_ko") or fn
        entry["_slug"] = slugify(base_name)
        all_entries.append(entry)

    # 파일/필드 기반으로 KO/EN 분리
    ko_entries = [e for e in all_entries if e["_lang"] == "ko" or e.get("name_ko")]
    en_entries = [e for e in all_entries if e["_lang"] == "en" or e.get("name_en")]

    # 상세 생성
    for e in ko_entries:
        slug = e["_slug"]
        with open(os.path.join(DETAILS_KO_DIR, f"{slug}_ko.html"), "w", encoding="utf-8") as f:
            f.write(render_detail_page(e, "ko"))

    for e in en_entries:
        slug = e["_slug"]
        with open(os.path.join(DETAILS_EN_DIR, f"{slug}_en.html"), "w", encoding="utf-8") as f:
            f.write(render_detail_page(e, "en"))

    # 인덱스 생성
    ko_extra = "<a class='pill' href='en/index.html'>English</a>"
    en_extra = "<a class='pill' href='../index.html'>Korean</a>"

    with open(os.path.join(SITE_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(render_index(ko_entries, "ko", "GPT Catalog (KO)", "details", ko_extra))

    with open(os.path.join(EN_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(render_index(en_entries, "en", "GPT Catalog (EN)", "details", en_extra))

    print(f"Loaded total: {len(all_entries)}")
    print(f"KO entries : {len(ko_entries)} -> {os.path.join(SITE_DIR,'index.html')}")
    print(f"EN entries : {len(en_entries)} -> {os.path.join(EN_DIR,'index.html')}")

if __name__ == "__main__":
    build()
