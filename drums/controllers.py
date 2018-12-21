"""Module with class representing drum sticks."""

import copy
from collections import namedtuple
import logging
from typing import List, Tuple, Iterator, Any, Dict

import cv2
import numpy as np

from drums.frame import Frame
from drums.streaming import InputVideoStream, OutputVideoStream


LOG = logging.getLogger(__name__)


class HSV(namedtuple('HSV', 'hue saturation value')):
    """Data class representing HSV color."""

    #: Minimum HSV color
    MINIMUM = (0, 0, 0)
    #: Maximum HSV color
    MAXIMUM = (180, 255, 255)

    __slots__ = ()

    def __add__(self, other: 'HSV') -> 'HSV':
        """Return element-wise sum. Cannot exceed maximum."""
        return HSV.minimum(HSV(*np.add(self, other)), HSV(*HSV.MAXIMUM))

    def __sub__(self, other: 'HSV') -> 'HSV':
        """Return element-wise difference. Cannot exceed minimum."""
        return HSV.maximum(HSV(*np.subtract(self, other)), HSV(*HSV.MINIMUM))

    @staticmethod
    def minimum(hsv_1: 'HSV', hsv_2: 'HSV') -> 'HSV':
        """Return element-wise minimum of both HSV."""
        return HSV(*(np.minimum(hsv_1, hsv_2)).tolist())

    @staticmethod
    def maximum(hsv_1: 'HSV', hsv_2: 'HSV') -> 'HSV':
        """Return element-wise maximum of both HSV."""
        return HSV(*(np.maximum(hsv_1, hsv_2)).tolist())

    def to_save_format(self) -> List[int]:
        """Transform HSV to format for saving to settings file."""
        return [int(number) for number in self]


class Controller:
    """Drum controllers: i.g. drum sticks and feet."""

    def __init__(self, key: str, name: str = None,
                 color_low: HSV = HSV(*HSV.MAXIMUM), color_high: HSV = HSV(*HSV.MINIMUM)):
        #: Unique key for controller
        self.key = key
        #: Name of controller
        self.name = name
        #: Low color bound for detecting controller
        self.color_low = color_low
        #: High color bound for detecting controller
        self.color_high = color_high
        #: Position of controller in image
        self.position = None

    def add_controller_position(self, image: np.ndarray) -> np.ndarray:
        """Draw controller position to image."""
        image = cv2.circle(image, self.position, 10, (255, 0, 0), -1)
        return image

    def calibrate_color(self, controller_settings: Dict[str, Any]):
        """Calibrate controller colors.

        Update them in the ``self`` and in the ``controller_settings``.
        """
        calibrator = Calibrator(self)
        calibrator.calibrate_color(self, controller_settings)

    @staticmethod
    def get_largest_contour_center(mask: np.ndarray) -> Tuple[float, float]:
        """Return center of largest contour in mask."""
        # Find contours in the mask
        contours = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = contours[-2]

        # Get the center of the largest contour
        if contours:
            centroid = max(contours, key=cv2.contourArea)
            centroid_moments = cv2.moments(centroid)
            controller_position = (
                int(centroid_moments["m10"] / centroid_moments["m00"]),
                int(centroid_moments["m01"] / centroid_moments["m00"])
            )
        else:
            controller_position = None

        return controller_position

    def get_controller_mask(self, frame: Frame) -> np.ndarray:
        """Get mask with controller area based on controller's color range."""
        frame = copy.deepcopy(frame)

        # Blur image to reduce noise
        frame.image = cv2.GaussianBlur(frame.image, (11, 11), 0)

        # Convert frame to HSV color space
        image_hsv = cv2.cvtColor(frame.image, cv2.COLOR_BGR2HSV)

        # Create a mask for the controller color
        mask = np.zeros(image_hsv.shape[:2], dtype=np.uint8)
        mask = cv2.inRange(image_hsv, self.color_low, self.color_high)

        # Remove small areas and smooth big areas
        mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)

        return mask


class Calibrator:
    """Class for calibrating controller colors."""

    HSV_AVERAGE_SPAN_LOW = HSV(10, 10, 10)
    HSV_AVERAGE_SPAN_HIGH = HSV(10, 100, 100)
    HSV_ITERATOR_STEP = HSV(10, 40, 40)

    def __init__(self, controller: Controller):
        #: Input stream for calibration
        self.stream = InputVideoStream()
        #: Low color bound for controller detection during calibration
        self.color_low = controller.color_low
        #: High color bound for controller detection during calibration
        self.color_high = controller.color_high
        #: Radius of circle for calibrating
        self.calibrating_circle_radius = 30
        #: Centers of circles for calibrating
        self.calibrating_circle_centers = (
            (width, height)
            for width in range(100, self.stream.image_size.width,
                               int(self.stream.image_size.width / 2))
            for height in range(100, self.stream.image_size.height,
                                int(self.stream.image_size.height / 2))
        )
        #: Flag if the calibration should stop
        self.stop_calibrating = False
        #: Flag if the calibration should move to the next calibrating point
        self.next_calibrating_point = False

    @staticmethod
    def get_colorspace_iterator(limits_low: HSV = HSV(*HSV.MINIMUM),
                                limits_high: HSV = HSV(*HSV.MAXIMUM),
                                span_low: HSV = HSV_AVERAGE_SPAN_LOW,
                                span_high: HSV = HSV_AVERAGE_SPAN_HIGH,
                                step: HSV = HSV_ITERATOR_STEP) -> Iterator[Tuple[HSV, HSV]]:
        """Return generator of HSV colors over HSV color space."""
        colorspace_iterator = (
            (HSV(hue - span_low.hue, saturation - span_low.saturation, value - span_low.value),
             HSV(hue + span_high.hue, saturation + span_high.saturation, value + span_high.value))
            for hue in range(limits_low.hue + span_low.hue,
                             limits_high.hue - span_high.hue,
                             step.hue)
            for saturation in range(limits_low.saturation + span_low.saturation,
                                    limits_high.saturation - span_high.saturation,
                                    step.saturation)
            for value in range(limits_low.value + span_low.value,
                               limits_high.value - span_high.value,
                               step.value)
        )

        return colorspace_iterator

    def calibrate_color(self, controller: Controller, controller_settings: Dict[str, Any]):
        """Calibrate colors of controller and update them in ``controller_settings``."""
        cv2.namedWindow('Image')
        cv2.moveWindow('Image', 100, 0)
        cv2.namedWindow('Mask')
        cv2.moveWindow('Mask', 100 + self.stream.image_size.width, 0)

        for circle_center in self.calibrating_circle_centers:
            if self.stop_calibrating:
                break
            self.next_calibrating_point = False
            while not (self.next_calibrating_point or self.stop_calibrating):
                frame = self.stream.read_frame()
                image = copy.deepcopy(frame.image)
                image_text = (
                    f'Calibrate of {controller.name}. '
                    'Keys: s/l=smaller/larger, r=reset, c=calibrate, n=next point, q=quit.'
                )
                image = cv2.putText(image, image_text, (10, 20),
                                    **OutputVideoStream.IMAGE_TEXT_PARAMETERS)
                image = cv2.circle(image, circle_center,
                                   self.calibrating_circle_radius, (255, 0, 0), 2)
                cv2.imshow('Image', image)
                mask = controller.get_controller_mask(frame)
                cv2.imshow('Mask', mask)
                self.check_pressed_key(controller, controller_settings, frame, circle_center)
        self.stream.stream.release()
        cv2.destroyAllWindows()

    def check_pressed_key(self, controller: Controller, controller_settings: Dict[str, Any],
                          frame: Frame, circle_center: Tuple[float, float]):
        """Do action based on pressed key."""
        pressed_key = cv2.waitKey(1)

        if pressed_key == ord('n'):
            controller_settings['color_low'] = HSV.to_save_format(controller.color_low)
            controller_settings['color_high'] = HSV.to_save_format(controller.color_high)
            self.next_calibrating_point = True

        if pressed_key == ord('s'):
            self.calibrating_circle_radius -= 10

        if pressed_key == ord('q'):
            self.stop_calibrating = True

        if pressed_key == ord('r'):
            controller.color_low = HSV(*HSV.MAXIMUM)
            controller.color_high = HSV(*HSV.MINIMUM)

        if pressed_key == ord('l'):
            self.calibrating_circle_radius += 10

        if pressed_key == ord('c'):
            mask = np.zeros(frame.image.shape[:2], dtype=np.uint8)
            mask = cv2.circle(mask, circle_center,
                              self.calibrating_circle_radius, (255, 0, 0), -1)
            image_hsv = cv2.cvtColor(frame.image, cv2.COLOR_BGR2HSV)
            average_color = HSV(*cv2.mean(image_hsv, mask)[:3])

            self.color_low = average_color - self.HSV_AVERAGE_SPAN_LOW
            self.color_high = average_color + self.HSV_AVERAGE_SPAN_HIGH
            controller.color_low = HSV.minimum(controller.color_low, self.color_low)
            controller.color_high = HSV.maximum(controller.color_high, self.color_high)
            LOG.debug('Controllers colors: %s - %s.', self.color_low, self.color_high)
