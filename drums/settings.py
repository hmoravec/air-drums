"""Drums configuration."""

from typing import Dict, Any

import yaml
# TODO: Change to ruamel so the format of config is not changed when resaved.
# from ruamel import yaml


class Settings:
    """Settings for air drums."""

    def __init__(self, settings_file_path: str):
        #: Relative path to the settings file
        self.settings_file_path = settings_file_path
        #: Air drums settings
        self.settings = self.get_settings()

    def get_settings(self) -> Dict[str, Any]:
        """Return settings."""
        with open(self.settings_file_path, 'r') as settings_file:
            # settings = yaml.load(settings_file, Loader=yaml.RoundTripLoader)
            settings = yaml.load(settings_file)
        return settings

    def save_settings(self):
        """Save settings to the settings file."""
        with open(self.settings_file_path, 'w') as settings_file:
            # yaml.dump(self.settings, settings_file, Dumper=yaml.RoundTripDumper)
            yaml.dump(self.settings, settings_file)
