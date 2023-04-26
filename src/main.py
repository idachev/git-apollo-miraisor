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
)
from git_utils import get_commit_messages
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


def get_all_branches_ticket_ids(repo, branches):
    all_ticket_ids = []

    for i, branch in enumerate(branches[:-1]):
        commit_messages = get_commit_messages(repo, branch, branches[i + 1])
        ticket_ids = extract_jira_ticket_numbers(commit_messages)
        all_ticket_ids.append(ticket_ids)

    return repo, all_ticket_ids


def create_miro_shape_with_tickets(ticket_ids, x, y, from_branch, to_branch):
    shape_text = f"<b>{from_branch} -> {to_branch}</b>\n"

    ticket_id_to_title = get_jira_tickets_titles(ticket_ids)

    ticket_texts = []
    for ticket_id in ticket_ids:
        ticket_url = JIRA_BROWSE_URL + f"/{ticket_id}"
        ticket_title = ticket_id_to_title[ticket_id]
        ticket_texts.append(
                f"<br/><a href=\"{ticket_url}\" target=\"blank\">"
                f"{ticket_id}</a> - {ticket_title}")

    if len(ticket_texts) > 0:
        shape_text += "<br/>\n"

    shape_text += "\n".join(ticket_texts)

    shape_color = SHAPE_COLOR_NO_TICKETS if not ticket_ids \
        else SHAPE_COLOR_TICKETS

    shape = miro_create_shape(x, y, shape_text, color=shape_color)

    return shape


def create_branch_shapes(
        branches,
        all_ticket_ids,
        x_offset,
        y_offset,
        connectors):
    first_branch_shape = None
    previous_shape = None

    max_shape_height = 0

    for i, branch in enumerate(branches[:-1]):
        logger.info(f"Processing branch: {branch} to {branches[i + 1]}")

        ticket_shape = create_miro_shape_with_tickets(
                all_ticket_ids[i], x_offset, y_offset, branch, branches[i + 1])

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


def calculate_max_shape_height_offset(all_ticket_ids):
    max_tickets_count = 0

    for ticket_ids in all_ticket_ids:
        max_tickets_count = max(max_tickets_count, len(ticket_ids))

    return max_tickets_count * 11


def get_repos_to_all_branches_ticket_ids(repos, branches):
    repo_to_all_ticket_ids = {}

    with concurrent.futures.ThreadPoolExecutor() as executor:

        futures = []

        for repo in repos:
            futures.append(executor.submit(get_all_branches_ticket_ids,
                                           repo=repo,
                                           branches=branches))

        for future in concurrent.futures.as_completed(futures):
            repo, all_ticket_ids = future.result()
            logging.info(f"Future get branches ticket IDs: "
                         f"{repo}, {all_ticket_ids}")
            repo_to_all_ticket_ids[repo] = all_ticket_ids

    return repo_to_all_ticket_ids


def create_miro_board_for_repos(repos, branches):
    y_offset = 0
    connectors = []

    repo_to_all_ticket_ids = get_repos_to_all_branches_ticket_ids(repos,
                                                                  branches)

    for repo in repos:
        logger.info(f"Processing repo: {repo}")

        all_ticket_ids = repo_to_all_ticket_ids[repo]
        any_tickets = any(ticket_ids for ticket_ids in all_ticket_ids)

        shape_color = SHAPE_COLOR_NO_TICKETS if not any_tickets \
            else SHAPE_COLOR_TICKETS

        y_offset += calculate_max_shape_height_offset(all_ticket_ids)

        repo_shape = miro_create_shape(0, y_offset, f"<b>{repo}</p>",
                                       color=shape_color)

        repo_shape_width = repo_shape['geometry']['width']
        x_offset = repo_shape_width + SHAPES_X_PADDING

        first_branch_shape, max_shape_height = \
            create_branch_shapes(branches, all_ticket_ids, x_offset, y_offset,
                                 connectors)

        if first_branch_shape is not None:
            connectors.append((repo_shape['id'], first_branch_shape['id']))

        y_offset += max_shape_height / 2 + REPO_PADDING

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
