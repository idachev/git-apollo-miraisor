import concurrent.futures
import logging
import os
import time

from config import (
    REPOS,
    BRANCHES,
    REPO_PADDING,
    SHAPE_COLOR_NO_TICKETS,
    SHAPE_COLOR_TICKETS,
    SHAPES_X_PADDING,
    JIRA_BROWSE_URL,
    GITHUB_OWNER,
    TRUNCATE_LINE_LENGTH, SHAPE_MAX_HEIGHT,
)
from git_utils import get_commit_messages, get_pull_requests_to_branch, \
    PullRequestInfo
from jira_utils import extract_jira_ticket_numbers, \
    get_jira_tickets_titles
from miro_utils import miro_create_shape, \
    miro_cleanup_board, miro_create_connectors

os.environ["TZ"] = "UTC"

logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
)

logger = logging.getLogger(__name__)

VERSION_FILE = './version.txt'

version = '0.0.0'

if os.path.isfile(VERSION_FILE):
    with open(VERSION_FILE, 'r') as f:
        version = f.read()
        version = version.strip()


def no_ticket_ids_in_commit_message(commit_message, ticket_ids):
    for ticket_id in ticket_ids:
        if ticket_id in commit_message:
            return False
    return True


def truncate_line(line):
    return line[:TRUNCATE_LINE_LENGTH] + (line[TRUNCATE_LINE_LENGTH:] and '...')


def filter_commit_messages_without_ticket_ids(commit_messages, ticket_ids):
    return list(
            map(lambda iter_line: truncate_line(iter_line),
                filter(lambda commit_message:
                       no_ticket_ids_in_commit_message(
                               commit_message,
                               ticket_ids),
                       commit_messages)))


def get_all_branches_ticket_ids(repo, branches):
    all_ticket_ids_and_commit_msgs = []

    for i, branch in enumerate(branches[:-1]):
        commit_messages = get_commit_messages(repo, branch, branches[i + 1])
        ticket_ids = extract_jira_ticket_numbers(commit_messages)
        commit_msgs_without_ticket_ids = \
            filter_commit_messages_without_ticket_ids(
                    commit_messages, ticket_ids)
        all_ticket_ids_and_commit_msgs.append(
                (ticket_ids, commit_msgs_without_ticket_ids))

    return repo, all_ticket_ids_and_commit_msgs


def get_pull_requests_to_branch_per_repo(repo, branch):
    return repo, get_pull_requests_to_branch(repo, branch)


def create_miro_shape_with_tickets(
        ticket_ids,
        commit_messages,
        x, y,
        from_branch, to_branch,
        shape_color):
    shape_text = f"<b>{from_branch} -> {to_branch}</b>\n"

    ticket_id_to_title = get_jira_tickets_titles(ticket_ids)

    ticket_texts = []
    for ticket_id in ticket_ids:
        ticket_url = JIRA_BROWSE_URL + f"/{ticket_id}"
        ticket_title = truncate_line(ticket_id_to_title[ticket_id])
        ticket_texts.append(
                f"<br/><a href=\"{ticket_url}\" target=\"blank\">"
                f"{ticket_id}</a> - {ticket_title}")

    for commit_message in commit_messages:
        ticket_texts.append(
                f"<br/>{commit_message}")

    if len(ticket_texts) > 0:
        shape_text += "<br/>\n"

    shape_text += "\n".join(ticket_texts)

    shape = miro_create_shape(x, y, shape_text, color=shape_color)

    return shape


def build_tickets_links_html(ticket_ids):
    if not ticket_ids:
        return ""

    ticket_texts = []
    for ticket_id in ticket_ids:
        ticket_url = JIRA_BROWSE_URL + f"/{ticket_id}"
        ticket_texts.append(
                f"<a href=\"{ticket_url}\" target=\"blank\">"
                f"{ticket_id}</a>")

    return ", ".join(ticket_texts)


def create_miro_shape_for_prs(
        pr_infos,
        x, y,
        to_branch,
        shape_color):
    shape_text = f"<b>Pull requests -> {to_branch}</b>\n"

    pr_texts = []
    for pr_info in pr_infos:
        assert isinstance(pr_info, PullRequestInfo)

        ticket_ids = extract_jira_ticket_numbers([pr_info.title])

        tickets_html = build_tickets_links_html(ticket_ids)

        pr_texts.append(
                "<br/>" +
                (f"{tickets_html} - " if tickets_html else "") +
                f"<a href=\"{pr_info.url}\" target=\"blank\">"
                f"{pr_info.title}</a> - "
                f"{pr_info.author}")

    if len(pr_texts) > 0:
        shape_text += "<br/>\n"

    shape_text += "\n".join(pr_texts)

    shape = miro_create_shape(x, y, shape_text, color=shape_color)

    return shape


def create_branch_shapes(
        branches,
        all_ticket_ids_and_commit_msgs,
        x_offset,
        y_offset,
        connectors,
        shape_color):
    first_branch_shape = None
    previous_shape = None

    max_shape_height = 0

    for i, branch in enumerate(branches[:-1]):
        logger.info(f"Processing branch: {branch} to {branches[i + 1]}")

        ticket_ids, commit_msgs = all_ticket_ids_and_commit_msgs[i]

        has_commit_msgs = len(commit_msgs) > 0
        commit_msgs = list(
                filter(lambda msg: 'pull request #' not in msg, commit_msgs))

        if len(commit_msgs) == 0 and has_commit_msgs:
            commit_msgs = ['...']

        ticket_shape = create_miro_shape_with_tickets(
                ticket_ids, commit_msgs,
                x_offset, y_offset, branch,
                branches[i + 1],
                shape_color)

        if ticket_shape is None:
            ticket_shape = create_miro_shape_with_tickets(
                    ticket_ids, ['...'],
                    x_offset, y_offset, branch,
                    branches[i + 1],
                    shape_color)

        if ticket_shape is None:
            continue

        if i == 0:
            first_branch_shape = ticket_shape
        if previous_shape is not None:
            connectors.append((previous_shape['id'], ticket_shape['id']))
        previous_shape = ticket_shape

        shape_width = ticket_shape['geometry']['width']
        shape_height = ticket_shape['geometry']['height']

        max_shape_height = max(shape_height, max_shape_height)

        x_offset += shape_width + SHAPES_X_PADDING

    return first_branch_shape, max_shape_height


def calculate_max_shape_height_offset(all_ticket_ids_and_commit_msgs):
    max_lines = 0

    for ticket_ids, commit_msgs in all_ticket_ids_and_commit_msgs:
        total_lines = len(ticket_ids) + len(commit_msgs)
        max_lines = max(max_lines, total_lines)

    offset = max_lines * 5

    return min(SHAPE_MAX_HEIGHT / 3, offset)


def calculate_max_shape_height_offset_per_pr_infos(pr_repos):
    offset = len(pr_repos) * 5

    return min(SHAPE_MAX_HEIGHT / 3, offset)


def get_repos_to_all_branches_ticket_ids(repos, branches):
    repo_to_all_ticket_ids = {}

    with concurrent.futures.ThreadPoolExecutor() as executor:

        futures = []

        for repo in repos:
            futures.append(executor.submit(get_all_branches_ticket_ids,
                                           repo=repo,
                                           branches=branches))

        for future in concurrent.futures.as_completed(futures):
            repo, all_ticket_ids_and_commit_msgs = future.result()
            logging.info(f"Future get branches ticket IDs: "
                         f"{repo}, {all_ticket_ids_and_commit_msgs}")
            repo_to_all_ticket_ids[repo] = all_ticket_ids_and_commit_msgs

    return repo_to_all_ticket_ids


def get_repos_pull_requests(repos, branch):
    repo_to_pr_infos = {}

    with concurrent.futures.ThreadPoolExecutor() as executor:

        futures = []

        for repo in repos:
            futures.append(executor.submit(get_pull_requests_to_branch_per_repo,
                                           repo=repo,
                                           branch=branch))

        for future in concurrent.futures.as_completed(futures):
            repo, pr_infos = future.result()
            logging.info(f"Future get branch pull requests: "
                         f"{repo}, {pr_infos}")
            repo_to_pr_infos[repo] = pr_infos

    return repo_to_pr_infos


def create_miro_board_for_repos(repos, branches):
    y_offset = 0
    connectors = []

    repo_to_all_ticket_ids = get_repos_to_all_branches_ticket_ids(repos,
                                                                  branches)

    current_time = time.strftime('%Y-%m-%d %H:%M:%S %Z', time.gmtime())

    time_text = f"<b>{current_time}</b><br/>" \
                f"<b>v.{version}</b>"
    miro_create_shape(0, y_offset, time_text, color=SHAPE_COLOR_NO_TICKETS)
    y_offset += REPO_PADDING

    repo_to_pr_infos = get_repos_pull_requests(repos, branches[0])

    for repo in repos:
        logger.info(f"Processing repo: {repo}")

        pr_infos = repo_to_pr_infos[repo]

        all_ticket_ids_and_commit_msgs = repo_to_all_ticket_ids[repo]

        any_tickets = any(ticket_ids or commit_msgs for
                          (ticket_ids, commit_msgs) in
                          all_ticket_ids_and_commit_msgs)

        any_tickets = any_tickets or any(pr_infos)

        y_offset += max(
                calculate_max_shape_height_offset_per_pr_infos(pr_infos),
                calculate_max_shape_height_offset(
                        all_ticket_ids_and_commit_msgs))

        shape_color = SHAPE_COLOR_NO_TICKETS if not any_tickets \
            else SHAPE_COLOR_TICKETS

        repo_text = f"<a href=\"https://github.com/{GITHUB_OWNER}/{repo}\" " \
                    f"target=\"blank\">{repo}</a></b>"

        repo_shape = miro_create_shape(0, y_offset, repo_text,
                                       color=shape_color)

        repo_shape_width = repo_shape['geometry']['width']
        x_offset = repo_shape_width + SHAPES_X_PADDING

        pr_shape = create_miro_shape_for_prs(pr_infos, x_offset, y_offset,
                                             branches[0], shape_color)

        pr_shape_width = pr_shape['geometry']['width']
        pr_shape_height = pr_shape['geometry']['height']
        x_offset += pr_shape_width + SHAPES_X_PADDING

        connectors.append((repo_shape['id'], pr_shape['id']))

        first_branch_shape, max_shape_height = \
            create_branch_shapes(branches, all_ticket_ids_and_commit_msgs,
                                 x_offset, y_offset,
                                 connectors,
                                 shape_color)

        if first_branch_shape is not None:
            connectors.append((pr_shape['id'], first_branch_shape['id']))

        y_offset += max(max_shape_height, pr_shape_height) / 2 + REPO_PADDING

    miro_create_connectors(connectors)


if __name__ == "__main__":
    while True:
        miro_cleanup_board()

        create_miro_board_for_repos(REPOS, BRANCHES)

        each_seconds = int(os.getenv("EXECUTE_EACH_SECONDS", 0))
        if each_seconds > 0:
            time.sleep(each_seconds)
        else:
            break
