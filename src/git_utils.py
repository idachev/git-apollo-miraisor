import http
import logging

import requests as requests

from config import (
    GITHUB_API_URL,
    GITHUB_API_TOKEN,
    GITHUB_OWNER,
)

github_headers = {
    'Authorization': f'Bearer {GITHUB_API_TOKEN}',
    'Content-Type': 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28'
}

logger = logging.getLogger(__name__)


def get_commit_messages(repo, base_branch, compare_branch):
    url = f'{GITHUB_API_URL}/repos/{GITHUB_OWNER}/{repo}/compare/{compare_branch}...{base_branch}'

    response = requests.get(url, headers=github_headers)

    if response.status_code != http.HTTPStatus.OK:
        logger.warning(f"Failed to get commit messages, "
                       f"repo: {repo}, {compare_branch}...{base_branch}, "
                       f"Status code: {response.status_code}, "
                       f"Response body: {response.text}")
        return []

    data = response.json()

    if 'commits' not in data:
        logger.warning(f"Missing commits, "
                       f"repo: {repo}, {compare_branch}...{base_branch}, "
                       f"Status code: {response.status_code}, "
                       f"Response body: {response.text}")
        return []

    commit_messages = [commit['commit']['message']
                       for commit in data['commits']]

    return commit_messages
