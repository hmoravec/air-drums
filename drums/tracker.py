"""Tracking of controllers."""

import logging
import time
from typing import Deque, Iterable

from drums.controllers import Controller
from drums.drum_set import DrumSet
from drums.frame import Frame


LOG = logging.getLogger(__name__)


class Tracker:
    """Tracker of controllers."""

    #: Sleep interval between tracking of two frames
    LOOP_SLEEP = 0.001

    def __init__(self, frames_to_track: Deque[Frame],
                 frames_tracked: Deque[Frame], drum_set: DrumSet):
        self.frames_to_track = frames_to_track
        self.frames_tracked = frames_tracked
        self.drum_set = drum_set

    def start_tracker(self):
        """Start tracking of controllers in frames."""
        while True:
            # Sleep a bit to leave more time to other threads
            time.sleep(Tracker.LOOP_SLEEP)
            self._log_queue_lengths()
            if not self.frames_to_track:
                continue
            frame_to_track = self.frames_to_track.popleft()
            frame_tracked = self.track_controllers_in_frame(
                frame_to_track, self.drum_set.controllers)
            self.drum_set.play()
            self.frames_tracked.append(frame_tracked)

    @staticmethod
    def track_controllers_in_frame(frame: Frame, controllers: Iterable[Controller]):
        """Track controllers in frame by colors tracking."""
        for controller in controllers:
            mask = controller.get_controller_mask(frame)
            controller.position = controller.get_largest_contour_center(mask)

        return frame

    def _log_queue_lengths(self):
        LOG.debug('Frames to track: %s.', len(self.frames_to_track))
        LOG.debug('Frames tracked: %s.', len(self.frames_tracked))
