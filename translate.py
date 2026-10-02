#!/usr/bin/env python3
"""
NaviTools i18n maintenance script.

Usage:
  python3 translate.py              # translate all missing keys in all target languages
  python3 translate.py --lang es    # only translate missing keys for Spanish
  python3 translate.py --force      # re-translate ALL keys (overwrites existing)

Workflow when adding new content:
  1. Add the new element to index.html with a data-i18n="your.new_key" attribute.
  2. Add "your.new_key": "English text" to lang/en.json.
  3. Run: python3 translate.py
  4. New keys are automatically translated and added to es.json and fr.json.

Translation API: MyMemory (free, no API key required, 5000 chars/day/IP).
If you need higher volume, sign up at mymemory.translated.net and pass your email
with --email your@email.com to raise the daily limit to 10000 chars.
"""

import json
import time
import urllib.request
import urllib.parse
import argparse
import sys
from pathlib import Path

LANG_DIR = Path(__file__).parent / "lang"
SOURCE_LANG = "en"
TARGET_LANGS = {"es": "Spanish", "fr": "French"}

MYMEMORY_URL = "https://api.mymemory.translated.net/get"


def load_json(path: Path) -> dict:
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_json(path: Path, data: dict):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  Saved {path.name}")


def translate(text: str, target_lang: str, email: str = "") -> str:
    """Translate a single string via MyMemory API."""
    params = {
        "q": text,
        "langpair": f"{SOURCE_LANG}|{target_lang}",
    }
    if email:
        params["de"] = email

    url = MYMEMORY_URL + "?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("responseStatus") == 200:
                translated = data["responseData"]["translatedText"]
                # MyMemory returns QUERY LIMIT REACHED when exhausted
                if "QUERY LIMIT" in translated.upper():
                    print(f"  ⚠  Daily translation limit reached. Stopping.")
                    sys.exit(1)
                return translated
            else:
                print(f"  ⚠  API error for key (status {data.get('responseStatus')}): {text[:60]}")
                return text
    except Exception as e:
        print(f"  ⚠  Request failed: {e}")
        return text


def translate_lang(target_lang: str, source: dict, existing: dict, force: bool, email: str) -> dict:
    """Return updated translation dict with all missing (or all if force) keys filled."""
    updated = dict(existing)
    keys_to_translate = [k for k in source if force or k not in existing]

    if not keys_to_translate:
        print(f"  [{target_lang}] All {len(source)} keys already present. Nothing to do.")
        return updated

    print(f"  [{target_lang}] Translating {len(keys_to_translate)} key(s)...")
    for i, key in enumerate(keys_to_translate, 1):
        value = source[key]
        translated = translate(value, target_lang, email)
        updated[key] = translated
        print(f"    ({i}/{len(keys_to_translate)}) {key}")
        # Respect MyMemory rate limit — 1 req/sec recommended
        if i < len(keys_to_translate):
            time.sleep(1.1)

    # Preserve key order from source (new keys appended at end)
    ordered = {k: updated[k] for k in source if k in updated}
    return ordered


def main():
    parser = argparse.ArgumentParser(description="Auto-translate NaviTools i18n files.")
    parser.add_argument("--lang", help="Only translate this target language code (e.g. es, fr)")
    parser.add_argument("--force", action="store_true", help="Re-translate all keys, overwriting existing")
    parser.add_argument("--email", default="", help="MyMemory registered email for higher rate limit")
    args = parser.parse_args()

    source_path = LANG_DIR / f"{SOURCE_LANG}.json"
    if not source_path.exists():
        print(f"ERROR: Source file not found: {source_path}")
        sys.exit(1)

    source = load_json(source_path)
    print(f"Source ({SOURCE_LANG}): {len(source)} keys loaded from {source_path.name}")

    targets = TARGET_LANGS
    if args.lang:
        if args.lang not in TARGET_LANGS:
            print(f"ERROR: Unknown language '{args.lang}'. Available: {', '.join(TARGET_LANGS)}")
            sys.exit(1)
        targets = {args.lang: TARGET_LANGS[args.lang]}

    for lang_code, lang_name in targets.items():
        print(f"\n── {lang_name} ({lang_code}) ──")
        target_path = LANG_DIR / f"{lang_code}.json"
        existing = load_json(target_path)
        updated = translate_lang(lang_code, source, existing, args.force, args.email)
        save_json(target_path, updated)

    print("\nDone.")


if __name__ == "__main__":
    main()
