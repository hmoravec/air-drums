"""Module with class representing percussion."""

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

        # Lower buffer has lower latency but cannot process too many sounds in a short time
        mixer.init(frequency=22050, size=-16, channels=2, buffer=2**8)
        self.sound = mixer.Sound(sound_path)
        # simpleaudio package has lower latency but no volume
        # self.sound = simpleaudio.WaveObject.from_wave_file(sound_path)

    def add_percussion_position(self, image: np.ndarray):
        """Draw percussion to image."""
        image = cv2.circle(image, self.center_position, self.radius, (0, 255, 0), 2)
        return image

    def play(self, controller: Controller):
        """Play the percussion."""
        LOG.debug('Playing drum.')
        if controller.velocity is not None:
            volume = np.log2(1 + controller.velocity / controller.velocity_max_volume)
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
