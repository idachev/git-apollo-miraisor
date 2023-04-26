#!/bin/bash
[ "$1" = -x ] && shift && set -x
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export REPOS=repo1,repo2
export BRANCHES=master,qa,staging,production

export GITHUB_OWNER=...
export GITHUB_API_TOKEN=...

export JIRA_API_URL=https://my-atlasian-domain.atlassian.net
export JIRA_USERNAME=...
export JIRA_API_TOKEN=...
export JIRA_BROWSE_URL=${JIRA_API_URL}/browse

export MIRO_API_TOKEN=...
export MIRO_BOARD_ID=...

export REPO_PADDING=200
export SHAPES_X_PADDING=150

export SHAPE_COLOR_NO_TICKETS='#AFE1AF'
export SHAPE_COLOR_TICKETS='#FFCCCB'
