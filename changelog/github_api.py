"""
Обновляет файлы в GitHub репо через REST API — без git subprocess.
"""
import base64
import json
import logging
from datetime import datetime
from pathlib import Path

import requests

logger = logging.getLogger("changelog.github_api")

OWNER = "dansavishev"
REPO = "Transformation-Bot"
API_BASE = f"https://api.github.com/repos/{OWNER}/{REPO}/contents"


def _headers(token: str) -> dict:
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def push_file_to_github(local_path: str, repo_path: str, token: str, commit_message: str = None) -> bool:
    """
    Атомарно обновляет файл в GitHub репо через API.
    local_path  — путь к локальному файлу
    repo_path   — путь внутри репо (напр. "data/changelog.json")
    token       — GitHub Personal Access Token
    Возвращает True при успехе.
    """
    if not commit_message:
        commit_message = f"Publish changelog [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]"

    with open(local_path, "rb") as f:
        content_b64 = base64.b64encode(f.read()).decode("utf-8")

    url = f"{API_BASE}/{repo_path}"

    # Получаем текущий SHA файла (нужен для update), явно указываем ветку
    resp = requests.get(url, headers=_headers(token), params={"ref": "master"}, timeout=15)
    if resp.status_code == 200:
        current_sha = resp.json().get("sha")
    elif resp.status_code == 404:
        current_sha = None  # файл новый
    else:
        logger.error(f"GitHub API GET ошибка {resp.status_code}: {resp.text[:200]}")
        return False

    payload = {
        "message": commit_message,
        "content": content_b64,
        "branch": "master",
    }
    if current_sha:
        payload["sha"] = current_sha

    resp = requests.put(url, headers=_headers(token), json=payload, timeout=15)
    if resp.status_code in (200, 201):
        logger.info(f"✅ GitHub API: {repo_path} обновлён")
        return True
    else:
        logger.error(f"GitHub API PUT ошибка {resp.status_code}: {resp.text[:300]}")
        return False
