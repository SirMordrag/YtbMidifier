"""
    Contains entry point for the app. Both console and GUI.
"""

from src.syn_processor import SynProcessor, save_frame, get_frame
from src.score_writer import ScoreWriter


def main():
    path = "vid.mp4"

    proc_config = {
        "path": path,
        "start_time": 3,
        "stop_time": 8,
        "row": 640,
    }

    syn_config = {
        "starting_key": ("a", 0),
        "note_colors": {"black": (17, 14, 15),
                        "red": (230, 13, 17),
                        },
        "key_colors": {"white": (144, 144, 144),
                       "black": (15, 15, 15)},
    }

    score_config = {
        "signature": (4, 4),
        "tempo": 110,
        "fps": 30,
    }

    save_frame(get_frame(path, 3))

    sp = SynProcessor(proc_config, syn_config)
    sp.release()
    print(sp.notes_by_frame)

    sw = ScoreWriter(score_config, syn_config)
    sw.keys = sp.keys
    sw.process(sp.notes_by_frame)


if __name__ == '__main__':
    main()
