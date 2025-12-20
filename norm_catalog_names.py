import os
import re
from datetime import datetime

# ===== CONFIG =====
CATALOG_DIR = "./catalog"   # <-- change if needed
DRY_RUN = False                  # set False to actually rename files
# ==================

LANG_MAP = {
    "en": "en",
    "ko": "ko",
    "kr": "ko",
    "kor": "ko",
}

LANG_PATTERN = re.compile(r"(?:_|-)(en|ko|kr|kor)(?:\.ya?ml)?$", re.IGNORECASE)
DATE_PATTERN = re.compile(r"(20\d{2})[-_](\d{2})[-_](\d{2})")

def normalize_slug(text: str) -> str:
    text = text.lower()
    text = text.replace("&", " ")
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"[\s\-]+", "_", text)
    text = re.sub(r"_+", "_", text)
    return text.strip("_")

def normalize_date(text: str) -> str | None:
    m = DATE_PATTERN.search(text)
    if not m:
        return None
    y, mth, d = m.groups()
    try:
        return datetime(int(y), int(mth), int(d)).strftime("%Y-%m-%d")
    except ValueError:
        return None

def extract_language(fname: str) -> str | None:
    m = LANG_PATTERN.search(fname)
    if not m:
        return None
    return LANG_MAP[m.group(1).lower()]

def normalize_filenames():
    for fname in os.listdir(CATALOG_DIR):
        if not fname.lower().endswith((".yaml", ".yml")):
            continue

        old_path = os.path.join(CATALOG_DIR, fname)

        lang = extract_language(fname)
        if not lang:
            print(f"[SKIP] No language suffix: {fname}")
            continue

        date = normalize_date(fname)
        if not date:
            print(f"[SKIP] No valid date: {fname}")
            continue

        # remove language + date from base
        base = fname
        base = LANG_PATTERN.sub("", base)
        base = DATE_PATTERN.sub("", base)
        base = base.replace(".yaml", "").replace(".yml", "")

        slug = normalize_slug(base)

        new_fname = f"{slug}__{lang}__{date}.yaml"
        new_path = os.path.join(CATALOG_DIR, new_fname)

        if fname == new_fname:
            print(f"[OK] Already normalized: {fname}")
            continue

        if os.path.exists(new_path):
            print(f"[CONFLICT] Target exists: {new_fname}")
            continue

        print(f"[RENAME] {fname} → {new_fname}")
        if not DRY_RUN:
            os.rename(old_path, new_path)

if __name__ == "__main__":
    normalize_filenames()
