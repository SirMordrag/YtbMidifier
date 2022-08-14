"""
    Convert frame-by-frame notes to MusicXML
"""

from pymusicxml import *


class ScoreWriter:
    def __init__(self, score_config, syn_config):
        self.frames_per_qnote = 60 * (score_config["fps"] / score_config["tempo"])
        self.colors_all = {}
        self.colors_keys = {}
        self.colors_notes = {}
        self.keys = {}

        self.note_names = ["c", "c#", "d", "d#", "e", "f", "f#", "g", "g#", "a", "a#", "b"]
        self.note_names_with_pich = [(note + str(pitch)) for pitch in range(0, 9) for note in self.note_names]
        self.starting_key = syn_config["starting_key"]
        self.colors_notes = syn_config["note_colors"]
        self.colors_all.update(self.colors_notes)
        self.colors_keys = syn_config["key_colors"]
        self.colors_all.update(self.colors_keys)

    def process(self, played_notes):
        nbfd = self._notes_by_frame_to_note_frame_durations(played_notes)




    def _notes_by_frame_to_note_frame_durations(self, notes_by_frame):
        # split into channels
        channel_names = notes_by_frame[0].keys()

        channels = {}
        for name in channel_names:
            channels[name] = list()

        for fr in notes_by_frame:  # fr ... dict
            for k in fr.keys():
                channels[k].append(fr[k])
        # <channels> now contains keys for every channel, which contain list of frames, each a list of notes

        # convert to note frame durations
        # <note_frame_durations>: dictionary by channel, each list of tuples (note, start, duration in frames)
        note_frame_durations = {}
        for ch in channels.keys():
            note_frame_durations[ch] = list()

            for note in self.note_names_with_pich:
                start_fr = None
                for i, fr in enumerate(channels[ch]):
                    if start_fr is None and note in fr:
                        start_fr = i
                    elif start_fr is not None and note in fr:
                        continue
                    elif start_fr is not None and note not in fr:
                        note_frame_durations[ch].append((note, start_fr, i - start_fr))
                        start_fr = None

        # sort
        for k in note_frame_durations.keys():
            note_frame_durations[k].sort(key=lambda y: y[1])
        print(note_frame_durations)
        return note_frame_durations



    def write_to_midi(self, channels, fpq):
        mf = None

        track = 0
        for key in channels.keys():
            mf.addTrackName(track, 0, key)
            for note in self.keys.keys():
                note_strokes = self._get_note_strokes(note, channels[key])
                for stroke in note_strokes:
                    start, dur = self._frames_to_qnotes(stroke[0], fpq), self._frames_to_qnotes(stroke[1], fpq)
                    if dur > 0:
                        mf.addNote(track, 0, self._sci_note_to_midi_pitch(note), start, dur, 100)

            track += 1

        with open("output.mid", 'wb') as outf:
            mf.writeFile(outf)

    def _get_note_strokes(self, note, channel):
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

    def _frames_to_qnotes(self, frames, fpq):
        qnotes = frames / fpq
        return round(qnotes, 2)

    def _sci_note_to_midi_pitch(self, note):
        tone = note[0:-1]
        octave = note[-1]
        pitch = 12 + self.note_names.index(tone) + int(octave) * 12
        return pitch
