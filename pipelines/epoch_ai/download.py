"""Polite HTTP download + archive extraction helpers (stdlib only)."""

import shutil
import tarfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

USER_AGENT = "yuyan-research-bot/0.1 (+https://github.com/diabhaque/yuyan; diabhaque@gmail.com)"


def download(url: str, dest: Path) -> int:
    """Stream `url` to `dest`. Returns bytes written."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=120) as resp, open(dest, "wb") as f:
        shutil.copyfileobj(resp, f)
    return dest.stat().st_size


def extract_zip(path: Path, dest_dir: Path) -> None:
    with zipfile.ZipFile(path) as z:
        z.extractall(dest_dir)


def fetch_repo(repo: str, dest_dir: Path) -> Path:
    """Download a github.com/epoch-research/<repo> tarball and extract it. Returns the dir."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    for branch in ("main", "master"):
        url = f"https://codeload.github.com/epoch-research/{repo}/tar.gz/refs/heads/{branch}"
        tar_path = dest_dir / f"{repo}.tar.gz"
        try:
            download(url, tar_path)
        except urllib.error.HTTPError:
            continue
        with tarfile.open(tar_path) as t:
            t.extractall(dest_dir, filter="data")
        return dest_dir
    raise FileNotFoundError(f"No main/master tarball for epoch-research/{repo}")
