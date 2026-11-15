import os
from pathlib import Path

def test_frontend_does_not_handle_jwt_tokens():
    """
    Verify security rule:
    JavaScript must NEVER read, store or manually attach the JWT:
    no localStorage, no sessionStorage, no JS variable token storage, no Authorization header.
    Session is managed exclusively by the backend via HttpOnly cookies.
    """
    frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
    assert frontend_dir.exists(), "frontend directory must exist"

    files_to_check = list(frontend_dir.rglob("*.js")) + list(frontend_dir.rglob("*.html"))
    assert len(files_to_check) > 0, "There should be frontend files to check"

    forbidden_patterns = [
        "localStorage.getItem('token'",
        "localStorage.setItem('token'",
        "localStorage.getItem('access_token'",
        "localStorage.setItem('access_token'",
        "sessionStorage.getItem('token'",
        "sessionStorage.setItem('token'",
        "sessionStorage.getItem('access_token'",
        "sessionStorage.setItem('access_token'",
        "Bearer ",
        "'Authorization'",
        '"Authorization"',
    ]

    for file_path in files_to_check:
        content = file_path.read_text(encoding="utf-8")
        for pattern in forbidden_patterns:
            assert pattern not in content, (
                f"Security violation in {file_path.name}: "
                f"Forbidden token handling pattern '{pattern}' found."
            )
