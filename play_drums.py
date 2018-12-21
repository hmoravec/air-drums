"""Run the app for air drum playing."""

import argparse
import logging

from drums.interface import Interface
from drums.settings import Settings


LOGGING_LEVEL = logging.DEBUG


def parse_arguments():
    """Return parsed command line arguments as dictionary."""
    parser = argparse.ArgumentParser(description='Air drums argument parser.')
    parser.add_argument('-s', '--settings_file_path',
                        default='./settings/drum_set_basic.yaml',
                        help='Relative path to the setting file.')

    parsed_arguments = parser.parse_args()
    arguments = vars(parsed_arguments)
    return arguments


def start_interface():
    """Start air drums interface with parsed settings."""
    arguments = parse_arguments()
    settings = Settings(arguments['settings_file_path'])

    interface = Interface(settings)
    interface.start_interface()


if __name__ == '__main__':
    logging.basicConfig(level=LOGGING_LEVEL)
    start_interface()
