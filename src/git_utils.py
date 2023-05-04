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


class PullRequestInfo:
    def __init__(self, title, url, author):
        self.title = title
        self.url = url
        self.author = author


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


def get_pull_requests_to_branch(repo, to_branch):
    url = f"{GITHUB_API_URL}/repos/{GITHUB_OWNER}/{repo}/pulls"
    params = {"state": "open", "base": f"{to_branch}"}

    response = requests.get(url, headers=github_headers, params=params)

    if response.status_code != http.HTTPStatus.OK:
        logger.warning(f"Failed to get pull requests, "
                       f"repo: {repo}, {to_branch}, "
                       f"Status code: {response.status_code}, "
                       f"Response body: {response.text}")
        return []

    pull_requests = response.json()

    pr_infos = []
    for pr in pull_requests:
        pr_infos.append(
                PullRequestInfo(pr["title"],
                                pr['html_url'],
                                pr['user']['login']))

    return pr_infos
