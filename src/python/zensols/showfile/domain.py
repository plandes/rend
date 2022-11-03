from __future__ import annotations
"""Contains application domain classes.

"""
__author__ = 'Paul Landes'

from typing import Union, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum, auto
import urllib.parse as up
from pathlib import Path
from zensols.util import APIError
from zensols.config import Dictable
from zensols.persist import persisted


class ShowFileError(APIError):
    """Raised for any :module:`zensols.showfile` API error.
    """
    pass


class FileNotFoundError(ShowFileError):
    """Raised when a locator is a file, but the file isn't found."""
    def __init__(self, path: Path):
        super().__init__(f'File not found: {path}')
        self.path = path


class LocatorType(Enum):
    """Identifies a URL or a file name.

    """
    file = auto()
    url = auto()

    @staticmethod
    def from_type(instance: Any) -> LocatorType:
        type: LocatorType
        if isinstance(instance, Path):
            type = LocatorType.file
        elif isinstance(instance, str):
            type = LocatorType.url
        else:
            raise ShowFileError(f'Unknown type: {type(instance)}')
        return type

    @staticmethod
    def from_str(s: str) -> Tuple[LocatorType, str]:
        """Return whether ``s`` looks like a file or a URL."""
        st: LocatorType = None
        path: str = None
        try:
            result: up.ParseResult = up.urlparse(s)
            if result.scheme == 'file' and len(result.path) > 0:
                st = LocatorType.url
                path = result.path
            elif all([result.scheme, result.netloc]):
                st = LocatorType.url
        except Exception:
            pass
        st = LocatorType.file if st is None else st
        return st, path


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
class Location(Dictable):
    """Has where to find the data and what it is to view.

    """
    source: Union[str, Path] = field()
    """Where to find the data to display."""

    type: LocatorType = field(default=None)
    """The type of resource (PDF or URL) to display."""

    def __post_init__(self):
        self._file_url_path = None
        if self.type is None:
            if isinstance(self.source, Path):
                self.type = LocatorType.file
                self.validate()
            else:
                self.type, path = LocatorType.from_str(self.source)
                if self.type == LocatorType.url and path is not None:
                    path = Path(path)
                    self._file_url_path = path
        if self.type == LocatorType.file and isinstance(self.source, str):
            self.source = Path(self.source)

    def validate(self):
        if self.type == LocatorType.file or self.is_file_url:
            path: Path = self.path
            if not path.is_file():
                raise FileNotFoundError(path)

    @property
    def is_file_url(self) -> bool:
        return self._file_url_path is not None

    @property
    @persisted('_url')
    def url(self) -> str:
        url: str = self.source
        if isinstance(self.source, Path):
            url = f'file://{self.source.absolute()}'
        return url

    @property
    @persisted('_path')
    def path(self) -> Path:
        if isinstance(self.source, Path):
            return self.source
        else:
            if self._file_url_path is None:
                raise ShowFileError(f'Not a path or URL path: {self.source}')
            return self._file_url_path

    def coerce_type(self, locator_type: LocatorType):
        if locator_type != self.type:
            if locator_type == LocatorType.file:
                type, path = LocatorType.from_str(self.source)
                if path is not None:
                    self.type = LocatorType.file
                    self.source = Path(path)
            else:
                self.source = self.url
                self.type = LocatorType.url
                self._file_url_path = None
        elif locator_type == LocatorType.url and self.is_file_url:
            self._file_url_path = None


@dataclass
class Presentation(Dictable):
    """Contains all the data to view all at once and where on the screen to
    display it.

    """
    locators: Tuple[Location] = field()
    """The locations of the content to display"""

    extent: Extent = field(default=None)
    """Where to display the content."""

    @staticmethod
    def from_str(locator_defs: str, delimiter: str = ',',
                 extent: Extent = None) -> Presentation:
        locs: Tuple[Location] = tuple(
            map(Location, locator_defs.split(delimiter)))
        return Presentation(locs, extent)

    @property
    @persisted('_loctypes')
    def locator_type_set(self) -> Set[LocatorType]:
        return frozenset(map(lambda loc: loc.type, self.locators))
