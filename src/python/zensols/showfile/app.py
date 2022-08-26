"""Invoke Preview.pp on macOS and set extents of based on screen profiles.

"""
__author__ = 'Paul Landes'

from dataclasses import dataclass, field
import logging
from pathlib import Path
from zensols.cli import ApplicationError
from . import Extent, LocatorType, BrowserManager

logger = logging.getLogger(__name__)


@dataclass
class Application(object):
    """Probe screen, open and set the viewing application extends.

    """
    browser_manager: BrowserManager = field()
    """Detects and controls the screen."""

    width: int = field(default=None)
    """The width to set, or use the configuraiton if not set."""

    height: int = field(default=None)
    """The height to set, or use the configuraiton if not set."""

    def config(self):
        """Print the display configurations."""
        dsps = sorted(self.browser_manager.displays.items(), key=lambda x: x[0])
        for n, dsp in dsps:
            print(f'{n}:')
            dsp.write(1)

    def show(self, locator: str, locator_type: LocatorType = None):
        """Open and display a file with the application's extents set for the
        display.

        :param locator: the file or URL to display

        :param locator_type: specify either a URL or file; determined by default

        """
        if locator_type is None:
            locator_type = self.browser_manager.guess_locator_type(locator)
        extent: Extent
        if self.width is None and self.height is None:
            extent = None
        elif self.width is None or self.height is None:
            raise ApplicationError(
                'Both width and height are expected when either is given')
        else:
            extent = Extent(self.width, self.height, 0, 0)
        if locator_type == LocatorType.file:
            locator = Path(locator)
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f'showing {locator} ({type(locator)})')
        self.browser_manager.show(locator, extent)
