"""Domain classes and the a screen manager class.

"""
from __future__ import annotations
__author__ = 'Paul Landes'
from typing import Sequence, Dict, Union, Tuple
from dataclasses import dataclass, field
from abc import ABCMeta, abstractmethod
import logging
import platform
from pathlib import Path
from zensols.config import Dictable, ConfigFactory
from zensols.persist import persisted
from . import (
    RenderFileError, Size, Extent, LocatorType, Location, LocationTransmuter,
    Display, Presentation,
)

logger = logging.getLogger(__name__)


@dataclass
class Browser(Dictable, metaclass=ABCMeta):
    """An abstract base class for browsers the can visually display files.

    """
    @property
    @persisted('_screen_size')
    def screen_size(self) -> Size:
        """Get the screen size for the current display."""
        return self._get_screen_size()

    @abstractmethod
    def _get_screen_size(self) -> Size:
        """Get the screen size for the current display."""
        pass

    @abstractmethod
    def show(self, presentation: Presentation):
        """Display the content.

        :param presentation: the file/PDF (or image) to display

        """
        pass


@dataclass
class BrowserManager(object):
    """Manages configured browsers and invoking them to display files and URLs.
    It also contains configuration for application extents based configured
    displays.

    """
    config_factory: ConfigFactory = field()
    """Set by the framework and used to get other configurations."""

    default_browser_name: str = field()
    """The app config section name of the default browser definition."""

    browser: Browser = field(default=None)
    """The platform implementation of the file browser."""

    display_names: Sequence[str] = field(default_factory=list)
    """The configured display names, used to fetch displays in the
    configuration.

    """
    transmuters: Tuple[LocationTransmuter] = field(default_factory=list)
    """A list of transmuters that map concrete locations to the ephemeral."""

    def __post_init__(self):
        if self.browser is None:
            os_name = platform.system().lower()
            sec_name = f'rend_{os_name}_browser'
            if sec_name not in self.config_factory.config.sections:
                sec_name = self.default_browser_name
            self.browser: Browser = self.config_factory(sec_name)

    @property
    @persisted('_displays')
    def displays(self) -> Dict[str, Size]:
        """The configured displays."""
        def map_display(name: str) -> Display:
            targ = Extent(**fac(f'{name}_target').asdict())
            return Display(**fac(name).asdict() |
                           {'name': name, 'target': targ})

        fac = self.config_factory
        return {d.name: d for d in map(map_display, self.display_names)}

    def _get_extent(self) -> Extent:
        screen: Size = self.browser.screen_size
        display: Display = self.displays_by_size.get(screen)
        logger.debug(f'detected: {screen} -> {display}')
        if display is None:
            logger.warning(
                f'no display entry for bounds: {screen}--using default')
            extent = Extent(
                x=0, y=0,
                width=screen.width // 2,
                height=screen.height)
        else:
            extent = display.target
        return extent

    @property
    @persisted('_displays_by_size')
    def displays_by_size(self) -> Dict[Size, Display]:
        """A dictionary of displays keyed by size."""
        return {Size(d.width, d.height): d for d in self.displays.values()}

    def locator_to_presentation(self, locator: Union[str, Path, Presentation],
                                extent: Extent = None, transmute: bool = True) \
            -> Presentation:
        """Create a presentation instance from a string, path, or other
        presentation.

        :param locator: the PDF (or image) file or URL to display

        :param extent: the position and size of the window after browsing

        :param transmute: whether to apply :class:`.LocationTransmuter`s

        """
        pres: Presentation
        if isinstance(locator, (str, Path)):
            loc_type: LocatorType = LocatorType.from_type(locator)
            loc: Location = Location(source=locator, type=loc_type)
            pres = Presentation(locators=(loc,))
        elif isinstance(locator, Presentation):
            pres = locator
        else:
            raise RenderFileError(f'Unsupported locator type: {type(locator)}')
        pres.extent = self._get_extent() if extent is None else extent
        if transmute:
            lt: LocationTransmuter
            for lt in self.transmuters:
                pres.apply_transmuter(lt)
        return pres

    def show(self, locator: Union[str, Path, Presentation],
             extent: Extent = None):
        """Display ``locator`` content on the screen and optionally resize the
        window to ``extent``.

        :param locator: the PDF (or image) file or URL to display

        :param extent: the position and size of the window after browsing

        """
        pres: Presentation = self.locator_to_presentation(locator, extent)
        try:
            pres.validate()
            self.browser.show(pres)
        finally:
            pres.deallocate()

    def __call__(self, *args, **kwargs):
        """See :meth:`show`."""
        return self.show(*args, **kwargs)
