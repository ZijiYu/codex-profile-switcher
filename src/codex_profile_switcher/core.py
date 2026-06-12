from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


PROFILE_FILES = ("config.toml", "account.config.toml", "api.config.toml", "auth.json")


@dataclass(frozen=True)
class ProfileStatus:
    name: str
    path: Path
    exists: bool
    mode: str
    model: str | None
    provider: str | None
    base_url: str | None
    auth_present: bool
    auth_mode: str | None
    config_present: bool
    config_empty: bool
    api_config_present: bool


class ProfileStore:
    def __init__(self, root: Path | None = None, codex_dir: Path | None = None) -> None:
        self.root = root or Path(os.environ.get("CODEX_PROFILE_ROOT", "~/.codex-profiles")).expanduser()
        self.codex_dir = codex_dir or Path(os.environ.get("CODEX_DIR", "~/.codex")).expanduser()

    def profile_dir(self, name: str) -> Path:
        return self.root / name

    def list_profiles(self) -> list[str]:
        if not self.root.exists():
            return []
        ignored = {"bin", "backups", "deleted"}
        return sorted(p.name for p in self.root.iterdir() if p.is_dir() and p.name not in ignored)

    def list_deleted(self) -> list[str]:
        deleted = self.root / "deleted"
        if not deleted.exists():
            return []
        return sorted(p.name for p in deleted.iterdir() if p.is_dir())

    def init_profile(self, name: str) -> Path:
        target = self.profile_dir(name)
        target.mkdir(parents=True, exist_ok=True)
        self._copy_profile_files(self.codex_dir, target)
        self._ensure_file_auth_store(target / "config.toml")
        return target

    def save_profile(self, name: str) -> Path:
        return self.init_profile(name)

    def use_profile(self, name: str) -> Path:
        source = self.profile_dir(name)
        if not source.exists():
            raise FileNotFoundError(f"profile does not exist: {source}")
        backup = self.backup_current()
        self._copy_profile_files(source, self.codex_dir)
        return backup

    def delete_profile(self, name: str) -> Path:
        source = self.profile_dir(name)
        if not source.exists():
            raise FileNotFoundError(f"profile does not exist: {source}")
        protected = {"bin", "backups", "deleted"}
        if name in protected:
            raise ValueError(f"refusing to delete protected profile: {name}")
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        target = self.root / "deleted" / f"{name}-{stamp}"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(target))
        return target

    def restore_profile(self, deleted_name: str, profile_name: str | None = None) -> Path:
        source = self.root / "deleted" / deleted_name
        if not source.exists():
            raise FileNotFoundError(f"deleted profile does not exist: {source}")
        target_name = profile_name or strip_deleted_stamp(deleted_name)
        target = self.profile_dir(target_name)
        if target.exists():
            raise FileExistsError(f"profile already exists: {target}")
        shutil.move(str(source), str(target))
        return target

    def backup_current(self) -> Path:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = self.root / "backups" / stamp
        backup.mkdir(parents=True, exist_ok=True)
        self._copy_profile_files(self.codex_dir, backup)
        return backup

    def login_profile(self, name: str) -> int:
        target = self.profile_dir(name)
        target.mkdir(parents=True, exist_ok=True)
        env = os.environ.copy()
        env["CODEX_HOME"] = str(target)
        return subprocess.call(["codex", "login"], env=env)

    def active_status(self) -> ProfileStatus:
        return self.status_for_path("active", self.codex_dir)

    def profile_status(self, name: str) -> ProfileStatus:
        return self.status_for_path(name, self.profile_dir(name))

    def status_for_path(self, name: str, path: Path) -> ProfileStatus:
        config_path = path / "config.toml"
        api_config_path = path / "api.config.toml"
        config = read_text(config_path)
        api_config = read_text(api_config_path)
        combined = "\n".join(part for part in (config, api_config) if part)
        auth = read_auth(path / "auth.json")
        return ProfileStatus(
            name=name,
            path=path,
            exists=path.exists(),
            mode=detect_mode(combined, auth),
            model=find_toml_scalar(combined, "model"),
            provider=find_toml_scalar(combined, "model_provider"),
            base_url=find_toml_scalar(combined, "base_url"),
            auth_present=(path / "auth.json").exists(),
            auth_mode=auth.get("auth_mode") if isinstance(auth, dict) else None,
            config_present=config_path.exists(),
            config_empty=config_path.exists() and not config.strip(),
            api_config_present=api_config_path.exists(),
        )

    def _copy_profile_files(self, source: Path, target: Path) -> None:
        target.mkdir(parents=True, exist_ok=True)
        for name in PROFILE_FILES:
            src = source / name
            if src.exists():
                shutil.copy2(src, target / name)

    def _ensure_file_auth_store(self, config_path: Path) -> None:
        if not config_path.exists():
            return
        text = config_path.read_text(encoding="utf-8")
        if "cli_auth_credentials_store" in text:
            return
        config_path.write_text('cli_auth_credentials_store = "file"\n' + text, encoding="utf-8")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def read_auth(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def find_toml_scalar(text: str, key: str) -> str | None:
    prefix = f"{key} = "
    for raw in text.splitlines():
        line = raw.strip()
        if not line.startswith(prefix):
            continue
        value = line[len(prefix) :].strip()
        if len(value) >= 2 and value[0] == value[-1] == '"':
            return value[1:-1]
        return value
    return None


def detect_mode(config_text: str, auth: dict) -> str:
    if 'env_key = "OPENAI_API_KEY"' in config_text or "env_key =" in config_text:
        return "api"
    if "requires_openai_auth = true" in config_text:
        return "auth"
    if auth.get("tokens"):
        return "auth"
    return "unknown"


def strip_deleted_stamp(name: str) -> str:
    parts = name.rsplit("-", 2)
    if len(parts) == 3 and len(parts[1]) == 8 and len(parts[2]) == 6:
        return parts[0]
    return name
