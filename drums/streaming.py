"""Video streaming from webcamera."""

from collections import namedtuple
import logging
import time
from typing import Deque, TYPE_CHECKING

import cv2

from drums.frame import Frame
if TYPE_CHECKING:
    from drums.drum_set import DrumSet


LOG = logging.getLogger(__name__)


ImageSize = namedtuple('ImageSize', 'width height')


class InputVideoStream:
    """Input video streaming."""

    #: Stream source (0 = web camera)
    STREAM_SOURCE = 0
    #: Maximal input image size (width or height).
    #: It will be more, if the camera does not support less.
    MAX_INPUT_IMAGE_WIDTH_OR_HEIGHT = 800
    #: If the width of input stream is more, resize it to this width.
    MAX_OUTPUT_IMAGE_WIDTH = 640
    #: Sleep interval between reading two frames from the stream.
    LOOP_SLEEP = 0.001
    #: Codec code of the stream (MJPG). Could be changed to 844715353 (YUY2)
    CODEC = 1196444237
    #: FPS of the input stream (if the stream source supports it).
    FPS = 30

    def __init__(self, frames: Deque[Frame] = None, stream_source: int = STREAM_SOURCE):
        LOG.debug('Initializing input video stream.')
        self.stream = cv2.VideoCapture(stream_source)
        self.image_size = ImageSize(None, None)
        self.frames = frames
        self.stream_enabled = True
        self.frame_count = 0
        self.fps = 0
        self.stream_start_time = None

        # Setup image size and connect to stream by reading the first frame
        self._setup_stream()
        self.stream.read()

    def _setup_stream(self):
        """Set up image size."""
        self.stream.set(cv2.CAP_PROP_FPS, InputVideoStream.FPS)
        self.stream.set(cv2.CAP_PROP_FOURCC, InputVideoStream.CODEC)
        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH,
                        InputVideoStream.MAX_INPUT_IMAGE_WIDTH_OR_HEIGHT)
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT,
                        InputVideoStream.MAX_INPUT_IMAGE_WIDTH_OR_HEIGHT)

        input_image_size = ImageSize(
            width=self.stream.get(cv2.CAP_PROP_FRAME_WIDTH),
            height=self.stream.get(cv2.CAP_PROP_FRAME_HEIGHT))
        image_scaling_factor = (
            min(input_image_size.width, InputVideoStream.MAX_OUTPUT_IMAGE_WIDTH)
            / input_image_size.width)
        self.image_size = ImageSize(
            width=int(input_image_size.width * image_scaling_factor),
            height=int(input_image_size.height * image_scaling_factor))

    def start_stream(self):
        """Start input video stream."""
        LOG.debug('Starting input video stream.')
        self.stream_start_time = time.time()
        while self.stream_enabled:
            # Sleep a bit to leave more time to other threads
            time.sleep(InputVideoStream.LOOP_SLEEP)
            self._refresh_fps()
            frame = self.read_frame()
            self.frames.append(frame)
        self.stream.release()

    def stop_stream(self):
        """Stop stream."""
        LOG.debug('Stopping input video stream.')
        self.stream_enabled = False

    def read_frame(self) -> Frame:
        """Return frame from video stream."""
        frame = Frame(*self.stream.read(), fps=self.fps, frame_count=self.frame_count)
        frame = self._preprocess_frame(frame)
        return frame

    def _preprocess_frame(self, frame: Frame) -> Frame:
        """Preprocess frame before passing it to tracking."""
        # Decrease image resolution for better performance
        frame.image = cv2.resize(frame.image, dsize=self.image_size)

        # Flip image so the drummers see themselves as in a mirror
        frame.image = cv2.flip(frame.image, 1)

        return frame

    def _refresh_fps(self):
        self.frame_count += 1
        self.fps = self.frame_count / (time.time() - self.stream_start_time)


class OutputVideoStream:
    """Output video stream with added percussion and tracked controllers.."""

    IMAGE_TEXT_PARAMETERS = {'fontFace': cv2.FONT_HERSHEY_SIMPLEX,
                             'fontScale': 0.5, 'color': (0, 0, 255), 'thickness': 2}
    #: Sleep interval between outputing two frames [ms]
    LOOP_SLEEP = 10

    def __init__(self, drum_set: 'DrumSet', frames: Deque[Frame] = None):
        LOG.debug('Initializing output video stream.')
        self.stream_enabled = True
        self.frames = frames
        self.drum_set = drum_set

    def start_stream(self):
        """Stream frames from the queue to output with added information."""
        LOG.debug('Starting output video stream.')
        while self.stream_enabled:
            if not self.frames:
                continue
            frame = self.frames.popleft()
            self._render_frame(frame)
        cv2.destroyAllWindows()

    def stop_stream(self):
        """Stop output stream."""
        LOG.debug('Stopping output video stream.')
        self.stream_enabled = False

    def _render_frame(self, frame: Frame):
        """Show frame with added FPS, lag, controllers and percussion."""
        # Show FPS in frame
        cv2.putText(frame.image, f'FPS: {frame.fps:.0f} f/s', (10, 20),
                    **OutputVideoStream.IMAGE_TEXT_PARAMETERS)
        # Show lag between current time and frame timestamp
        lag = (time.time() - frame.timestamp)
        cv2.putText(frame.image, f'Lag: {lag:.2f} s', (10, 40),
                    **OutputVideoStream.IMAGE_TEXT_PARAMETERS)

        # Draw controllers and percussion
        for controller in self.drum_set.controllers:
            frame.image = controller.add_controller_position(frame.image)
        for percussion in self.drum_set.percussion:
            frame.image = percussion.add_percussion_position(frame.image)

        # Show the frame in window
        cv2.imshow('Air drums', frame.image)
        # Sleep a bit so the image can be rendered
        cv2.waitKey(OutputVideoStream.LOOP_SLEEP)
