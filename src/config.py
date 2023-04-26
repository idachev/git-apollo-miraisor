import os


def get_default_if_empty(env_value, default):
    if env_value is None or len(env_value) == 0:
        return default
    else:
        return env_value


GITHUB_API_URL = "https://api.github.com"
GITHUB_API_TOKEN = os.environ.get("GITHUB_API_TOKEN")
GITHUB_OWNER = os.environ.get("GITHUB_OWNER")

JIRA_API_URL = os.environ.get("JIRA_API_URL")
JIRA_USERNAME = os.environ.get("JIRA_USERNAME")
JIRA_API_TOKEN = os.environ.get("JIRA_API_TOKEN")

MIRO_API_URL = "https://api.miro.com/v2"
MIRO_API_TOKEN = os.environ.get("MIRO_API_TOKEN")
MIRO_BOARD_ID = os.environ.get("MIRO_BOARD_ID")

REPOS = os.environ.get("REPOS").split(",")
BRANCHES = get_default_if_empty(os.environ.get("BRANCHES"),
                                "master,qa,staging,production").split(",")

JIRA_BROWSE_URL = os.environ.get("JIRA_BROWSE_URL")

REPO_PADDING = int(get_default_if_empty(os.environ.get("REPO_PADDING"), 200))
SHAPES_X_PADDING = int(
        get_default_if_empty(os.environ.get("SHAPES_X_PADDING"), 150))

SHAPE_COLOR_NO_TICKETS = get_default_if_empty(
        os.environ.get("SHAPE_COLOR_NO_TICKETS"), "#AFE1AF")
SHAPE_COLOR_TICKETS = get_default_if_empty(
        os.environ.get("SHAPE_COLOR_TICKETS"), "#FFCCCB")

SHAPE_MAX_HEIGHT = int(
        get_default_if_empty(os.environ.get("SHAPE_MAX_HEIGHT"), 500))

TRUNCATE_LINE_LENGTH = int(
        get_default_if_empty(os.environ.get("TRUNCATE_LINE_LENGTH"), 65))

MAX_REQUEST_RETRIES = int(
        get_default_if_empty(os.environ.get("MAX_REQUEST_RETRIES"), 7))
