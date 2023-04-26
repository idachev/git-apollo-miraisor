#!/bin/bash
[ "$1" = -x ] && shift && set -x
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

source ${DIR}/docker-build-env.sh

if [[ "${DOCKER_RUN_ENV}" ]]; then
  source ${DOCKER_RUN_ENV}
else
  source ${DIR}/docker-run-env.sh
fi

set -e

${DIR}/docker-build.sh

docker run -d -it \
  -e REPOS=${REPOS} \
  -e BRANCHES=${BRANCHES} \
  -e GITHUB_OWNER=${GITHUB_OWNER} \
  -e GITHUB_API_TOKEN=${GITHUB_API_TOKEN} \
  -e MIRO_API_TOKEN=${MIRO_API_TOKEN} \
  -e MIRO_BOARD_ID=${MIRO_BOARD_ID} \
  -e REPO_PADDING=${REPO_PADDING} \
  -e SHAPES_X_PADDING=${SHAPES_X_PADDING} \
  -e SHAPE_COLOR_NO_TICKETS=${SHAPE_COLOR_NO_TICKETS} \
  -e SHAPE_COLOR_TICKETS=${SHAPE_COLOR_TICKETS} \
  -e JIRA_API_URL=${JIRA_API_URL} \
  -e JIRA_USERNAME=${JIRA_USERNAME} \
  -e JIRA_API_TOKEN=${JIRA_API_TOKEN} \
  -e JIRA_BROWSE_URL=${JIRA_BROWSE_URL} \
  -e EXECUTE_EACH_SECONDS=${EXECUTE_EACH_SECONDS} \
  ${DOCKER_IMG_TAG}
