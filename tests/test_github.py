import pytest
from app.utils.hashing import url_to_repo_id


def test_url_to_repo_id_is_stable():
    url = "https://github.com/tiangolo/fastapi"
    assert url_to_repo_id(url) == url_to_repo_id(url)


def test_url_to_repo_id_is_12_chars():
    result = url_to_repo_id("https://github.com/test/repo")
    assert len(result) == 12


def test_url_to_repo_id_differs_by_repo():
    a = url_to_repo_id("https://github.com/user/repo-a")
    b = url_to_repo_id("https://github.com/user/repo-b")
    assert a != b


def test_url_to_repo_id_trailing_slash_normalized():
    a = url_to_repo_id("https://github.com/user/repo")
    b = url_to_repo_id("https://github.com/user/repo/")
    assert a == b
