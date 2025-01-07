from typing import List

import petscii
from utils import Block


def find_areas_with_content(screens: List[petscii.PetsciiScreen]):
    min_y = 25
    max_y = 0
    min_x = 40
    max_x = 0

    for screen in screens:
        for y in range(25):
            for x in range(40):
                offset = y * 40 + x
                if screen.screen_codes[offset] != 0:
                    if x > max_x:
                        max_x = x
                    if x < min_x:
                        min_x = x
                    if y > max_y:
                        max_y = y
                    if y < min_y:
                        min_y = y

    return Block(min_x, min_y, max_x - min_x + 1, max_y - min_y + 1)
