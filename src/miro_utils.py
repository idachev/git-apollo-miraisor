import concurrent.futures
import http
import logging
import math
import random
import re
import string
import sys
import time

import requests

from config import (
    MIRO_API_URL,
    MIRO_API_TOKEN,
    MIRO_BOARD_ID, MAX_REQUEST_RETRIES, SHAPE_MAX_HEIGHT,
)

logger = logging.getLogger(__name__)

miro_headers = {
    'Authorization': f'Bearer {MIRO_API_TOKEN}',
    "Accept": "application/json",
    "Content-Type": "application/json",
}

shapes_url = f'{MIRO_API_URL}/boards/{MIRO_BOARD_ID}/shapes'

connectors_url = f'{MIRO_API_URL}/boards/{MIRO_BOARD_ID}/connectors'

items_url = f'{MIRO_API_URL}/boards/{MIRO_BOARD_ID}/items'

html_tags = ['<b>', '</b>', '<br>', '<br/>', '</br>', '<p>', '</p>']


def execute_requests_with_retry(lambda_func):
    for retry in range(1, MAX_REQUEST_RETRIES):
        response = lambda_func()

        if response.status_code == http.HTTPStatus.TOO_MANY_REQUESTS:
            time.sleep(
                    random.randrange(1, math.ceil(1.5 * MAX_REQUEST_RETRIES)))
            continue

        if response.status_code == http.HTTPStatus.NO_CONTENT:
            return None

        if response.status_code == http.HTTPStatus.FORBIDDEN:
            if 'the request has been blocked' in response.text:
                logger.warning(
                        "Found 'the request has been blocked' "
                        "in response, sleep a bit...")

                logger.warning(f"Response: {response.text}")

                time.sleep(
                        random.randrange(1,
                                         math.ceil(1.5 * MAX_REQUEST_RETRIES)))

                continue
            else:
                logger.fatal(
                        f"Got forbidden "
                        f"{response.status_code}, {response.text}")
                sys.exit(1)

        if response.status_code == http.HTTPStatus.OK or \
                response.status_code == http.HTTPStatus.CREATED:
            try:
                return response.json()
            except Exception as e:
                logger.exception(
                        f"On retry {retry} Failed to parse response: "
                        f"{response.status_code}, {response.text}, {e}")
                time.sleep(random.randrange(2, 20))
        else:
            logger.fatal(
                    f"Got unexpected status code {response.status_code}, "
                    f"{response.text}")
            sys.exit(2)

    logger.fatal(
            f"Failed to execute request after {MAX_REQUEST_RETRIES} retries")
    sys.exit(3)


def normalize_line_len(line):
    links = re.findall(r'(<a href="[^\s\"]+"[^>]*>)', line)

    line_len = len(line)

    for link in links:
        line_len -= len(link)

    for tag in html_tags:
        line_len -= line.count(tag) * len(tag)

    return line_len


def calculate_shape_width_and_height_from_text(text):
    width_per_char = 6
    height_per_line = 20
    padding = 50
    min_width = 200
    min_height = 100

    text_lines = text.split("\n")
    max_line_length = max(normalize_line_len(line) for line in text_lines)
    num_lines = len(text_lines)

    width = max(min_width, max_line_length * width_per_char + padding)
    height = min(SHAPE_MAX_HEIGHT,
                 max(min_height, num_lines * height_per_line + padding))

    return width, height


def remove_non_ascii(a_str):
    ascii_chars = set(string.printable)

    return ''.join(
            filter(lambda x: x in ascii_chars, a_str)
    )


total_max_send = 0


def miro_create_shape(x, y, text, color=None):
    global total_max_send

    """
    Check https://developers.miro.com/reference/create-shape-item

    :param x:
    :param y:
    :param text:
    :param color:
    :return:
    """

    text = text.strip()

    width, height = calculate_shape_width_and_height_from_text(text)

    is_single_line = len(text.split("\n")) == 1

    text = remove_non_ascii(text)

    shape_payload = {
        "data": {
            "content": text,
            "shape": "round_rectangle",
        },
        "position": {
            "origin": "center",
            "x": math.ceil(x + width / 2),
            "y": math.ceil(y)
        },
        "geometry": {
            "height": math.ceil(height),
            "width": math.ceil(width)
        },
        "style": {
            "textAlignVertical": "middle",
            "textAlign": ("center" if is_single_line else "left")
        }
    }
    if color:
        shape_payload['style']['fillColor'] = color

    return execute_requests_with_retry(
            lambda: requests.post(shapes_url,
                                  json=shape_payload,
                                  headers=miro_headers))


def miro_create_connector(start_shape_id, end_shape_id):
    """
    Check https://developers.miro.com/reference/create-connector

    :param start_shape_id:
    :param end_shape_id:
    :return:
    """
    connector_payload = {
        "startItem": {"id": start_shape_id},
        "endItem": {"id": end_shape_id},
        "shape": "curved"
    }

    return execute_requests_with_retry(
            lambda: requests.post(connectors_url,
                                  json=connector_payload, headers=miro_headers))


def miro_create_connectors(connectors):
    with concurrent.futures.ThreadPoolExecutor() as executor:

        futures = []

        for (start_shape_id, end_shape_id) in connectors:
            futures.append(executor.submit(miro_create_connector,
                                           start_shape_id=start_shape_id,
                                           end_shape_id=end_shape_id))

        for future in concurrent.futures.as_completed(futures):
            logging.info(f"Future create connectors result: {future.result()}")


def miro_delete_shape(shape_id):
    logging.info(f"Delete shape: {shape_id}")

    execute_requests_with_retry(
            lambda: requests.delete(shapes_url + f"/{shape_id}",
                                    headers=miro_headers))


def miro_delete_shapes(shape_ids):
    with concurrent.futures.ThreadPoolExecutor() as executor:

        futures = []

        for shape_id in shape_ids:
            futures.append(
                    executor.submit(miro_delete_shape, shape_id=shape_id))

        for future in concurrent.futures.as_completed(futures):
            logging.info(f"Future delete result: {future.result()}")


def miro_cleanup_board():
    iter_cursor = ""
    while True:
        params = {
            "limit": 50,
            "type": "shape",
            "cursor": iter_cursor
        }

        items = execute_requests_with_retry(
                lambda: requests.get(items_url, params, headers=miro_headers))

        if 'data' in items and len(items['data']) > 0:
            shape_ids = list(map(lambda shape: shape['id'], items['data']))
            miro_delete_shapes(shape_ids)
        else:
            break

        if 'cursor' in items:
            iter_cursor = items['cursor']
        else:
            break
