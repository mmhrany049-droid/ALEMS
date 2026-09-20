"""File Management — data/ backups/ exports/ imports/ (doc 03 folder layout).

All filesystem roots are derived from Settings; nothing is scattered in code.
Backup/restore, export and import modules (phases 6/8) use these helpers.
"""
from __future__ import annotations

from pathlib import Path

from app.core.config import Settings, get_settings


def ensure_directories(settings: Settings | None = None) -> None:
    s = settings or get_settings()
    for d in (s.data_dir, s.backups_dir, s.exports_dir, s.imports_dir):
        Path(d).mkdir(parents=True, exist_ok=True)


def data_dir(settings: Settings | None = None) -> Path:
    s = settings or get_settings()
    return Path(s.data_dir)


def backups_dir(settings: Settings | None = None) -> Path:
    s = settings or get_settings()
    return Path(s.backups_dir)


def exports_dir(settings: Settings | None = None) -> Path:
    s = settings or get_settings()
    return Path(s.exports_dir)


def imports_dir(settings: Settings | None = None) -> Path:
    s = settings or get_settings()
    return Path(s.imports_dir)
