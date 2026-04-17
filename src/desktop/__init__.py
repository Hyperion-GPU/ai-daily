"""Desktop package exports for the QML-only runtime."""

from __future__ import annotations


def create_qml_runtime(*args, **kwargs):
    from .qml_app import create_qml_runtime as _create_qml_runtime

    return _create_qml_runtime(*args, **kwargs)


def launch_qml_desktop_app(argv=None):
    from .qml_app import launch_qml_desktop_app as _launch_qml_desktop_app

    return _launch_qml_desktop_app(argv=argv)


def main(argv=None):
    from .qml_app import main as _main

    return _main(argv=argv)


__all__ = ["create_qml_runtime", "launch_qml_desktop_app", "main"]
