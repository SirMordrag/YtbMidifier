"""
    Detect notes from video frames
"""

from statistics import mode, StatisticsError
import numpy as np


class SynReader:
    def __init__(self, syn_config):
        self.colors_all = {}
        self.colors_keys = {}
        self.colors_notes = {}
        self.keys = {}

        self.note_names = ["c", "c#", "d", "d#", "e", "f", "f#", "g", "g#", "a", "a#", "b"]
        self.starting_key = syn_config["starting_key"]
        self.colors_notes = syn_config["note_colors"]
        self.colors_all.update(self.colors_notes)
        self.colors_keys = syn_config["key_colors"]
        self.colors_all.update(self.colors_keys)

        self.notes_by_frame = []

    def _color_distance(self, col1, col2):
        return np.sqrt((col1[0] - col2[0]) ** 2 + (col1[1] - col2[1]) ** 2 + (col1[2] - col2[2]) ** 2)

    def detect_keys(self, row):
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
            min_black_key_length = int(np.median(np.array(lengths)) / 2)

            for key in kb:
                if key[1] - key[0] < min_black_key_length:
                    kb.remove(key)
            return kb

        # get discreet colors of pixels
        discreet_colors = self.discretize_colours(self.colors_keys, row)
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
        octave = self.starting_key[1]
        while self.note_names[i] != self.starting_key[0]:  # go to starting key
            i += 1

        for key in key_ranges:
            if i >= len(self.note_names):
                i = 0
                octave += 1
            keys[self.note_names[i] + str(octave)] = key
            i += 1

        self.keys = keys

    def detect_notes(self, row, detected_from_keys=True):
        colors = self.colors_all if detected_from_keys else self.colors_notes
        discreet_colors = self.discretize_colours(colors, row)
        played_notes = {}
        for color in self.colors_notes.keys():
            played_notes[color] = []
        played_notes.pop("black")
        for key in self.keys.keys():
            line = discreet_colors[self.keys[key][0]:self.keys[key][1]]
            try:
                line_color = mode(line)
            except StatisticsError:
                continue
            if line_color not in self.colors_keys.keys():
                played_notes[line_color].append(key)
        self.notes_by_frame.append(played_notes)

    def discretize_colours(self, colors, row):
        colored_pixels = []
        for i, pix in enumerate(row):
            dist_vector = []
            for col in colors.keys():
                dist_vector.append(self._color_distance(pix, colors[col]))
            colored_pixels.append(list(colors.keys())[np.array(dist_vector).argmin()])
        # to_image(colored_pixels, self.colors_all)
        return colored_pixels
