from __future__ import annotations

"""Mainline packaged desktop smoke for the qml-only desktop runtime."""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
BRANDING_DIR = REPO_ROOT / "assets" / "branding"
FONT_DIR = REPO_ROOT / "assets" / "fonts"
SPEC_PATH = REPO_ROOT / "build" / "windows" / "AI Daily.spec"
DIST_QML_LAYOUTS_DIR = REPO_ROOT / "dist" / "AI Daily" / "_internal" / "PySide6" / "qml" / "QtQuick" / "Layouts"
DIST_RESOURCE_BUNDLE_PATH = REPO_ROOT / "dist" / "AI Daily" / "_internal" / "src" / "desktop" / "resources.rcc"


def test_desktop_assets_include_minimum_icons_and_fonts() -> None:
    expected_files = [
        BRANDING_DIR / "icon-digest.svg",
        BRANDING_DIR / "icon-trending.svg",
        BRANDING_DIR / "icon-settings.svg",
        BRANDING_DIR / "icon-search.svg",
        FONT_DIR / "NotoSansSC-VF.ttf",
        FONT_DIR / "NotoSerifSC-VF.ttf",
    ]

    for asset_path in expected_files:
        assert asset_path.is_file(), f"missing asset: {asset_path}"
        assert asset_path.stat().st_size > 0, f"empty asset: {asset_path}"


def test_pyinstaller_spec_packages_branding_fonts_and_resource_bundle() -> None:
    spec_text = SPEC_PATH.read_text(encoding="utf-8")

    assert 'assets" / "branding' in spec_text
    assert 'assets" / "fonts' in spec_text
    assert 'src" / "desktop" / "resources.rcc' in spec_text


def test_pyinstaller_spec_uses_qml_collection_instead_of_qtquicklayouts_hidden_import() -> None:
    spec_text = SPEC_PATH.read_text(encoding="utf-8")

    assert '"PySide6.QtQml"' in spec_text
    assert '"PySide6.QtQuick"' in spec_text
    assert '"PySide6.QtQuickControls2"' in spec_text
    assert '"PySide6.QtQuickLayouts"' not in spec_text


def test_packaged_runtime_includes_qtquick_layouts_plugin_when_dist_exists() -> None:
    if not DIST_QML_LAYOUTS_DIR.exists():
        pytest.skip("packaged runtime not present; run PyInstaller before checking QML plugin payload")

    expected_files = [
        DIST_QML_LAYOUTS_DIR / "qmldir",
        DIST_QML_LAYOUTS_DIR / "plugins.qmltypes",
        DIST_QML_LAYOUTS_DIR / "qquicklayoutsplugin.dll",
    ]

    for asset_path in expected_files:
        assert asset_path.is_file(), f"missing packaged QML layout plugin asset: {asset_path}"

    assert DIST_RESOURCE_BUNDLE_PATH.is_file(), (
        f"missing packaged desktop resource bundle: {DIST_RESOURCE_BUNDLE_PATH}"
    )
