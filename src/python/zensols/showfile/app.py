"""Invoke Preview.pp on macOS and set extents of based on screen profiles.

"""
__author__ = 'Paul Landes'

from typing import Optional
from dataclasses import dataclass, field
import logging
from zensols.cli import ApplicationError
from . import (
    ShowFileError, LocatorType, Extent, Location, Presentation, BrowserManager
)

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

    def _get_extent(self) -> Optional[Extent]:
        extent: Extent
        if self.width is None and self.height is None:
            extent = None
        elif self.width is None or self.height is None:
            raise ApplicationError(
                'Both width and height are expected when either is given')
        else:
            extent = Extent(self.width, self.height, 0, 0)
        return extent

    def show(self, locator: str, locator_type: LocatorType = None,
             delimiter: str = ','):
        """Open and display a file with the application's extents set for the
        display.

        :param locator: the file or URL to display

        :param locator_type: specify either a URL or file; determined by default

        :param delimiter: the string used to split locator strings

        """
        extent: Optional[Extent] = self._get_extent()
        pres: Presentation = Presentation.from_str(locator, delimiter, extent)
        if locator_type is not None:
            loc: Location
            for loc in pres.locators:
                loc.type = locator_type
        try:
            self.browser_manager.show(pres)
        except ShowFileError as e:
            raise e
            raise ApplicationError(str(e)) from e
