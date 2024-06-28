from dotenv import load_dotenv

load_dotenv()

import base64
import io
import json
import logging
import os
import socket
from datetime import datetime
from itertools import cycle
from time import sleep

import numpy as np
import requests
import sseclient
from PIL import Image
from requests.exceptions import ConnectionError

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)
log.info("Initializing Worker")

DO_NOT_SEND_TO_RITER = os.environ["DO_NOT_SEND_TO_RITER"] == "true"
WEB_SERVICE_HOST = os.environ["WEB_SERVICE_HOST"]

RENDERER_URLS = {
    "text": os.environ["RENDERER_TEXT_HOST"] + "/render",
    # "text": "http://renderertext/render",
    # "noise": "http://renderernoise/render",
    "osc": "http://rendererosc/render",
    # "image": "http://rendererimage/render",
}
ALL_RENDERERS = list(RENDERER_URLS.keys())

# PROD i.e. disco on raspi
SCREEN_UDP_IP = "10.0.0.42"
SCREEN_UDP_PORT = 6450

SCREEN_WIDTH = 96
SCREEN_HEIGHT = 38

SCREEN_SOCK = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP

RENDERER_CONNECT_TIMEOUT_S = 5
RENDERER_READ_TIMEOUT_S = 5


def receive_frames_from_renderer(renderer_name, json_payload=None):
    try:
        response = requests.post(
            RENDERER_URLS[renderer_name],
            headers={"Accept": "text/event-stream"},
            stream=True,
            json=json_payload,
            # timeout is a tuple of (connect, read) second timeout values
            timeout=(RENDERER_CONNECT_TIMEOUT_S, RENDERER_READ_TIMEOUT_S),
        )
    except requests.RequestException as e:
        log.error("request exception!! %s", e)
        return

    assert response.status_code == 200

    try:
        for event in sseclient.SSEClient(response).events():
            if event.event == "screen_update":
                # print("event.data", event.data)
                base64_text = event.data
                image_bytes = base64.b64decode(base64_text)
                yield image_bytes
            elif event.event == "end":
                return
    except requests.RequestException as e:
        # log.error("request exception!! %s", e)
        return


def send_frame_to_display(pillow_raw_image_data):
    # FIXME
    # FIXME
    # FIXME
    # THIS ASSUMES THAT pillow_raw_image_data WAS IN MODE 1!!!!
    # IT MIGHT NOT BE!!!

    # expecting base64 1 channel png, fail otherwise
    pil_image = Image.frombytes("1", (96, 38), pillow_raw_image_data)
    # assert that it's exactly 96x38
    assert pil_image.size == (SCREEN_WIDTH, SCREEN_HEIGHT)
    # assert that its mode is 1 i.e. black and white
    assert pil_image.mode == "1"

    frame = np.zeros((SCREEN_HEIGHT * SCREEN_WIDTH, 1), bool)

    np_image = np.asarray(pil_image)

    # flip img from right-left to left-right
    np_image = np.flip(np_image, 1)

    frame_packed_bits = np.packbits(
        np_image.astype("bool"), axis=None, bitorder="little"
    )

    if DO_NOT_SEND_TO_RITER:
        # go through the lines and columns
        # and print '.' for 0 bit and '#' for 1 bit
        for y in range(SCREEN_HEIGHT):
            for x in range(SCREEN_WIDTH - 1, 0, -1):
                if np_image[y][x] == 1:
                    print("#", end="")
                else:
                    print(".", end="")
            print()
        print("--------------------------------------------------------")
    else:
        SCREEN_SOCK.sendto(frame_packed_bits, (SCREEN_UDP_IP, SCREEN_UDP_PORT))


def worker():
    while True:
        log.info("Worker is working...")

        # # fetch all shows from the web microservice
        # r = requests.get(WEB_SERVICE_HOST + "/internalapi/get_all_shows")
        # json_response = r.json()
        # # log.info("got response from web service: %s", json_response)
        # all_shows = json_response["shows"]
        # # log.info("got shows from web service: %s", all_shows)

        # for show in all_shows:
        #     log.info("Current show: %s", show)

        #     for frame in receive_frames_from_renderer(
        #         show["show_type"], json_payload=show["payload"]
        #     ):
        #         # we processed 1 frame, we can do other things now
        #         send_frame_to_display(frame)

        # sleep(1)

        for renderer in cycle(ALL_RENDERERS):
            log.info("Current renderer: %s", renderer)
            json_payload = None
            if renderer == "text":
                json_payload = {
                    "text": "Send 3648 chars of 0 and 1 by OSC to 10.100.7.28 port 12000. the OSC path does not matter. xx",
                    # "text": "Recurse Center Rapid Riter",
                }
            for frame in receive_frames_from_renderer(
                renderer, json_payload=json_payload
            ):
                # we processed 1 frame, we can do other things now
                send_frame_to_display(frame)
            sleep(1)


if __name__ == "__main__":
    worker()
