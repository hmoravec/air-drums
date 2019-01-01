"""Module with class representing percussion."""

import logging
from typing import Tuple

import cv2
import simpleaudio as sa
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
        self.sound = sa.WaveObject.from_wave_file(sound_path)
        self.sound_with_volume = self.sound

    def add_percussion_position(self, image: np.ndarray):
        """Draw percussion to image."""
        image = cv2.circle(image, self.center_position, self.radius, (0, 255, 0), 2)
        return image

    def play(self, controller: Controller):
        """Play the percussion."""
        LOG.debug('Playing drum.')
        if controller.velocity is not None:
            volume = np.log2(1 + controller.velocity / controller.velocity_max_volume)
            self.sound_with_volume = self.set_volume(self.sound, volume)
        self.sound_with_volume.play()

    @staticmethod
    def set_volume(wave_object: sa.WaveObject, volume: float) -> sa.WaveObject:
        """Return wave_object with set absolute volume.

        Minimal volume = 0, maximal volume = 1.

        The audio data has to be rounded to integers after volume change
        so there can be a slight sound distortion if the volume is repeatedly changed
        on the same audio data. To prevent this, change volume always from the
        original audio data.
        """
        if volume < 0:
            volume = 0
        if volume > 1:
            volume = 1
        audio_data = np.frombuffer(wave_object.audio_data, dtype=np.int16)
        volume_factor = volume * 32767 / np.max(np.abs(audio_data))
        audio_data = np.int16(audio_data * volume_factor)
        wave_object = sa.WaveObject(
            audio_data, wave_object.num_channels, wave_object.bytes_per_sample,
            wave_object.sample_rate)
        return wave_object

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
