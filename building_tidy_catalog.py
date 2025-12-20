import os
import re
import csv
import yaml

# ========= CONFIG =========
CATALOG_DIR = "./catalog"          # folder with renamed YAML files
OUTPUT_FILE = "gpt_catalog_tidy.csv"
# ==========================

FILENAME_PATTERN = re.compile(
    r"^(?P<gpt_id>.+?)__(?P<lang>en|ko)__(?P<date>\d{4}-\d{2}-\d{2})\.ya?ml$",
    re.IGNORECASE
)

def as_list(x):
    if x is None:
        return []
    if isinstance(x, list):
        return [str(i).strip() for i in x if str(i).strip()]
    return [str(x).strip()]

def load_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def main():
    rows = []

    for fname in os.listdir(CATALOG_DIR):
        if not fname.lower().endswith((".yaml", ".yml")):
            continue

        m = FILENAME_PATTERN.match(fname)
        if not m:
            print(f"[SKIP] Filename does not match contract: {fname}")
            continue

        gpt_id = m.group("gpt_id")
        language = m.group("lang")
        version = m.group("date")

        path = os.path.join(CATALOG_DIR, fname)
        data = load_yaml(path)

        row = {
            "gpt_id": gpt_id,
            "language": language,
            "version": version,
            "name": data.get("name", ""),
            "tags": "|".join(as_list(data.get("tags"))),
            "intro": data.get("intro", "") or data.get("description", ""),
            "functions": "|".join(as_list(data.get("functions"))),
            "limitations": "|".join(as_list(data.get("limitations"))),
            "source_file": fname,
        }

        rows.append(row)

    if not rows:
        raise RuntimeError("No valid YAML files processed. Check filenames and folder.")

    fieldnames = list(rows[0].keys())

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"[DONE] Tidy file written: {OUTPUT_FILE}")
    print(f"[INFO] Rows: {len(rows)}")

if __name__ == "__main__":
    main()
