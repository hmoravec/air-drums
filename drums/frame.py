"""Module with frame data container."""

import time

import numpy as np


class Frame:
    """Data container representing captured frame."""

    __slots__ = ('grabbed', 'image', 'fps', 'frame_count', 'timestamp')

    def __init__(self, grabbed: bool, image: np.ndarray, fps: float = None,
                 frame_count: int = None, timestamp: float = None):
        #: If the frame was grabbed correctly.
        self.grabbed = grabbed
        #: Grabbed image.
        self.image = image
        #: FPS calculated at the time of grabbing the frame.
        self.fps = fps
        #: Frames count since the start of streaming.
        self.frame_count = frame_count
        #: Timestamp of the frame.
        self.timestamp = timestamp or time.time()
