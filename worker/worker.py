import base64
import io
import logging
import socket
from itertools import cycle
from time import sleep

import numpy as np
import requests
import sseclient
from PIL import Image
from requests.exceptions import ConnectionError

log = logging.getLogger(__name__)

log.info("Initializing Worker")

RENDERER_URLS = {
    "noise": "http://renderernoise/render",
    # "text": "http://renderertext/render",
    "osc": "http://rendererosc/render",
}
ALL_RENDERERS = list(RENDERER_URLS.keys())

# PROD i.e. disco on raspi
SCREEN_UDP_IP = "10.0.0.42"
SCREEN_UDP_PORT = 6450

SCREEN_WIDTH = 96
SCREEN_HEIGHT = 38

SCREEN_SOCK = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP


def receive_frames_from_renderer(renderer_name):
    try:
        response = requests.post(
            RENDERER_URLS[renderer_name],
            headers={"Accept": "text/event-stream"},
            stream=True,
            json={"payload": "some data"},
            # timeout is a tuple of (connect, read) second timeout values
            timeout=(1, 5),
        )
    except requests.RequestException as e:
        print("request exception!!", e)
        return

    assert response.status_code == 200

    # if response.status_code != 200:
    # log.info("Screen endpoint returned %d", response.status_code)
    #     return

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
        print("request exception!!", e)


def send_frame_to_display(png_image_data):
    # expecting base64 1 channel png, fail otherwise
    pil_image = Image.frombytes("1", (96, 38), png_image_data)
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
    SCREEN_SOCK.sendto(frame_packed_bits, (SCREEN_UDP_IP, SCREEN_UDP_PORT))


def worker():
    all_renderers = cycle(ALL_RENDERERS)

    while True:
        print("Worker is working...")

        for renderer in all_renderers:
            print("Current renderer:", renderer)
            for frame in receive_frames_from_renderer(renderer):
                # we processed 1 frame, we can do other things now
                send_frame_to_display(frame)
            sleep(1)


if __name__ == "__main__":
    worker()
