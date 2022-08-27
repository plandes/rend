"""Domain classes and the a screen manager class.

"""
__author__ = 'Paul Landes'

from typing import Sequence, Dict, Union
from dataclasses import dataclass, field
from enum import Enum, auto
from abc import ABCMeta, abstractmethod
import logging
import platform
from urllib.parse import urlparse
from pathlib import Path
from zensols.config import Dictable, ConfigFactory
from zensols.persist import persisted
from zensols.cli import ApplicationError

logger = logging.getLogger(__name__)


class LocatorType(Enum):
    """Identifies a URL or a file name.

    """
    file = auto()
    url = auto()


@dataclass(eq=True, unsafe_hash=True)
class Size(Dictable):
    """A screen size configuration.  This is created either for the current
    display, or one that's configured.

    """
    width: int = field()
    height: int = field()

    def __str__(self):
        return f'{self.width} X {self.height}'


@dataclass(eq=True, unsafe_hash=True)
class Extent(Size):
    """The size (parent class) and the position of the screen.

    """
    x: int = field(default=0)
    y: int = field(default=0)


@dataclass(eq=True, unsafe_hash=True)
class Display(Size):
    """The screen display.

    """
    _DICTABLE_WRITE_EXCLUDES = {'name'}

    name: str = field()
    """The name of the display as the section name in the configuration."""

    target: Extent = field()
    """The extends of the display or what to use for the Preview app."""

    def __str__(self):
        return super().__str__() + f' ({self.name})'


@dataclass
class Browser(Dictable, metaclass=ABCMeta):
    @property
    @persisted('_screen_size')
    def screen_size(self) -> Size:
        """Get the screen size for the current display."""
        return self._get_screen_size()

    @abstractmethod
    def _get_screen_size(self) -> Size:
        """Get the screen size for the current display."""
        pass

    def _file_to_url(self, path: Path) -> str:
        return f'file://{path.absolute()}'

    @abstractmethod
    def show_file(self, file_name: Path, extent: Extent):
        """Open and resize a file.

        :param file_name: the PDF (or image) file to resize

        :param extent: the screen position of where to put the app

        """
        pass

    def show_url(self, url: str, extent: Extent):
        """Open and resize a URL.

        :param url: the URL to open

        :param extent: the screen position of where to put the app

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

    browser: Browser = field(default=None)
    """The platform implementation of the file browser."""

    display_names: Sequence[str] = field(default_factory=list)
    """The configured display names, used to fetch displays in the
    configuration.

    """
    def __post_init__(self):
        if self.browser is None:
            os_name = platform.system().lower()
            sec_name = f'{os_name}_browser'
            if sec_name not in self.config_factory.config.sections:
                sec_name = 'default_browser'
            self.browser: Browser = self.config_factory(sec_name)

    @staticmethod
    def guess_locator_type(s: str) -> LocatorType:
        """Return whether ``s`` looks like a file or a URL."""
        st: LocatorType = None
        try:
            result = urlparse(s)
            if all([result.scheme, result.netloc]):
                st = LocatorType.url
        except Exception:
            pass
        st = LocatorType.file if st is None else st
        return st

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

    @property
    @persisted('_displays_by_size')
    def displays_by_size(self) -> Dict[Size, Display]:
        """A dictionary of displays keyed by size."""
        return {Size(d.width, d.height): d for d in self.displays.values()}

    def show(self, locator: Union[str, Path], extent: Extent = None):
        """Display ``locator`` content on the screen and optionally resize the
        window to ``extent``.

        :param locator: the PDF (or image) file or URL to display

        :param extent: the position and size of the window after browsing

        """
        if extent is None:
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
        if isinstance(locator, Path):
            path: Path = locator
            if not path.is_file():
                raise ApplicationError(f'No file found: {path}')
            self.browser.show_file(locator, extent)
        else:
            self.browser.show_url(locator, extent)
