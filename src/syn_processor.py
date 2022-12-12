"""
    Processes video into frames and gives them to SynReader for note detection
"""

import cv2
import json
from src.syn_reader import SynReader


def get_frame(path, seconds):
    video = cv2.VideoCapture(path)
    fps = int(video.get(cv2.CAP_PROP_FPS))
    frame_no = seconds * fps
    video.set(cv2.CAP_PROP_POS_FRAMES, frame_no)
    ret, frame = video.read()
    video.release()

    if ret:
        return frame
    else:
        raise ValueError("Frame not found")


def save_frame(frame, filename="image", extension=".png"):
    cv2.imwrite(filename + extension, frame)


class SynProcessor(SynReader):
    def __init__(self, proc_config, syn_config):
        SynReader.__init__(self, syn_config)

        self.video = cv2.VideoCapture(proc_config["path"])

        self.fps = int(self.video.get(cv2.CAP_PROP_FPS))
        self.start_frame = proc_config["start_time"] * self.fps
        self.stop_frame = proc_config["stop_time"] * self.fps
        self.row = proc_config["row"]

        self.process_syn_video()

    def process_syn_video(self):
        # set index to startframe
        self.video.set(cv2.CAP_PROP_POS_FRAMES, self.start_frame)

        for index in range(self.stop_frame - self.start_frame):
            ret, frame = self.video.read()

            if not ret:
                print(f"WARNING:premature termination at frame {self.start_frame + index} of {self.stop_frame}")
                break

            # convert colors from BGR to RGB
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # crop the frame to the selected row
            frame = frame[self.row, :, :]

            if index == 0:
                self.detect_keys(frame)
            # give it to processing
            self.detect_notes(frame)

            # print progress
            if index % self.fps == 0:
                print(f"Processed {int(index / self.fps)} seconds")

        self.notes_by_frame_to_note_frame_durations()

    def release(self):
        self.video.release()
        cv2.destroyAllWindows()

    def save_output(self, filename="output"):
        with open(filename + ".txt", "w") as out:
            out.write(json.dumps(self.note_frame_durations))
