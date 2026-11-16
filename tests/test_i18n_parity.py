"""
Test for i18n Dictionary Parity & Localization Completeness (Phase C9).
Ensures that all keys defined in English (en) also exist in Hindi (hi) and Marathi (mr).
"""

import re
import os
import json
import pytest

def extract_translations():
    i18n_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "js", "i18n.js")
    with open(i18n_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Regex extract dictionary objects for en, hi, mr
    # Find matching block for translations = { ... }
    en_block = re.search(r"en:\s*\{(.*?)\n\s*\},", content, re.DOTALL)
    hi_block = re.search(r"hi:\s*\{(.*?)\n\s*\},", content, re.DOTALL)
    mr_block = re.search(r"mr:\s*\{(.*?)\n\s*\}\n\};", content, re.DOTALL)

    assert en_block is not None, "Failed to parse 'en' block from i18n.js"
    assert hi_block is not None, "Failed to parse 'hi' block from i18n.js"
    assert mr_block is not None, "Failed to parse 'mr' block from i18n.js"

    def parse_keys(block_text):
        keys = {}
        for line in block_text.splitlines():
            line = line.strip()
            if not line or line.startswith("//"):
                continue
            match = re.match(r"^([a-zA-Z0-9_]+)\s*:\s*(.+?),?$", line)
            if match:
                key = match.group(1)
                val = match.group(2).rstrip(",")
                keys[key] = val
        return keys

    en_keys = parse_keys(en_block.group(1))
    hi_keys = parse_keys(hi_block.group(1))
    mr_keys = parse_keys(mr_block.group(1))

    return en_keys, hi_keys, mr_keys


def test_i18n_parity_between_languages():
    """
    Verify complete dictionary parity:
    Every translation key present in English must also exist in Hindi and Marathi.
    """
    en_keys, hi_keys, mr_keys = extract_translations()

    assert len(en_keys) > 0, "English translations dictionary is empty"

    missing_in_hi = set(en_keys.keys()) - set(hi_keys.keys())
    missing_in_mr = set(en_keys.keys()) - set(mr_keys.keys())

    assert not missing_in_hi, f"Keys present in English but missing in Hindi: {sorted(list(missing_in_hi))}"
    assert not missing_in_mr, f"Keys present in English but missing in Marathi: {sorted(list(missing_in_mr))}"

    # Verify no empty values
    for k, v in en_keys.items():
        assert v.strip() not in ['""', "''"], f"Empty value for English key: {k}"
    for k, v in hi_keys.items():
        assert v.strip() not in ['""', "''"], f"Empty value for Hindi key: {k}"
    for k, v in mr_keys.items():
        assert v.strip() not in ['""', "''"], f"Empty value for Marathi key: {k}"


def test_i18n_review_disclaimer_present():
    """
    Verify machine-written translations are marked 'needs native-speaker review'.
    """
    i18n_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "js", "i18n.js")
    with open(i18n_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "needs native-speaker review" in content
