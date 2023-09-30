"""Contains application domain classes.

"""
from __future__ import annotations
__author__ = 'Paul Landes'
from typing import Union, Tuple, Any, Set, List
from dataclasses import dataclass, field
from abc import abstractmethod, ABCMeta
from enum import Enum, auto
import urllib.parse as up
from pathlib import Path
from zensols.util import APIError
from zensols.config import Dictable
from zensols.persist import persisted, PersistedWork, PersistableContainer


class RenderFileError(APIError):
    """Raised for any :module:`zensols.rend` API error.

    """
    pass


class FileNotFoundError(RenderFileError):
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
            raise RenderFileError(f'Unknown type: {type(instance)}')
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
class Location(PersistableContainer, Dictable):
    """Has the ability to find the data and how to view it.

    """
    source: Union[str, Path] = field()
    """Where to find the data to display."""

    type: LocatorType = field(default=None)
    """The type of resource (PDF or URL) to display."""

    def __post_init__(self):
        super().__init__()
        self._url = PersistedWork('_url', self)
        self._path = PersistedWork('_path', self)
        self._file_url_path = None
        if self.type is None:
            if isinstance(self.source, Path):
                self.type = LocatorType.file
                self.validate()
            else:
                self.type, path = LocatorType.from_str(self.source)
                if self.type == LocatorType.url and path is not None:
                    self._file_url_path = Path(path)
        if self.type == LocatorType.file and isinstance(self.source, str):
            self.source = Path(self.source)

    def validate(self):
        """Validate the location such as confirming file locations exist.

        :raises FileNotFoundError: if the location points to a non-existant file

        """
        if self.type == LocatorType.file or self.is_file_url:
            path: Path = self.path
            if not path.is_file():
                raise FileNotFoundError(path)

    @property
    def is_file_url(self) -> bool:
        """Whether the locator is a URL that points to a file."""
        return self._file_url_path is not None

    @property
    @persisted('_url')
    def url(self) -> str:
        """The URL of the locator."""
        url: str = self.source
        if isinstance(self.source, Path):
            url = f'file://{self.source.absolute()}'
        return url

    @property
    def has_path(self) -> bool:
        """Whether this locator has a path and that access to :obj:`path` will
        not raise an error.

        """
        return isinstance(self.source, Path) or self.is_file_url

    @property
    @persisted('_path')
    def path(self) -> Path:
        """The path of the locator.

        :raises RenderFileError: if the locator does not point to a path or not a
                               URL path

        """
        if isinstance(self.source, Path):
            return self.source
        else:
            if self._file_url_path is None:
                raise RenderFileError(f'Not a path or URL path: {self.source}')
            return self._file_url_path

    def coerce_type(self, locator_type: LocatorType):
        """Change to the locator from a file to a URL or vica versa if possible.

        """
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
        self._url.clear()
        self._url.clear()


@dataclass
class LocationTransmuter(object, metaclass=ABCMeta):
    """Transmutes concrete locations to their ephemeral counterparts, which
    usually need additional resources.

    """
    @abstractmethod
    def transmute(self, location: Location) -> Tuple[Location]:
        """Transmute the location if possible.

        :return: a transmuted location if possible, otherwise ``None``

        """
        pass


@dataclass
class Presentation(PersistableContainer, Dictable):
    """Contains all the data to view all at once and where on the screen to
    display it.

    """
    locators: Tuple[Location] = field()
    """The locations of the content to display"""

    extent: Extent = field(default=None)
    """Where to display the content."""

    def __post_init__(self):
        super().__init__()
        self._locator_type_set = PersistedWork('_locator_type_set', self)

    @staticmethod
    def from_str(locator_defs: str, delimiter: str = ',',
                 extent: Extent = None) -> Presentation:
        """Create a presentation from a comma-delimited list of locators."""
        locs: Tuple[Location] = tuple(
            map(Location, locator_defs.split(delimiter)))
        return Presentation(locs, extent)

    @property
    @persisted('_locator_type_set')
    def locator_type_set(self) -> Set[LocatorType]:
        """A set of :obj:`locators`."""
        return frozenset(map(lambda loc: loc.type, self.locators))

    def apply_transmuter(self, transmuter: LocationTransmuter):
        changed: bool = False
        updates: List[Location] = []
        loc: Location
        for loc in self.locators:
            locs: Tuple[Location] = transmuter.transmute(loc)
            if len(locs) > 0:
                updates.extend(locs)
                changed = True
            else:
                updates.append(loc)
        if changed:
            self.locators = tuple(updates)
            self._locator_type_set.clear()

    def validate(self):
        """Validate all locators.

        :see: :meth:`.Location.validate`

        """
        for loc in self.locators:
            loc.validate()

    def deallocate(self):
        loc: Location
        for loc in self.locators:
            loc.deallocate()
        super().deallocate()
