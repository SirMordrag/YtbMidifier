"""
    Contains entry point for the app. Both console and GUI.
"""

from src.syn_video import SynVideo
from src.syn_reader import SynReader
from src.score_writer import ScoreWriter


def main():
    path = "..\\vid.mp4"

    video_config = {
        "path": path,
        "start_time": "3:04",
        "stop_time": "9:03",
        "row": 550,
        "fps": 30
    }

    reader_config = {
        "starting_key": ("d#", 1),
        "key_colors": {"white": (253, 251, 231),
                       "black": (20, 18, 19)},
        "note_colors": {"blue": (139, 167, 203),
                        "green": (164, 243, 103),
                        },
    }

    score_config = {
        "signature": (4, 4),
        "tempo": 60,
        "fps": 30,
    }

    sv = SynVideo(path)
    sv.init_reading(**video_config)
    sv.init_reading(row=video_config["row"], start_time=video_config["start_time"],
                    stop_time=video_config["stop_time"], fps=video_config["fps"])
    sr = SynReader(sv, reader_config)

    # sw = ScoreWriter(score_config, syn_config)
    # sw.keys = sp.keys
    # sw.process(sp.notes_by_frame)


if __name__ == '__main__':
    main()
