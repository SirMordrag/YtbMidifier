"""
    Detect notes from video frames
"""
import random

from src.syn_video import SynVideo
import numpy as np
import csv
import os


class SynColorSet:
    def __init__(self, color_set):
        self.as_dict = dict()
        self.as_list = list()
        self.names = list()
        self.as_array = None

        self.update(color_set)
        self._update_sets()

    def update(self, new_colors):
        if isinstance(new_colors, dict):
            self.as_dict.update(new_colors)
        elif isinstance(new_colors, SynColorSet):
            self.as_dict.update(new_colors.as_dict)
        else:
            raise TypeError(f"Wrong type for updating set: {type(new_colors)}")

        self._update_sets()

    def get(self, color):
        return self.as_dict[color]

    def _update_sets(self):
        self.as_list = list(self.as_dict.values())
        self.names = list(self.as_dict.keys())
        self.as_array = np.array(self.as_list)

    def match_color(self, color_to_match):
        if not isinstance(color_to_match, np.ndarray):
            color_to_match = np.array(color_to_match)
        distances = np.sqrt(np.sum((self.as_array - color_to_match) ** 2, axis=1))
        index_of_smallest = int(np.where(distances == np.amin(distances))[0][0])
        color_name = self.names[index_of_smallest]
        return color_name


class SynOutput:
    output_csv_file_path = "..//keys_by_frame"

    def __init__(self, keys: list):
        self.keys = keys
        self.idx = 0
        self.data = list()
        self.data.append([self.idx, *keys])

    def new_row(self):
        self.idx += 1
        self.data.append([0] * (len(self.keys) + 1))
        self.data[self.idx][0] = self.idx

    def insert(self, key, value):
        ptr = self.keys.index(key) + 1
        self.data[self.idx][ptr] = value

    def save_csv(self):
        filename = SynOutput.output_csv_file_path
        if os.path.isfile(filename + ".csv") and not os.access(filename + ".csv", os.W_OK):
            filename = filename + "_" + str(random.randint(0, 100000))
        with open(filename + ".csv", 'w', newline='') as file:
            writer = csv.writer(file, delimiter=';')
            writer.writerows(self.data)


class SynReader:
    def __init__(self, syn_video: SynVideo, syn_config: dict):
        self.syn_video = syn_video

        self.colors_all = {}
        self.colors_keys = {}
        self.colors_notes = {}
        self.keys = {}

        self.note_names = ["c", "c#", "d", "d#", "e", "f", "f#", "g", "g#", "a", "a#", "b"]
        self.starting_key = syn_config["starting_key"]

        self.colors_notes = SynColorSet(syn_config["note_colors"])
        self.colors_keys = SynColorSet(syn_config["key_colors"])
        self.colors_all = SynColorSet(self.colors_notes)
        self.colors_all.update(self.colors_keys)

        self.output = None

        self.do()

    def do(self):
        row = self.syn_video.read()
        self.detect_keys(row)
        self.output = SynOutput(list(self.keys.keys()))

        while not self.syn_video.is_finished:
            row = self.syn_video.read()
            self.detect_notes(row)

            if self.syn_video.idx_last_read_frame % self.syn_video.fps == 0:
                print(f"Processed {self.syn_video.idx_last_read_frame // self.syn_video.fps} seconds")

        self.output.save_csv()
        self.syn_video.release()

    def detect_notes(self, row):
        self.output.new_row()
        for key in self.keys.keys():
            pixels_of_key = row[self.keys[key][0]:self.keys[key][1]]
            color_of_key = self._find_average_color_of_list(pixels_of_key, self.colors_all)
            if color_of_key in self.colors_keys.names:  # do not insert non-pressed keys
                value_of_key = 0
            else:
                value_of_key = color_of_key

            self.output.insert(key, value_of_key)

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
        discreet_colors = self._find_colors_of_list(row, self.colors_keys)

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

    @staticmethod
    def _find_colors_of_list(row: list, color_set: SynColorSet):
        colored_pixels = []
        for pix in row:
            colored_pixels.append(color_set.match_color(pix))
        return colored_pixels

    @staticmethod
    def _find_average_color_of_list(pixels, color_set: SynColorSet):
        avg_pix = [sum(x)//len(pixels) for x in zip(*pixels)]
        return color_set.match_color(avg_pix)
