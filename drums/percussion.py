"""Module with class representing air drums."""

import logging
from typing import Tuple

import cv2
from pygame import mixer
import numpy as np

from drums.controllers import Controller


LOG = logging.getLogger(__name__)


class Percussion:
    """Percussion instrument (e.g. drum or cymbal)."""

    def __init__(self, name: str, sound_path: str,
                 center_position: Tuple[float, float], radius: float):
        self.name = name
        self.sound_path = sound_path
        self.center_position = center_position
        self.radius = radius

        self.currently_playing_controllers = set()

        mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        self.sound = mixer.Sound(sound_path)

    def add_percussion_position(self, image: np.ndarray):
        """Draw percussion to image."""
        image = cv2.circle(image, self.center_position, self.radius, (0, 255, 0), 2)
        return image

    def play(self, volume: float = 1):
        """Play the percussion."""
        # TODO: Change volume based on controller speed.
        LOG.debug('Playing drum.')
        self.sound.set_volume(volume)
        self.sound.play()

    def is_played(self, controller: Controller):
        """Check if the percussion is played."""
        if not controller.position:
            return False
        if np.linalg.norm(np.asarray(self.center_position)
                          - np.asarray(controller.position)) < self.radius:
            if controller.name not in self.currently_playing_controllers:
                self.currently_playing_controllers.add(controller.name)
                return True
        elif controller.name in self.currently_playing_controllers:
            self.currently_playing_controllers.remove(controller.name)
        return False
