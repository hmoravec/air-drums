"""Module managing the whole air drums process."""

from collections import deque
import logging
from threading import Thread
import sys

import drums.settings
from drums.drum_set import DrumSet
from drums.streaming import InputVideoStream, OutputVideoStream
from drums.tracker import Tracker


LOG = logging.getLogger(__name__)


class Interface:
    """Interface that is handling the whole air drums app."""

    #: Maximal length of the queue with frames.
    DEQUE_MAX_LENGTH = 50
    #: Small thread switch interval to prevent lags in processing.
    THREAD_SWITCH_INTERVAL = 0.0001

    def __init__(self, settings: drums.settings.Settings,
                 deque_max_length: int = DEQUE_MAX_LENGTH):
        self.frames_to_track = deque(maxlen=deque_max_length)
        self.frames_tracked = deque(maxlen=deque_max_length)
        self.settings = settings
        self.drum_set = DrumSet(self.settings)
        sys.setswitchinterval(Interface.THREAD_SWITCH_INTERVAL)

    def start_interface(self):
        """Calibrate controllers, run input stream, tracking and output video stream."""
        LOG.debug('Starting interface.')

        for controller in self.drum_set.controllers:
            controller_settings = self.settings.settings['controllers'][controller.key]
            controller.calibrate_color(controller_settings)
            self.settings.save_settings()

        input_video_stream = InputVideoStream(frames=self.frames_to_track)
        tracker = Tracker(self.frames_to_track, self.frames_tracked, self.drum_set)

        output_video_stream = OutputVideoStream(drum_set=self.drum_set, frames=self.frames_tracked)

        input_thread = Thread(name='input_stream',
                              target=input_video_stream.start_stream)
        tracker_thread = Thread(name='tracker',
                                target=tracker.start_tracker)
        input_thread.start()
        tracker_thread.start()
        output_video_stream.start_stream()
