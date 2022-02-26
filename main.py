# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

from PIL import Image
import numpy as np
from statistics import mode

note_names = ["c", "c#", "d", "d#", "e", "f", "f#", "g", "g#", "a", "a#", "b"]

colors_all = {}
colors_keys = {"white": (255, 255, 255),
               "black": (0, 0, 0)}
colors_all.update(colors_keys)

colors_notes = {"black": (0, 0, 0),
                "blue": (2, 17, 255),
                "green": (73, 246, 42),
                "purple": (138, 69, 255),
                "red": (252, 72, 23),
                "yellow": (251, 246, 56),
                }
colors_all.update(colors_notes)


def init(key_image, key_image_row, starting_key):
    pass


def _to_image(row, name="new", show=False):
    pixels = []
    for pix in row:
        pixels.append(colors_all[pix])

    array = np.array([pixels for _ in range(50)], dtype=np.uint8)

    # Use PIL to create an image from the new array of pixels
    new_image = Image.fromarray(array)
    new_image.save(name + '.png')
    if show:
        new_image.show()


def _color_distance(col1, col2):
    return np.sqrt((col1[0] - col2[0]) ** 2 + (col1[1] - col2[1]) ** 2 + (col1[2] - col2[2]) ** 2)


def get_pixel_row(image, row):
    pix_row = []
    for i in range(image.size[0]):
        pix_row.append(image.getpixel((i, row)))
    return pix_row


def detect_keys(row, starting_key):
    # get discreet colors of pixels
    discreet_colors = discretize_colours(colors_keys, row)
    # _to_image(discreet_colors, "keys_d")

    # get strip lengths
    keys_black, keys_white = _get_key_lengths(discreet_colors)

    # remove spaces between white keys
    keys_black = _remove_spaces(keys_black)

    # join lists
    key_ranges = keys_black + keys_white
    key_ranges.sort(key=lambda y: y[0])

    # name keys
    keys = {}
    i = 0
    octave = starting_key[1]
    while note_names[i] != starting_key[0]:  # go to starting key
        i += 1

    for key in key_ranges:
        if i >= len(note_names):
            i = 0
            octave += 1
        keys[note_names[i] + str(octave)] = key
        i += 1

    return keys


def _get_key_lengths(pix_list):
    i = 0
    keys_white = []
    keys_black = []
    while i < len(pix_list) - 1:
        if pix_list[i] == "black":
            key_start = i
            while pix_list[i] == "black" and i < len(pix_list) - 1:
                i += 1
            else:
                key_end = i - 1
            keys_black.append((key_start, key_end))
        if pix_list[i] == "white":
            key_start = i
            while pix_list[i] == "white" and i < len(pix_list) - 1:
                i += 1
            else:
                key_end = i - 1
            keys_white.append((key_start, key_end))

    return keys_black, keys_white


def _remove_spaces(kb):
    lengths = []
    for key in kb:
        lengths.append(key[1] - key[0])
    min_black_key_length = np.histogram(np.array(lengths), 2)[0][0]
    print(min_black_key_length)
    for key in kb:
        if key[1] - key[0] < min_black_key_length:
            kb.remove(key)
    return kb


def detect_notes(keys, row, detected_from_keys=False):
    colors = colors_all if detected_from_keys else colors_notes
    discreet_colors = discretize_colours(colors, row)
    played_notes = {}
    for color in colors_notes.keys():
        played_notes[color] = []
    played_notes.pop("black")
    for key in keys.keys():
        line = discreet_colors[keys[key][0]:keys[key][1]]
        line_color = mode(line)
        if line_color not in colors_keys.keys():
            played_notes[line_color].append(key)
    return played_notes


def discretize_colours(colors, row):
    colored_pixels = []
    for i, pix in enumerate(row):
        dist_vector = []
        for col in colors.keys():
            dist_vector.append(_color_distance(pix, colors[col]))
        colored_pixels.append(list(colors.keys())[np.array(dist_vector).argmin()])
    return colored_pixels


def main():
    starting_key = ("a", 0)

    im_notes = Image.open("notes_3.PNG")
    im_keys = Image.open("keys.PNG")

    im_notes_pix = get_pixel_row(im_notes, 1)
    im_keys_pix = get_pixel_row(im_keys, 1)

    keys = detect_keys(im_keys_pix, starting_key)
    played_notes = detect_notes(keys, im_notes_pix, True)
    print(played_notes)


if __name__ == '__main__':
    main()
