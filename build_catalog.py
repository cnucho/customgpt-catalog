import os
import yaml
import re
import html
import urllib.parse
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CATALOG_DIR = os.path.join(BASE_DIR, "catalog")
SITE_DIR = os.path.join(BASE_DIR, "site")

DETAILS_KO_DIR = os.path.join(SITE_DIR, "details")
EN_DIR = os.path.join(SITE_DIR, "en")
DETAILS_EN_DIR = os.path.join(EN_DIR, "details")

# (Optional) If you keep a tistory output folder, atlas.yaml will also be written there.
TISTORY_DIR = os.path.join(BASE_DIR, "tistory")

# 기본 티스토리 목록 URL (back 파라미터 없을 때 사용)
DEFAULT_TISTORY_LIST_URL = "https://skcho.tistory.com/129"

HANGUL_RE = re.compile(r"[가-힣]")
ASCII_LETTERS_RE = re.compile(r"[A-Za-z]")
SAFE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$", re.IGNORECASE)

def esc(s) -> str:
    return html.escape(str(s)) if s is not None else ""

def slugify(text: str) -> str:
    t = (text or "").lower()
    t = re.sub(r"[^a-z0-9]+", "-", t).strip("-")
    return t or "item"

def sanitize_id(raw_id: str) -> str:
    """파일/URL에 안전한 id를 보장한다. 이미 안전하면 그대로, 아니면 slugify."""
    if not raw_id:
        return "item"
    s = str(raw_id).strip()
    return s if SAFE_ID_RE.match(s) else slugify(s)

def sanitize_filename(name: str) -> str:
    """Windows-safe filename sanitizer (keeps meaning; ensures filesystem legality)."""
    s = str(name or "").strip()
    # Replace Windows-illegal filename characters
    s = re.sub(r'[<>:"/\\|?*]', "_", s)
    # Collapse whitespace
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

def get_list(entry: dict, key: str):
    v = entry.get(key, [])
    return v if isinstance(v, list) else ([] if v is None else [v])

def _lang_from_filename(fn_lower: str):
    # Explicit filename-driven language detection (authoritative)
    # Supports: _ko/_kr/_kor, -ko/-kr/-kor, and same for _en/-en, for both .yml/.yaml
    if (
        fn_lower.endswith(("_en.yaml", "_en.yml", "-en.yaml", "-en.yml"))
        or "_en_" in fn_lower
        or "-en_" in fn_lower
        or "_en-" in fn_lower
        or "-en-" in fn_lower
    ):
        return "en"
    if (
        fn_lower.endswith(("_ko.yaml", "_ko.yml", "_kr.yaml", "_kr.yml", "_kor.yaml", "_kor.yml",
                          "-ko.yaml", "-ko.yml", "-kr.yaml", "-kr.yml", "-kor.yaml", "-kor.yml"))
        or "_ko_" in fn_lower or "_kr_" in fn_lower or "_kor_" in fn_lower
        or "-ko_" in fn_lower or "-kr_" in fn_lower or "-kor_" in fn_lower
        or "_ko-" in fn_lower or "_kr-" in fn_lower or "_kor-" in fn_lower
        or "-ko-" in fn_lower or "-kr-" in fn_lower or "-kor-" in fn_lower
    ):
        return "ko"
    return None

def guess_lang(entry: dict, filename: str) -> str:
    """
    언어는 '파일명'과 'language/lang 필드'로만 판정한다.
    콘텐츠(한글 포함 여부) 기반 판정은 섞임/오분류를 유발하므로 사용하지 않는다.
    """
    fn = (filename or "").lower()
    by_fn = _lang_from_filename(fn)
    if by_fn:
        return by_fn

    lang = (entry.get("language") or entry.get("lang") or "").lower().strip()
    if lang in ("ko", "kr", "kor", "korean"):
        return "ko"
    if lang in ("en", "eng", "english"):
        return "en"

    # Default: EN (prevents KO index contamination)
    return "en"

def is_probably_english_name(name: str) -> bool:
    if not name:
        return False
    s = str(name).strip()
    # If it contains Hangul, treat as not English canonical
    if HANGUL_RE.search(s):
        return False
    return bool(ASCII_LETTERS_RE.search(s))

def auto_translate_name_ko(name_en: str) -> str:
    """가벼운 오프라인 자동번역(단어 치환)"""
    if not name_en:
        return ""
    s = str(name_en)

    # Normalize separators
    s = re.sub(r"[-_/]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()

    mapping = {
        "assistant": "어시스턴트",
        "analyzer": "분석기",
        "analysis": "분석",
        "research": "리서치",
        "desk": "데스크",
        "data": "데이터",
        "report": "리포트",
        "writer": "작성기",
        "builder": "빌더",
        "catalog": "카탈로그",
        "atlas": "아틀라스",
        "survey": "설문",
        "weighting": "가중치",
        "pro": "프로",
        "plus": "플러스",
        "qa": "QA",
        "qc": "QC",
        "meta": "메타",
        "guide": "가이드",
        "coach": "코치",
        "planner": "플래너",
        "translator": "번역기",
        "summarizer": "요약기",
        "summarize": "요약",
        "extractor": "추출기",
        "validator": "검증기",
        "checker": "체커",
        "stats": "통계",
        "statistics": "통계",
        "code": "코드",
    }

    out_tokens = []
    for tok in s.split(" "):
        key = tok.lower()
        if re.fullmatch(r"[A-Z0-9]{2,}", tok):
            out_tokens.append(tok)
            continue
        out_tokens.append(mapping.get(key, tok))
    return " ".join(out_tokens).strip()

def render_detail_page(entry: dict, lang: str) -> str:
    name_en = entry.get("name_en") or entry.get("name") or ""
    name_ko = entry.get("name_ko") or ""
    ko_policy = (entry.get("name_ko_policy") or "none").lower()

    # IMPORTANT:
    # - KO detail page should NOT mix EN+KO into one title string.
    # - EN detail page should NOT mix KO+EN into one title string.
    # We show the primary-language name as the title, and the other language as a small meta line.
    if lang == "ko":
        title_name = name_ko or name_en or entry.get("name") or ""
        if name_ko and ko_policy == "auto":
            subtitle_html = f"<div class='meta'>(자동번역) English: {esc(name_en)}</div>" if name_en else "<div class='meta'>(자동번역)</div>"
        else:
            subtitle_html = f"<div class='meta'>English: {esc(name_en)}</div>" if (name_en and title_name != name_en) else ""
        one_line = (
            entry.get("one_line_ko")
            or entry.get("one_line")
            or entry.get("description_ko")
            or entry.get("description")
            or entry.get("one_line_en")
            or ""
        )
    else:
        title_name = name_en or entry.get("name") or ""
        subtitle_html = f"<div class='meta'>Korean: {esc(name_ko)}</div>" if name_ko else ""
        one_line = (
            entry.get("one_line_en")
            or entry.get("one_line")
            or entry.get("description_en")
            or entry.get("description")
            or entry.get("one_line_ko")
            or ""
        )

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
        return "<ul>" + "\n".join(f"<li>{esc(x)}</li>" for x in items) + "</ul>"

    url_html = f"<a href='{esc(url)}' target='_blank' rel='noopener noreferrer'>{esc(url)}</a>" if url else "-"

    tistory_url = entry.get("tistory_url") or ""
    github_url = entry.get("github_url") or ""

    extra_links = []
    if tistory_url:
        extra_links.append(f"<a href='{esc(tistory_url)}' target='_blank' rel='noopener noreferrer'>티스토리 안내</a>")
    if github_url:
        extra_links.append(f"<a href='{esc(github_url)}' target='_blank' rel='noopener noreferrer'>GitHub 안내</a>")

    extra_links_html = " &nbsp;|&nbsp; ".join(extra_links) if extra_links else "-"

    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title_name)}</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; line-height: 1.5; }}
    .meta {{ color: #555; font-size: 14px; }}
    h1 {{ margin-bottom: 6px; }}
    h2 {{ margin-top: 22px; }}
    a {{ text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .topnav {{ margin-bottom: 12px; }}
  </style>
</head>
<body>
  <div class="topnav meta">
    <a href="../index.html">← GitHub 목록</a>
    &nbsp;|&nbsp;
    <a id="backToTistory" href="{esc(DEFAULT_TISTORY_LIST_URL)}">← 티스토리 목록</a>
  </div>

  <script>
    const p = new URLSearchParams(location.search);
    const back = p.get('back');
    if (back) document.getElementById('backToTistory').href = back;
  </script>

  <h1>{esc(title_name)}</h1>\n  {subtitle_html}
  <p>{esc(one_line)}</p>

  <h2>GPT 바로가기</h2>
  <p>{url_html}</p>

  <h2>External guides</h2>
  <p>{extra_links_html}</p>

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

def render_index(entries, lang: str, title: str, details_prefix: str, extra_link_html: str, tistory_list_url: str) -> str:
    li = []
    for idx, e in enumerate(entries, start=1):
        item_id = e["_id"]
        name_en = e.get("name_en") or e.get("name") or item_id
        name_ko = e.get("name_ko") or ""
        ko_policy = (e.get("name_ko_policy") or "none").lower()

        if name_ko:
            if ko_policy == "auto":
                display_name = f"{name_en} · (자동번역) {name_ko}"
            else:
                display_name = f"{name_en} · {name_ko}"
        else:
            display_name = name_en

        one = e.get(f"one_line_{lang}") or e.get("one_line") or e.get("one_line_ko") or e.get("one_line_en") or ""
        tags = " ".join(get_list(e, "tags"))
        detail_basename = sanitize_filename(f"{item_id}_{lang}.html")
        detail_href_base = f"{details_prefix}/{detail_basename}"
        back_q = urllib.parse.quote(tistory_list_url or "")
        detail_href = f"{detail_href_base}?back={back_q}" if back_q else detail_href_base

        gpt_url = e.get("url") or ""
        tistory_url = e.get("tistory_url") or ""
        github_url = e.get("github_url") or ""

        btns = []
        if gpt_url:
            btns.append(f"<a class='btn' href='{esc(gpt_url)}' target='_blank' rel='noopener noreferrer'>GPT 바로가기</a>")
        btns.append(f"<a class='btn' href='{detail_href}'>상세정보</a>")
        if tistory_url:
            btns.append(f"<a class='btn' href='{esc(tistory_url)}' target='_blank' rel='noopener noreferrer'>티스토리</a>")
        if github_url:
            btns.append(f"<a class='btn' href='{esc(github_url)}' target='_blank' rel='noopener noreferrer'>GitHub</a>")

        li.append(
            f"<li data-name='{esc(display_name)}' data-tags='{esc(tags)}' data-one='{esc(one)}'>"
            f"<div class='row'>"
            f"  <a class='titlelink' href='{detail_href}'><strong>{idx}. {esc(display_name)}</strong></a>"
            f"</div>"
            f"<div class='meta'>{esc(one)}</div>"
            f"<div class='btnbar'>{''.join(btns)}</div>"
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
    li {{ padding: 12px 0; border-bottom: 1px solid #eee; }}
    .meta {{ color: #555; font-size: 13px; margin-top: 4px; }}
    .topbar {{ display: flex; flex-wrap: wrap; gap: 10px; align-items: center; margin-bottom: 12px; }}
    .pill {{ font-size: 12px; color: #333; background: #f3f3f3; padding: 6px 10px; border-radius: 999px; text-decoration: none; }}
    .btnbar {{ margin-top: 8px; display: flex; flex-wrap: wrap; gap: 8px; }}
    .btn {{ display:inline-block; font-size: 12px; padding: 6px 10px; border-radius: 10px; background: #f6f6f6; color: #222; text-decoration: none; }}
    .btn:hover {{ background: #ededed; }}
    .titlelink {{ color: inherit; text-decoration: none; }}
    .titlelink:hover {{ text-decoration: underline; }}
  </style>
</head>
<body>
  <div class="topbar">
    <span class="pill">Total: {len(entries)}</span>
    {extra_link_html}
    <a class="pill" href="{esc(tistory_list_url)}" target="_blank" rel="noopener noreferrer">티스토리 목록</a>
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

def write_atlas_yaml(entries: list, out_path: str):
    items = []
    for e in entries:
        gpt_id = e.get("gpt_id") or e["_id"]
        name_en = e.get("name_en") or e.get("name") or ""
        if not gpt_id or not name_en or not e.get("url"):
            continue

        obj = {
            "gpt_id": gpt_id,
            "names": {"en": name_en},
            "url": e.get("url"),
        }

        name_ko = e.get("name_ko")
        ko_policy = (e.get("name_ko_policy") or "none").lower()
        if name_ko:
            obj["names"]["ko"] = name_ko
            obj["names"]["ko_policy"] = ko_policy

        summary = {}
        if e.get("one_line_en"):
            summary["en"] = e.get("one_line_en")
        if e.get("one_line_ko"):
            summary["ko"] = e.get("one_line_ko")
        if summary:
            obj["summary"] = summary

        tags = get_list(e, "tags")
        if tags:
            obj["tags"] = tags

        suitable_for = get_list(e, "target_users")
        if suitable_for:
            obj["suitable_for"] = suitable_for

        limitations = get_list(e, "limitations")
        if limitations:
            obj["limitations"] = limitations

        detail_pages = {}
        if e.get("tistory_url"):
            detail_pages["tistory"] = e.get("tistory_url")
        if e.get("github_url"):
            detail_pages["github"] = e.get("github_url")
        if detail_pages:
            obj["detail_pages"] = detail_pages

        items.append(obj)

    atlas = {
        "gpt_atlas": {
            "version": "1.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "items": items,
        }
    }

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        yaml.dump(atlas, f, allow_unicode=True, sort_keys=False)

def _assign_ids(entries: list):
    """Assign stable _id for each entry (per-language), and resolve collisions inside the list only."""
    for e in entries:
        gpt_id = e.get("gpt_id")
        base_name = e.get("name_en") or e.get("name") or e.get("name_ko") or e.get("_src_fn") or "item"
        raw_id = gpt_id if gpt_id else slugify(base_name)
        e["_slug"] = slugify(base_name)
        e["_id"] = sanitize_id(raw_id)

    # Collision resolve within the same language list only
    seen = {}
    for e in entries:
        base = e["_id"]
        n = seen.get(base, 0) + 1
        seen[base] = n
        if n > 1:
            e["_id"] = f"{base}-{n}"

def build():
    os.makedirs(DETAILS_KO_DIR, exist_ok=True)
    os.makedirs(DETAILS_EN_DIR, exist_ok=True)
    os.makedirs(EN_DIR, exist_ok=True)

    if not os.path.isdir(CATALOG_DIR):
        print(f"[WARN] catalog 폴더가 없음: {CATALOG_DIR}")
        return

    # ===== Build-stage split: load -> detect -> append =====
    ko_entries = []
    en_entries = []
    all_loaded = []  # for cross-language normalization (e.g., url->canonical name_en)

    for fn in sorted(os.listdir(CATALOG_DIR)):
        if not (fn.lower().endswith(".yaml") or fn.lower().endswith(".yml")):
            continue

        raw = load_yaml_safe(os.path.join(CATALOG_DIR, fn))
        if raw is None:
            continue

        entry = normalize_entry(raw)
        if not entry:
            continue

        entry["_src_fn"] = fn
        entry["_lang"] = guess_lang(entry, fn)

        # push immediately (no later content-based reclassification)
        if entry["_lang"] == "ko":
            ko_entries.append(entry)
        else:
            en_entries.append(entry)

        all_loaded.append(entry)

    # IDs: per-language (prevents ko/en cross-suffixing)
    _assign_ids(ko_entries)
    _assign_ids(en_entries)

    # URL -> canonical English name map (prefer true English name), using all loaded entries
    url_to_en = {}
    for e in all_loaded:
        url = (e.get("url") or "").strip()
        en = (e.get("name_en") or "").strip()
        if url and is_probably_english_name(en):
            url_to_en.setdefault(url, en)

    # restore name_en if it was (incorrectly) Korean-translated
    for e in all_loaded:
        url = (e.get("url") or "").strip()
        en = (e.get("name_en") or "").strip()
        if url and (not is_probably_english_name(en)) and (url in url_to_en):
            e["name_en"] = url_to_en[url]

    # ensure name_ko exists (auto translate if missing)
    for e in all_loaded:
        if not e.get("name_ko"):
            en = e.get("name_en") or e.get("name") or ""
            ko = auto_translate_name_ko(en)
            if ko:
                e["name_ko"] = ko
                e["name_ko_policy"] = "auto"
        else:
            if not e.get("name_ko_policy"):
                e["name_ko_policy"] = "human"

    def sort_key(e):
        return (str(e.get("name_en") or e.get("name") or e["_id"]).lower(),
                str(e.get("name_ko") or "").lower())

    ko_entries.sort(key=sort_key)
    en_entries.sort(key=sort_key)

    # Details
    for e in ko_entries:
        item_id = e["_id"]
        detail_basename = sanitize_filename(f"{item_id}_ko.html")
        with open(os.path.join(DETAILS_KO_DIR, detail_basename), "w", encoding="utf-8") as f:
            f.write(render_detail_page(e, "ko"))

    for e in en_entries:
        item_id = e["_id"]
        detail_basename = sanitize_filename(f"{item_id}_en.html")
        with open(os.path.join(DETAILS_EN_DIR, detail_basename), "w", encoding="utf-8") as f:
            f.write(render_detail_page(e, "en"))

    # Index (each language list only)
    ko_extra = "<a class='pill' href='en/index.html'>English</a>"
    en_extra = "<a class='pill' href='../index.html'>Korean</a>"

    with open(os.path.join(SITE_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(render_index(ko_entries, "ko", "GPT Catalog (KO)", "details", ko_extra, DEFAULT_TISTORY_LIST_URL))

    with open(os.path.join(EN_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(render_index(en_entries, "en", "GPT Catalog (EN)", "details", en_extra, DEFAULT_TISTORY_LIST_URL))

    # Atlas split (+ optional mixed)
    atlas_site_path = os.path.join(SITE_DIR, "atlas.yaml")          # mixed for compatibility
    atlas_ko_path = os.path.join(SITE_DIR, "atlas_ko.yaml")         # ko-only
    atlas_en_path = os.path.join(EN_DIR, "atlas_en.yaml")           # en-only

    write_atlas_yaml(ko_entries + en_entries, atlas_site_path)
    write_atlas_yaml(ko_entries, atlas_ko_path)
    write_atlas_yaml(en_entries, atlas_en_path)

    # Optional tistory copies
    if os.path.isdir(TISTORY_DIR):
        try:
            write_atlas_yaml(ko_entries + en_entries, os.path.join(TISTORY_DIR, "atlas.yaml"))
            write_atlas_yaml(ko_entries, os.path.join(TISTORY_DIR, "atlas_ko.yaml"))
            write_atlas_yaml(en_entries, os.path.join(TISTORY_DIR, "atlas_en.yaml"))
        except Exception:
            pass

    print(f"Loaded total: {len(ko_entries)+len(en_entries)}")
    print(f"KO entries : {len(ko_entries)} -> {os.path.join(SITE_DIR,'index.html')}")
    print(f"EN entries : {len(en_entries)} -> {os.path.join(EN_DIR,'index.html')}")
    print(f"Atlas (mix): {atlas_site_path}")
    print(f"Atlas (ko) : {atlas_ko_path}")
    print(f"Atlas (en) : {atlas_en_path}")

if __name__ == "__main__":
    build()
