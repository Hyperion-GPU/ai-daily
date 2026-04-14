import os
from types import SimpleNamespace

from src.runtime import get_runtime_paths, sync_web_data_to_desktop
from src import settings


def test_get_runtime_paths_uses_writable_root_for_relative_output_dir(monkeypatch, tmp_path):
    monkeypatch.setenv("AI_DAILY_DESKTOP_MODE", "1")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))

    paths = get_runtime_paths(config={"outputs": {"output_dir": "output"}}, mode="desktop")

    assert paths.output_dir == tmp_path / "AI Daily" / "output"
    assert paths.state_file == tmp_path / "AI Daily" / "data" / "state.json"


def test_save_config_strips_runtime_metadata(tmp_path):
    config_path = tmp_path / "config.yaml"

    saved_path = settings.save_config(
        {
            "timezone": "Asia/Shanghai",
            "outputs": {"output_dir": "output"},
            "_runtime": {"mode": "desktop"},
        },
        config_path=config_path,
        mode="web",
    )

    text = saved_path.read_text(encoding="utf-8")
    assert "_runtime" not in text
    assert "timezone: Asia/Shanghai" in text


def test_get_llm_api_key_falls_back_to_keyring(monkeypatch):
    monkeypatch.delenv("SILICONFLOW_API_KEY", raising=False)
    monkeypatch.setattr(settings, "load_runtime_env", lambda config=None, mode=None: None)
    monkeypatch.setattr(
        settings,
        "keyring",
        SimpleNamespace(get_password=lambda service, username: "from-keyring"),
    )

    config = {
        "llm": {
            "provider": "siliconflow",
            "siliconflow": {
                "api_key_env": "SILICONFLOW_API_KEY",
            },
        }
    }

    assert settings.get_llm_api_key(config) == "from-keyring"


def test_load_config_uses_cached_file_payload(monkeypatch, tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text("timezone: UTC\n", encoding="utf-8")

    call_count = {"count": 0}
    real_safe_load = settings.yaml.safe_load

    def counted_safe_load(stream):
        call_count["count"] += 1
        return real_safe_load(stream)

    monkeypatch.setattr(settings.yaml, "safe_load", counted_safe_load)
    settings._load_config_payload.cache_clear()

    first = settings.load_config(config_path=config_path, mode="web")
    second = settings.load_config(config_path=config_path, mode="web")

    assert call_count["count"] == 1
    assert first["timezone"] == "UTC"
    assert second["timezone"] == "UTC"
    assert first is not second


def test_sync_web_data_to_desktop_copies_repo_archives(monkeypatch, tmp_path):
    repo_root = tmp_path / "repo"
    bundle_root = repo_root
    output_dir = repo_root / "output"
    github_dir = output_dir / "github"
    data_dir = repo_root / "data"
    output_dir.mkdir(parents=True)
    github_dir.mkdir(parents=True)
    data_dir.mkdir(parents=True)

    (output_dir / "2026-04-08.json").write_text('{"date":"2026-04-08"}', encoding="utf-8")
    (output_dir / "2026-04-08.md").write_text("# report", encoding="utf-8")
    (output_dir / "index.json").write_text("[]", encoding="utf-8")
    (github_dir / "trending-2026-04-08.json").write_text('{"date":"2026-04-08","projects":[]}', encoding="utf-8")
    (output_dir / "2026-04-08.partial.json").write_text("{}", encoding="utf-8")
    (data_dir / "state.json").write_text('{"seen_urls":["a"]}', encoding="utf-8")

    monkeypatch.setenv("AI_DAILY_DESKTOP_MODE", "1")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "localappdata"))
    monkeypatch.setattr("src.runtime._repo_root", lambda: repo_root)
    monkeypatch.setattr("src.runtime._bundle_root", lambda: bundle_root)

    report = sync_web_data_to_desktop(config={"outputs": {"output_dir": "output"}})
    desktop_root = tmp_path / "localappdata" / "AI Daily"

    assert report["copied_files"] == 4
    assert report["state_copied"] == 1
    assert (desktop_root / "output" / "2026-04-08.json").exists()
    assert (desktop_root / "output" / "2026-04-08.md").exists()
    assert (desktop_root / "output" / "index.json").exists()
    assert (desktop_root / "output" / "github" / "trending-2026-04-08.json").exists()
    assert not (desktop_root / "output" / "2026-04-08.partial.json").exists()
    assert (desktop_root / "data" / "state.json").exists()


def test_sync_web_data_to_desktop_keeps_newer_desktop_file(monkeypatch, tmp_path):
    repo_root = tmp_path / "repo"
    bundle_root = repo_root
    output_dir = repo_root / "output"
    output_dir.mkdir(parents=True)

    source = output_dir / "index.json"
    source.write_text('["repo"]', encoding="utf-8")

    desktop_root = tmp_path / "localappdata" / "AI Daily"
    desktop_output = desktop_root / "output"
    desktop_output.mkdir(parents=True)
    target = desktop_output / "index.json"
    target.write_text('["desktop"]', encoding="utf-8")

    now = 1_700_000_000
    os.utime(source, (now, now))
    os.utime(target, (now + 30, now + 30))

    monkeypatch.setenv("AI_DAILY_DESKTOP_MODE", "1")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "localappdata"))
    monkeypatch.setattr("src.runtime._repo_root", lambda: repo_root)
    monkeypatch.setattr("src.runtime._bundle_root", lambda: bundle_root)

    report = sync_web_data_to_desktop(config={"outputs": {"output_dir": "output"}})

    assert report["copied_files"] == 0
    assert target.read_text(encoding="utf-8") == '["desktop"]'


def test_sync_web_data_to_desktop_respects_configured_web_output_dir(monkeypatch, tmp_path):
    repo_root = tmp_path / "repo"
    bundle_root = repo_root
    configured_output = repo_root / "custom-output"
    default_output = repo_root / "output"
    data_dir = repo_root / "data"
    configured_output.mkdir(parents=True)
    default_output.mkdir(parents=True)
    data_dir.mkdir(parents=True)

    (configured_output / "2026-04-09.json").write_text('{"date":"2026-04-09"}', encoding="utf-8")
    (default_output / "ignored.json").write_text('{"date":"ignored"}', encoding="utf-8")
    (data_dir / "state.json").write_text('{"seen_urls":["a"]}', encoding="utf-8")

    monkeypatch.setenv("AI_DAILY_DESKTOP_MODE", "1")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "localappdata"))
    monkeypatch.setattr("src.runtime._repo_root", lambda: repo_root)
    monkeypatch.setattr("src.runtime._bundle_root", lambda: bundle_root)

    report = sync_web_data_to_desktop(config={"outputs": {"output_dir": "custom-output"}})
    desktop_root = tmp_path / "localappdata" / "AI Daily"

    assert report["copied_files"] == 1
    assert report["state_copied"] == 1
    assert (desktop_root / "custom-output" / "2026-04-09.json").exists()
    assert not (desktop_root / "custom-output" / "ignored.json").exists()
