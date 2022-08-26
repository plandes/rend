"""Domain classes and the a screen manager class.

"""
__author__ = 'Paul Landes'

from typing import Sequence, Dict
from dataclasses import dataclass, field
from abc import ABCMeta, abstractmethod
import logging
import platform
from pathlib import Path
from zensols.config import Dictable, ConfigFactory
from zensols.persist import persisted
from zensols.cli import ApplicationError

logger = logging.getLogger(__name__)


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

    @abstractmethod
    def show(self, file_name: Path, extent: Extent):
        """Open and resize a file.

        :param file_name: the PDF (or image) file to resize

        :param extent: the screen position of where to put the app

        """
        pass


@dataclass
class ScreenManager(object):
    """Resizing Preview.app based on provided screen configuration.
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

    def show(self, file_name: Path, extent: Extent = None):
        """Like :meth:`resize` but use the screen extents of the current screen.

        :param file_name: the PDF (or image) file to resize

        """
        if not file_name.is_file():
            raise ApplicationError(f'No file found: {file_name}')
        if extent is None:
            screen: Size = self.browser.screen_size
            display: Display = self.displays_by_size.get(screen)
            logger.debug(f'detected: {screen} -> {display}')
            if display is None:
                raise ApplicationError(f'No display entry for bounds: {screen}')
            extent = display.target
        self.browser.show(file_name, extent)
