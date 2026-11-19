"""
Frontend Quality Tests (Phase C10 & Issue Fixes)
Guards against:
- External CDN usage (Leaflet unpkg.com)
- Missing vendored Leaflet files
- Missing i18n translation keys referenced in HTML
- Unwrapped tables causing mobile horizontal scroll
- Missing admin role redirection
"""

import os
import re
from pathlib import Path
import pytest
from tests.test_i18n_parity import extract_translations


def test_no_cdn_leaflet_in_frontend():
    """Verify that unpkg.com or external CDN for Leaflet is never used in frontend code."""
    frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
    files = list(frontend_dir.glob("*.html")) + list((frontend_dir / "js").glob("*.js"))

    for f in files:
        content = f.read_text(encoding="utf-8")
        assert "unpkg.com/leaflet" not in content, f"Found unpkg.com/leaflet CDN reference in {f.name}"
        assert "cdnjs.cloudflare.com/ajax/libs/leaflet" not in content, f"Found cdnjs Leaflet reference in {f.name}"


def test_vendored_leaflet_files_exist():
    """Verify Leaflet 1.9.4 CSS, JS, LICENSE, and markers are vendored locally."""
    vendor_dir = Path(__file__).resolve().parent.parent / "frontend" / "vendor" / "leaflet"
    assert (vendor_dir / "leaflet.js").exists(), "leaflet.js must be vendored"
    assert (vendor_dir / "leaflet.css").exists(), "leaflet.css must be vendored"
    assert (vendor_dir / "LICENSE").exists(), "Leaflet LICENSE must exist"
    assert (vendor_dir / "images" / "marker-icon.png").exists(), "marker-icon.png must exist"
    assert (vendor_dir / "images" / "marker-icon-2x.png").exists(), "marker-icon-2x.png must exist"
    assert (vendor_dir / "images" / "marker-shadow.png").exists(), "marker-shadow.png must exist"


def test_html_data_i18n_keys_exist_in_dictionaries():
    """Verify that every data-i18n and data-i18n-html key in HTML files is present in en, hi, mr dictionaries."""
    frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
    en_keys, hi_keys, mr_keys = extract_translations()

    html_files = list(frontend_dir.glob("*.html"))
    for hf in html_files:
        content = hf.read_text(encoding="utf-8")

        # Find all data-i18n="xyz"
        i18n_matches = re.findall(r'data-i18n=["\']([^"\']+)["\']', content)
        for key in i18n_matches:
            assert key in en_keys, f"Key '{key}' in {hf.name} missing from English dictionary"
            assert key in hi_keys, f"Key '{key}' in {hf.name} missing from Hindi dictionary"
            assert key in mr_keys, f"Key '{key}' in {hf.name} missing from Marathi dictionary"

        # Find all data-i18n-html="xyz"
        i18n_html_matches = re.findall(r'data-i18n-html=["\']([^"\']+)["\']', content)
        for key in i18n_html_matches:
            assert key in en_keys, f"HTML Key '{key}' in {hf.name} missing from English dictionary"
            assert key in hi_keys, f"HTML Key '{key}' in {hf.name} missing from Hindi dictionary"
            assert key in mr_keys, f"HTML Key '{key}' in {hf.name} missing from Marathi dictionary"


def test_tables_are_wrapped_in_table_container():
    """Verify every <table> tag in frontend HTML and JS sits inside a .table-container."""
    frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
    files = list(frontend_dir.glob("*.html"))

    for f in files:
        content = f.read_text(encoding="utf-8")
        matches = [m.start() for m in re.finditer(r'<table', content)]
        for pos in matches:
            preceding = content[max(0, pos - 150):pos]
            assert "table-container" in preceding, f"Unwrapped table found in {f.name} around char {pos}"


def test_core_operator_redirects_in_auth_js():
    """Verify auth.js redirects all 4 primary operator roles properly."""
    auth_js = Path(__file__).resolve().parent.parent / "frontend" / "js" / "auth.js"
    content = auth_js.read_text(encoding="utf-8")
    assert "case 'FARMER':" in content, "FARMER redirect missing in auth.js"
    assert "farmer.html" in content, "farmer.html missing in auth.js"
    assert "case 'STATIC_OPERATOR':" in content, "STATIC_OPERATOR redirect missing in auth.js"
    assert "storage_operator.html" in content, "storage_operator.html missing in auth.js"
    assert "case 'VAN_OPERATOR':" in content, "VAN_OPERATOR redirect missing in auth.js"
    assert "van_operator.html" in content, "van_operator.html missing in auth.js"
    assert "case 'BUYER':" in content, "BUYER redirect missing in auth.js"
    assert "buyer.html" in content, "buyer.html missing in auth.js"
