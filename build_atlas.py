 import os
import yaml
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CATALOG_DIR = os.path.join(BASE_DIR, "catalog")
TISTORY_DIR = os.path.join(BASE_DIR, "tistory")
OUT_PATH = os.path.join(TISTORY_DIR, "atlas.yaml")

os.makedirs(TISTORY_DIR, exist_ok=True)

def load_yaml(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception:
        return None

def normalize_entry(raw: dict):
    if not isinstance(raw, dict):
        return None
    if "catalog_entry" in raw:
        return raw["catalog_entry"]
    return raw

atlas_items = []

for fn in sorted(os.listdir(CATALOG_DIR)):
    if not fn.endswith(".yaml"):
        continue

    raw = load_yaml(os.path.join(CATALOG_DIR, fn))
    entry = normalize_entry(raw)
    if not entry:
        continue

    gpt_id = entry.get("gpt_id")
    name_en = entry.get("name_en")
    url = entry.get("url")

    # 필수 필드 검증 (Atlas는 불완전 항목 무시)
    if not gpt_id or not name_en or not url:
        continue

    item = {
        "gpt_id": gpt_id,
        "names": {
            "en": name_en
        },
        "url": url
    }

    # 한국어 이름
    name_ko = entry.get("name_ko")
    ko_policy = entry.get("name_ko_policy", "none")

    if name_ko:
        item["names"]["ko"] = name_ko
        item["names"]["ko_policy"] = ko_policy

    # 요약
    summary = {}
    if entry.get("one_line_en"):
        summary["en"] = entry["one_line_en"]
    if entry.get("one_line_ko"):
        summary["ko"] = entry["one_line_ko"]
    if summary:
        item["summary"] = summary

    # 태그 / 대상
    for key_src, key_dst in [
        ("tags", "tags"),
        ("target_users", "suitable_for"),
        ("limitations", "limitations")
    ]:
        val = entry.get(key_src)
        if isinstance(val, list) and val:
            item[key_dst] = val

    # 외부 안내 페이지 (있을 때만)
    detail_pages = {}
    if entry.get("tistory_url"):
        detail_pages["tistory"] = entry["tistory_url"]
    if entry.get("github_url"):
        detail_pages["github"] = entry["github_url"]

    if detail_pages:
        item["detail_pages"] = detail_pages

    atlas_items.append(item)

atlas = {
    "gpt_atlas": {
        "version": "1.0",
        "generated_at": datetime.utcnow().isoformat(),
        "items": atlas_items
    }
}

with open(OUT_PATH, "w", encoding="utf-8") as f:
    yaml.dump(atlas, f, allow_unicode=True, sort_keys=False)

print(f"[OK] atlas.yaml generated: {OUT_PATH}")
print(f"[OK] items: {len(atlas_items)}")
