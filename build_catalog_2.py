#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
build_catalog_ko_en.py

국문 카탈로그와 영문 카탈로그를 각각 따로 병합하여
- Gpt catalog_ko.yaml
- Gpt catalog_en.yaml
두 개의 병합본을 생성한다.

원본 build_catalog.py 로직을 기반으로 하되,
언어 구분 및 병합 분리를 위해 구조를 확장했다.
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime

try:
    import yaml
except ImportError:
    print("PyYAML이 필요합니다. 먼저 `pip install pyyaml` 을 실행하세요.", file=sys.stderr)
    sys.exit(1)


REQUIRED_FIELDS = [
    "gpt_id",
    "name",
    "url",
    "version",
    "last_updated",
    "one_line",
    "functions",
]

RECOMMENDED_FIELDS = [
    "alias",
    "tags",
    "target_users",
    "ideal_use_cases",
    "limitations",
    "example_commands",
    "additional_features",
]

# 파일명에 포함된 토큰으로 언어를 추론한다.
LANG_GROUPS = {
    "ko": ["_ko", "_kor"],
    "en": ["_en", "_eng"],
}


def detect_language(filename: str):
    """파일명 기반으로 언어코드를 추론한다."""
    lower = filename.lower()
    for lang, tokens in LANG_GROUPS.items():
        for tok in tokens:
            if tok in lower:
                return lang
    return None


def find_catalog_files(catalog_dir: Path):
    """catalog 디렉토리 안의 .yaml/.yml 파일 리스트를 반환.
    템플릿 파일(예: template 포함)은 자동 무시.
    """
    if not catalog_dir.exists():
        raise FileNotFoundError(f"catalog 디렉토리가 없습니다: {catalog_dir}")

    files = []
    for p in sorted(catalog_dir.iterdir()):
        if p.suffix.lower() not in {".yaml", ".yml"}:
            continue
        if "template" in p.name.lower():
            continue
        files.append(p)
    return files


def normalize_entries(data, source_file: Path):
    """
    개별 YAML 파일의 내용(data)을 '엔트리(dict)들의 리스트'로 정규화.

    허용 형태:
      - 리스트: [ {gpt_id: ...}, {gpt_id: ...}, ... ]
      - 딕셔너리 1개: {gpt_id: ..., ...}
      - 템플릿 스타일: {catalog_template: {gpt_block: {...}} } → 무시
    """
    if data is None:
        return []

    if isinstance(data, dict) and "catalog_template" in data:
        # 템플릿 구조는 무시
        return []

    if isinstance(data, list):
        entries = data
    elif isinstance(data, dict):
        if "gpt_block" in data and isinstance(data["gpt_block"], dict):
            entries = [data["gpt_block"]]
        else:
            entries = [data]
    else:
        print(f"[경고] {source_file} : YAML 최상위 타입이 dict/list 아님 → 무시", file=sys.stderr)
        return []

    normalized = []
    for idx, e in enumerate(entries):
        if isinstance(e, dict):
            normalized.append(e)
        else:
            print(
                f"[경고] {source_file} : 리스트 내 {idx}번째 항목이 dict가 아님({type(e)}), 무시함",
                file=sys.stderr,
            )
    return normalized


def validate_entry(entry: dict, source_file: Path) -> bool:
    """하나의 GPT 엔트리가 최소 요건을 만족하는지 검사."""
    missing_required = [f for f in REQUIRED_FIELDS if f not in entry or entry.get(f) in (None, "")]
    missing_recommended = [f for f in RECOMMENDED_FIELDS if f not in entry or entry.get(f) in (None, "", [])]

    is_valid = len(missing_required) == 0

    if not is_valid:
        print(
            f"[에러] {source_file} 의 gpt_id='{entry.get('gpt_id')}' 엔트리에 "
            f"필수 필드 누락: {missing_required}",
            file=sys.stderr,
        )
    elif missing_recommended:
        print(
            f"[주의] {source_file} 의 gpt_id='{entry.get('gpt_id')}' 엔트리에 "
            f"권장 필드 누락: {missing_recommended}",
            file=sys.stderr,
        )

    # last_updated 형식 체크(YYYY-MM-DD)
    lu = entry.get("last_updated")
    if lu:
        try:
            datetime.strptime(lu, "%Y-%m-%d")
        except ValueError:
            print(
                f"[주의] {source_file} 의 gpt_id='{entry.get('gpt_id')}' : "
                f"last_updated 형식이 'YYYY-MM-DD'가 아님: {lu}",
                file=sys.stderr,
            )

    return is_valid


def merge_language_catalog(lang_code: str, files, base_dir: Path):
    """특정 언어 그룹에 속하는 파일들을 병합하여 Gpt catalog_{lang}.yaml 생성."""
    if not files:
        print(f"[정보] 언어 '{lang_code}' 에 해당하는 카탈로그 파일이 없습니다.")
        return

    merged_by_id = {}

    for f in files:
        try:
            text = f.read_text(encoding="utf-8")
            data = yaml.safe_load(text)
        except Exception as e:
            print(f"[에러] {f} 읽기/파싱 실패: {e}", file=sys.stderr)
            continue

        entries = normalize_entries(data, f)
        if not entries:
            continue

        for entry in entries:
            if not validate_entry(entry, f):
                continue
            gid = entry.get("gpt_id")
            if not gid:
                continue
            if gid in merged_by_id:
                print(
                    f"[주의] {f} : gpt_id '{gid}' 가 이미 존재합니다. "
                    f"이 엔트리가 이전 것을 덮어씁니다.",
                    file=sys.stderr,
                )
            merged_by_id[gid] = entry

    out_path = base_dir / f"Gpt catalog_{lang_code}.yaml"
    with out_path.open("w", encoding="utf-8") as fw:
        yaml.safe_dump(
            list(merged_by_id.values()),
            fw,
            allow_unicode=True,
            sort_keys=False,
            width=120,
        )
    print(f"[완료] 언어 '{lang_code}' 병합 카탈로그를 생성했습니다: {out_path}")
    print(f"        총 엔트리 수: {len(merged_by_id)}")


def main():
    parser = argparse.ArgumentParser(
        description=(
            "catalog/ 폴더의 GPT 카탈로그들을 읽어 "
            "국문(Gpt catalog_ko.yaml)과 영문(Gpt catalog_en.yaml) 병합본을 각각 생성합니다."
        )
    )
    parser.add_argument(
        "--base-dir",
        type=str,
        required=True,
        help="이 스크립트와 catalog/ 폴더가 위치한 기준 경로. 예: C:\\Users\\me\\Dropbox\\CustomGPT\\1GPT_Catalog",
    )

    args = parser.parse_args()
    base_dir = Path(args.base_dir).expanduser().resolve()
    catalog_dir = base_dir / "catalog"

    try:
        all_files = find_catalog_files(catalog_dir)
    except FileNotFoundError as e:
        print(f"[에러] {e}", file=sys.stderr)
        sys.exit(1)

    lang_files = {"ko": [], "en": []}
    for f in all_files:
        lang = detect_language(f.name)
        if lang in lang_files:
            lang_files[lang].append(f)
        else:
        # 언어를 판별할 수 없는 파일은 경고만 출력하고 병합에서 제외
            print(f"[주의] 언어를 판별할 수 없어 건너뜀: {f.name}", file=sys.stderr)

    merge_language_catalog("ko", lang_files["ko"], base_dir)
    merge_language_catalog("en", lang_files["en"], base_dir)


if __name__ == "__main__":
    main()
