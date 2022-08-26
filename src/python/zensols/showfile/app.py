"""Invoke Preview.pp on macOS and set extents of based on screen profiles.

"""
__author__ = 'Paul Landes'

from dataclasses import dataclass, field
import logging
from pathlib import Path
from zensols.cli import ApplicationError
from . import ScreenManager, Extent

logger = logging.getLogger(__name__)


@dataclass
class Application(object):
    """Probe screen, open and set the viewing application extends.

    """
    smng: ScreenManager = field()
    """Detects and controls the screen."""

    width: int = field(default=None)
    """The width to set, or use the configuraiton if not set."""

    height: int = field(default=None)
    """The height to set, or use the configuraiton if not set."""

    def config(self):
        """Print the display configurations."""
        for n, dsp in sorted(self.smng.displays.items(), key=lambda x: x[0]):
            print(f'{n}:')
            dsp.write(1)

    def show(self, file_name: Path):
        """Open and display a file with the application's extents set for the
        display.

        :param file_name: the file to show in the preview application

        """
        if self.width is None and self.height is None:
            self.smng.detect_and_resize(file_name)
        elif self.width is None or self.height is None:
            raise ApplicationError(
                'Both width and height are expected when either is given')
        else:
            self.smng.resize(file_name, Extent(self.width, self.height, 0, 0))
