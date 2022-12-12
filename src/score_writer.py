"""
    Convert frame-by-frame notes to MusicXML
"""

from midiutil.MidiFile import MIDIFile


class ScoreWriter:
    def __init__(self, score_config, syn_config):
        self.frames_per_qnote = 60 * (score_config["fps"] / score_config["tempo"])
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

    def process(self, played_notes):
        channels = {}
        for col in self.colors_notes.keys():
            if col == "black":
                continue
            channels[col] = []
            for row in played_notes:
                channels[col].append(row[col])

        for col in self.colors_notes:
            if col == "black":
                continue
            # print(channels[col])

        self.write_to_midi(channels, self.frames_per_qnote)

    def write_to_midi(self, channels, fpq):
        mf = MIDIFile(len(channels), eventtime_is_ticks=True)

        track = 0
        for key in channels.keys():
            mf.addTrackName(track, 0, key)
            for note in self.keys.keys():
                note_strokes = self._get_note_strokes(note, channels[key])
                for stroke in note_strokes:
                    start, dur = stroke[0] * 1000, stroke[1] * 1000
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
