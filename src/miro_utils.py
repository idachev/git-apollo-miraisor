import concurrent.futures
import logging

import requests

from config import (
    MIRO_API_URL,
    MIRO_API_TOKEN,
    MIRO_BOARD_ID,
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


def calculate_shape_width_and_height_from_text(text):
    width_per_char = 3
    height_per_line = 25
    padding = 50
    min_width = 200
    min_height = 100

    text_lines = text.split("\n")
    max_line_length = max(len(line) for line in text_lines)
    num_lines = len(text_lines)

    width = max(min_width, max_line_length * width_per_char + padding)
    height = max(min_height, num_lines * height_per_line + padding)

    return width, height


def miro_create_shape(x, y, text, color=None):
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

    shape_payload = {
        "data": {
            "content": text,
            "shape": "round_rectangle",
        },
        "position": {
            "origin": "center",
            "x": x + width / 2,
            "y": y
        },
        "geometry": {
            "height": height,
            "width": width
        },
        "style": {
            "textAlignVertical": "middle",
            "textAlign": ("center" if is_single_line else "left")
        }
    }
    if color:
        shape_payload['style']['fillColor'] = color

    response = requests.post(shapes_url,
                             json=shape_payload, headers=miro_headers)
    return response.json()


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

    response = requests.post(connectors_url,
                             json=connector_payload, headers=miro_headers)
    return response.json()


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

    requests.delete(shapes_url + f"/{shape_id}", headers=miro_headers)


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

        response = requests.get(items_url, params, headers=miro_headers)
        items = response.json()

        if len(items['data']) > 0:
            shape_ids = list(map(lambda shape: shape['id'], items['data']))
            miro_delete_shapes(shape_ids)
        else:
            break

        if 'cursor' in items:
            iter_cursor = items['cursor']
        else:
            break
