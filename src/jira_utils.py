import base64
import concurrent.futures
import logging
import re

from jira import JIRA

from config import JIRA_USERNAME, JIRA_API_TOKEN, JIRA_API_URL

jira_auth_encoded = base64.b64encode(
        f"{JIRA_USERNAME}:{JIRA_API_TOKEN}".encode()).decode()

jira_headers = {
    'Accept': 'application/json',
    'Authorization': f'Basic {jira_auth_encoded}',
}

jira = JIRA(JIRA_API_URL, basic_auth=(JIRA_USERNAME, JIRA_API_TOKEN))


def get_jira_ticket_title(ticket_id):
    if 'LITE-000' in ticket_id:
        return ticket_id, ''

    try:
        issue = jira.issue(ticket_id)
    except:
        logging.exception(f"Failed to get summary for {ticket_id}")

        return ticket_id, ''

    return ticket_id, issue.fields.summary


def get_jira_tickets_titles(ticket_ids):
    ticket_id_to_title = {}

    with concurrent.futures.ThreadPoolExecutor() as executor:

        futures = []

        for ticket_id in ticket_ids:
            futures.append(executor.submit(get_jira_ticket_title,
                                           ticket_id=ticket_id))

        for future in concurrent.futures.as_completed(futures):
            ticket_id, title = future.result()
            logging.info(f"Future get title result: {ticket_id}, {title}")
            ticket_id_to_title[ticket_id] = title

    return ticket_id_to_title


def extract_jira_ticket_numbers(commit_messages):
    ticket_pattern = r'[A-Z]+-\d+'
    ticket_ids = set(re.findall(ticket_pattern, ' '.join(commit_messages)))

    return sorted(set(
            filter(lambda ticket_id: 'LITE-000' not in ticket_id, ticket_ids)))
