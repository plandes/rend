"""Invoke Preview.pp on macOS and set extents of based on screen profiles.

"""
__author__ = 'Paul Landes'

from typing import Optional
from dataclasses import dataclass, field
import logging
from zensols.cli import ApplicationError
from . import (
    RenderFileError, LocationType, Extent, Location,
    Presentation, BrowserManager
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
        print('current:')
        self.browser_manager.browser.screen_size.write(depth=1)

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

    def show(self, location: str, location_type: LocationType = None,
             delimiter: str = ','):
        """Open and display a file with the application's extents set for the
        display.

        :param location: the file or URL to display

        :param location_type: specify either a URL or file; determined by
                              default

        :param delimiter: the string used to split location strings or ``-`` for
                          none

        """
        extent: Optional[Extent] = self._get_extent()
        if delimiter == '-':
            delimiter = None
        pres: Presentation = Presentation.from_str(location, delimiter, extent)
        if location_type is not None:
            loc: Location
            for loc in pres.locations:
                loc.coerce_type(location_type)
        try:
            self.browser_manager.show(pres)
        except RenderFileError as e:
            raise ApplicationError(str(e)) from e

    def __call__(self, *args, **kwargs):
        """See :meth:`show`."""
        return self.show(*args, **kwargs)
