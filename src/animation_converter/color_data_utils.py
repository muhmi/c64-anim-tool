import random
from typing import List

from petscii import petscii_screen


def offset_color_frames(screens: List[petscii_screen], offset: int):
    color_datas = []
    for screen in screens:
        color_datas.append([] + screen.color_data)
    index = offset % len(screens)
    offset_screens = []
    for screen in screens:
        offset_screen = screen.copy()
        offset_screen.color_data = color_datas[index]
        index = (index + 1) % len(screens)
        offset_screens.append(offset_screen)
    return offset_screens


def randomize_color_frames(screens: List[petscii_screen], seed: int):
    color_datas = []
    for screen in screens:
        color_datas.append([] + screen.color_data)

    random.Random(seed).shuffle(color_datas)

    for idx, screen in enumerate(screens):
        screen.color_data = color_datas[idx]

    return screens
