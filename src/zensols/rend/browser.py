"""Domain classes and the a screen manager class.

"""
from __future__ import annotations
__author__ = 'Paul Landes'
from typing import Sequence, TypeAlias
from dataclasses import dataclass, field
from abc import ABCMeta, abstractmethod
import logging
import re
import platform
from itertools import chain
from pathlib import Path
import filetype
from filetype.types.base import Type as FileType
from pandas import DataFrame
from zensols.config import Dictable, ConfigFactory
from zensols.persist import persisted
from . import (
    RenderFileError, Size, Extent, LocationType, Location, LocationTransmuter,
    Display, Presentation,
)

logger = logging.getLogger(__name__)

Showable: TypeAlias = str | Path | Presentation | Location | \
    DataFrame | Sequence


@dataclass
class FileTypeFilter(Dictable):
    """Filters locations either by file name or the contents of the file.

    """
    name_regex: re.Pattern | str = field()
    """A regular expression that matches locations to keep."""

    mime_regex: re.Pattern | str = field()
    """A regular expression that matches mime types (determined by file content)
    to keep.

    """
    def __post_init__(self):
        for attr in 'name_regex mime_regex'.split():
            val = getattr(self, attr)
            if isinstance(val, str):
                enc: str = val.encode().decode('unicode-escape')
                setattr(self, attr, re.compile(enc))

    def _name_matches(self, path: Path) -> bool:
        if self.name_regex is not None:
            return self.name_regex.match(str(path)) is not None
        return False

    def _type_matches(self, path: Path) -> bool:
        if self.mime_regex is not None:
            ftype: FileType = filetype.guess(path)
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f'file type: {ftype}')
            if ftype is not None:
                mime: str = ftype.mime
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f'mime type: {mime}')
                return self.mime_regex.match(mime) is not None
        return False

    def __call__(self, presentation: Presentation):
        keeps: list[Location] = []
        for loc in presentation.locations:
            if loc.has_path:
                path: Path = loc.path
                if self._name_matches(path) or self._type_matches(path):
                    keeps.append(loc)
                else:
                    logger.warning(f'unknown file: {path}--skipping')
            else:
                keeps.append(loc)
        if len(presentation.locations) > len(keeps):
            presentation.locations = tuple(keeps)
        return presentation


@dataclass
class Browser(Dictable, metaclass=ABCMeta):
    """An abstract base class for browsers the can visually display files.

    """
    file_type_filter: FileTypeFilter = field()
    """Filters locations either by file name or the contents of the file."""

    @property
    @persisted('_screen_size')
    def screen_size(self) -> Size:
        """Get the screen size for the current display."""
        return self._get_screen_size()

    @abstractmethod
    def _get_screen_size(self) -> Size:
        """Get the screen size for the current display."""
        pass

    def show(self, presentation: Presentation):
        """Display the content.

        :param presentation: the file/PDF (or image) to display

        """
        presentation = self.file_type_filter(presentation)
        self._show(presentation)

    @abstractmethod
    def _show(self, presentation: Presentation):
        """See :meth:`show`."""
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
    transmuters: tuple[LocationTransmuter, ...] = field(default_factory=list)
    """A list of transmuters that map concrete locations to the ephemeral."""

    def __post_init__(self):
        if self.browser is None:
            os_name: str = platform.system().lower()
            sec_name: str = f'rend_{os_name}_browser'
            if sec_name not in self.config_factory.config.sections:
                sec_name = self.default_browser_name
            try:
                self.browser: Browser = self.config_factory(sec_name)
            except Exception as e:
                logger.warning(f'Could not create browser: {sec_name}: {e}')
            if self.browser is None:
                sec_name = self.default_browser_name
                self.browser: Browser = self.config_factory(sec_name)

    @property
    @persisted('_displays')
    def displays(self) -> dict[str, Size]:
        """The configured displays."""
        def map_display(name: str) -> Display:
            targ = Extent(**fac(f'{name}_target').asdict())
            return Display(**fac(name).asdict() |
                           {'name': name, 'target': targ})

        fac = self.config_factory
        return {d.name: d for d in map(map_display, self.display_names)}

    def _get_extent(self) -> Extent:
        screen: Size = self.browser.screen_size
        displays: dict[Size, Display] = self.displays_by_size
        display: Display = displays.get(screen)
        if logger.isEnabledFor(logging.TRACE):
            from pprint import pprint
            from io import StringIO
            sio = StringIO()
            sio.write('displays:\n')
            pprint(displays, sio)
            logger.debug(f'displays: {sio.getvalue()}')
        if logger.isEnabledFor(logging.DEBUG):
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
    def displays_by_size(self) -> dict[Size, Display]:
        """A dictionary of displays keyed by size."""
        return {Size(d.width, d.height): d for d in self.displays.values()}

    def dataframe_to_location(self, df: DataFrame, name: str = None) -> \
            Location:
        """Create a location from a Pandas dataframe.

        :param df: the datafram to display

        :param name: the name of the location and used as the title of the frame

        """
        from zensols.rend.df import CachedDataFrameSource, DataFrameLocation
        df_source = CachedDataFrameSource(df, name)
        return DataFrameLocation(df_source)

    def to_presentation(self, data: Showable, extent: Extent = None) \
            -> Presentation:
        """Create a presentation instance from a string, path, or other
        presentation.

        :param data: the data (image file, URL, Pandas dataframe) to display

        :param extent: the position and size of the window after browsing

        """
        from zensols.datdesc import DataFrameDescriber, DataDescriber
        pres: Presentation
        if isinstance(data, (str, Path)):
            loc_type: LocationType = LocationType.from_type(data)
            loc: Location = Location(source=data, type=loc_type)
            pres = Presentation(locations=(loc,))
        elif isinstance(data, Presentation):
            pres = data
        elif isinstance(data, Location):
            pres = Presentation(locations=(data,))
        elif isinstance(data, DataFrame):
            loc: Location = self.dataframe_to_location(data)
            pres = Presentation(locations=(loc,))
        elif isinstance(data, Sequence):
            pres = Presentation(
                locations=tuple(chain.from_iterable(map(
                    lambda loc: self.to_presentation(loc).locations, data))))
        elif isinstance(data, DataFrameDescriber):
            pres = self.to_presentation(DataDescriber(describers=(data,)))
        elif isinstance(data, DataDescriber):
            from .df import DataDescriberLocation
            loc: Location = DataDescriberLocation(data)
            pres = Presentation(locations=(loc,))
        else:
            raise RenderFileError(f'Unsupported location type: {type(data)}')
        pres.extent = self._get_extent() if extent is None else extent
        lt: LocationTransmuter
        for lt in self.transmuters:
            pres.apply_transmuter(lt)
        return pres

    def show(self, data: Showable, extent: Extent = None):
        """Display ``data`` content on the screen and optionally resize the
        window to ``extent``.

        :param data: the data (image file, URL, Pandas dataframe) to display

        :param extent: the position and size of the window after browsing

        """
        pres: Presentation = self.to_presentation(data, extent)
        try:
            pres.validate()
            self.browser.show(pres)
        finally:
            pres.deallocate()

    def __call__(self, *args, **kwargs):
        """See :meth:`show`."""
        return self.show(*args, **kwargs)
