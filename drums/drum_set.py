"""Module with drum set."""

import drums.settings
from drums.controllers import Controller, HSV
from drums.percussion import Percussion


class DrumSet:
    """Air drums."""

    def __init__(self, settings: drums.settings.Settings):
        self.settings = settings
        self.percussion = [Percussion(percussion['name'],
                                      percussion['sound_path'],
                                      tuple(percussion['center_position']),
                                      percussion['radius'])
                           for percussion in self.settings.settings['percussion'].values()]
        self.controllers = [Controller(key,
                                       setting['name'],
                                       HSV(*setting['color_low']),
                                       HSV(*setting['color_high']),
                                       setting['velocity_max_volume'])
                            for key, setting in self.settings.settings['controllers'].items()]

    def play(self):
        """Play drum set."""
        for controller in self.controllers:
            for percussion in self.percussion:
                if percussion.is_played(controller):
                    percussion.play(controller)

    def setup_drum_set(self, save: bool = True):
        """Set up drum set: calibrate controllers and save to settings file."""
        for controller in self.controllers:
            controller_settings = self.settings.settings['controllers'][controller.key]
            controller.calibrate(controller_settings)
            if save:
                self.settings.save_settings()
