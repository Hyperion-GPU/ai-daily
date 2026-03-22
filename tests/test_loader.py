import json

from src.server import loader


def test_list_dates_ignores_non_digest_json(tmp_path, monkeypatch):
    monkeypatch.setattr(loader, "OUTPUT_DIR", tmp_path)
    (tmp_path / "2026-03-14.json").write_text("{}", encoding="utf-8")
    (tmp_path / "index.json").write_text("[]", encoding="utf-8")
    (tmp_path / "notes.json").write_text("{}", encoding="utf-8")

    result = loader.list_dates()

    assert result == ["2026-03-14"]


def test_load_index_returns_none_for_invalid_payload(tmp_path, monkeypatch):
    index_path = tmp_path / "index.json"
    index_path.write_text(json.dumps({"date": "2026-03-14"}), encoding="utf-8")
    monkeypatch.setattr(loader, "INDEX_PATH", index_path)
    loader._load_index.cache_clear()

    result = loader.load_index()

    assert result is None


def test_list_github_dates_reads_trending_snapshots(tmp_path, monkeypatch):
    github_dir = tmp_path / "github"
    github_dir.mkdir()
    (github_dir / "trending-2026-03-16.json").write_text("{}", encoding="utf-8")
    (github_dir / "trending-2026-03-14.json").write_text("{}", encoding="utf-8")
    (github_dir / "notes.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(loader, "GITHUB_OUTPUT_DIR", github_dir)

    result = loader.list_github_dates()

    assert result == ["2026-03-16", "2026-03-14"]


def test_load_github_trending_returns_none_for_bad_json(tmp_path, monkeypatch):
    github_dir = tmp_path / "github"
    github_dir.mkdir()
    bad_path = github_dir / "trending-2026-03-16.json"
    bad_path.write_text("{bad json", encoding="utf-8")
    monkeypatch.setattr(loader, "GITHUB_OUTPUT_DIR", github_dir)
    loader._load_github_json.cache_clear()

    result = loader.load_github_trending("2026-03-16")

    assert result is None
