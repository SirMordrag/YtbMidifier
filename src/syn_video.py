"""
    Wrapper for video file, which allows for reading frame-by-frame of certain row
"""

import numpy
import cv2


class SynVideo:
    def __init__(self, filename):
        self.video = cv2.VideoCapture(filename)
        self.fps = self.video.get(cv2.CAP_PROP_FPS)
        
        self.row = None
        self.start_frame = 0
        self.stop_frame = None
        self.frame = None
        self.idx_last_read_frame = -1
        
        self.is_initialized = False
        self.is_finished = False
        
    def show_video_frame(self):
        raise NotImplementedError()

    def release(self):
        self.video.release()
    
    def init_reading(self, row, start_time=0, stop_time=None, fps=None):
        if fps:
            self.fps = fps
        self.row = row
        self.start_frame = int(start_time * self.fps)
        if self.start_frame > 0:
            self.video.set(cv2.CAP_PROP_POS_FRAMES, self.start_frame - 1)
        if stop_time:
            self.stop_frame = int(stop_time * self.fps)
        else:
            self.stop_frame = self.video.get(cv2.CAP_PROP_FRAME_COUNT)

        self._read_frame()
        self.is_initialized = True
        self._info()
    
    def read(self) -> numpy.array:
        if not self.is_initialized:
            self._info()
            self.release()
            raise ValueError("SynVideo not initialized!")
        elif self.is_finished:
            self._info()
            self.release()
            raise ValueError("Reading finished, no more frames to read!")
        
        return self.frame[self.row]

    def _read_frame(self):
        ret, self.frame = self.video.read()
        self.idx_last_read_frame += 1

        if self.idx_last_read_frame > self.stop_frame:
            self.is_finished = True
            self.frame = None
            self.release()
            print("Finished")
            self._info()
        elif not ret:
            self._info()
            self.release()
            raise ValueError("Error while reading frame")

    def _info(self, do_print=True):
        out = "SynVideo runtime info:\r\n"
        out += f"LAST READ FRAME: {self.idx_last_read_frame}, FRAME OK: {self.frame is not None}, " \
               f"VIDEO OK: {bool(self.video)}, INITIALIZED: {self.is_initialized}, FINISHED: {self.is_finished}"
        out += "\r\n"
        out += f"FPS: {self.fps}, ROW: {self.row}, START_FR = {self.start_frame}, STOP_FR: {self.stop_frame}"
        out += "\r\n"
        if do_print:
            print(out)
        return out
