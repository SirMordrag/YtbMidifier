# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import statistics

from PIL import Image
import numpy as np
from statistics import mode
import cv2
from midiutil.MidiFile import MIDIFile

note_names = []

colors_all = {}
colors_keys = {}
colors_notes = {}
keys = {}


def init(key_image, key_image_row, starting_key, note_colors):
    global keys, colors_notes, colors_keys, colors_all, note_names

    note_names = ["c", "c#", "d", "d#", "e", "f", "f#", "g", "g#", "a", "a#", "b"]
    colors_notes = note_colors
    colors_all.update(colors_notes)
    colors_keys = colors_keys = {"white": (255, 255, 255),
                                 "black": (0, 0, 0)}
    colors_all.update(colors_keys)

    keys = detect_keys(_get_pixel_row(key_image, key_image_row), starting_key)


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


def _get_pixel_row(image, row):
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
    for key in kb:
        if key[1] - key[0] < min_black_key_length:
            kb.remove(key)
    return kb


def detect_notes(row, detected_from_keys=False):
    colors = colors_all if detected_from_keys else colors_notes
    discreet_colors = discretize_colours(colors, row)
    played_notes = {}
    for color in colors_notes.keys():
        played_notes[color] = []
    played_notes.pop("black")
    for key in keys.keys():
        line = discreet_colors[keys[key][0]:keys[key][1]]
        try:
            line_color = mode(line)
        except statistics.StatisticsError:
            continue
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


def write_to_midi(channels, fpq):
    mf = MIDIFile(len(channels))

    track = 0
    for key in channels.keys():
        mf.addTrackName(track, 0, key)
        for note in keys.keys():
            note_strokes = _get_note_strokes(note, channels[key])
            for stroke in note_strokes:
                start, dur = _frames_to_qnotes(stroke[0], fpq), _frames_to_qnotes(stroke[1], fpq)
                if dur > 0:
                    mf.addNote(track, 0, _sci_note_to_midi_pitch(note), start, dur, 100)  # fixme duration

        track += 1

    with open("output.mid", 'wb') as outf:
        mf.writeFile(outf)


def _get_note_strokes(note, channel):
    strokes = []  # (start, dur)
    flag = 0
    start = 0
    for idx, played_notes in enumerate(channel):
        if flag == 0:
            if note in played_notes:  # start
                start = idx
                flag = 1
        else:
            if note not in played_notes:  # end
                flag = 0
                strokes.append((start, idx - start))
    else:
        if flag == 1:
            strokes.append((start, idx - start))
    print(note, strokes)
    return strokes


def _frames_to_qnotes(frames, fpq):
    qnotes = frames / fpq
    return round(qnotes, 2)


def _sci_note_to_midi_pitch(note):
    tone = note[0:-1]
    octave = note[-1]
    pitch = 12 + note_names.index(tone) + int(octave) * 12
    return pitch



def main():
    starting_key = ("a", 0)
    note_colors = {"black": (0, 0, 0),
                   "blue": (2, 17, 255),
                   "green": (73, 246, 42),
                   # "purple": (138, 69, 255),
                   # "red": (252, 72, 23),
                   # "yellow": (251, 246, 56),
                   }
    start_time = 2.5
    stop_time = 91

    bpm = 85

    im_notes = Image.open("notes_3.PNG")
    im_keys = Image.open("keys.PNG")

    # init(im_keys, 1, starting_key, note_colors)

    played_notes = []

    video = cv2.VideoCapture('vid.mp4')
    fps = video.get(cv2.CAP_PROP_FPS)
    frames_per_qnote = 60 * (fps/bpm)
    currentframe = 0
    while True:
        ret, frame = video.read()

        if not ret:
            break

        currentframe += 1
        if currentframe / fps < start_time:
            continue
        elif stop_time is not None and currentframe / fps > stop_time:
            break

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(frame)
        im_notes_pix = _get_pixel_row(image, 615)
        if currentframe == start_time * fps:
            init(image, 615, starting_key, note_colors)

        played_notes.append(detect_notes(im_notes_pix, True))

        if currentframe % fps == 0:
            print(f"Processed {int(currentframe / fps)} seconds")

    video.release()
    cv2.destroyAllWindows()

    channels = {}
    for col in colors_notes.keys():
        if col == "black":
            continue
        channels[col] = []
        for row in played_notes:
            channels[col].append(row[col])

    for col in colors_notes:
        if col == "black":
            continue
        print(channels[col])

    write_to_midi(channels, frames_per_qnote)


if __name__ == '__main__':
    main()
