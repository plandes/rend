"""Mapped transmutator implementation.

"""
from typing import Sequence, Any
from collections.abc import Iterable
from dataclasses import dataclass, field
import re
import parse
from pathlib import Path
from zensols.config import ConfigFactory
from zensols.persist import persisted, ReadOnlyStash, Stash
from .domain import Location, LocationTransmuter


@dataclass
class RegexFactoryStash(ReadOnlyStash):
    """A stash that loads configuration objects as loaded items.

    """
    config_factory: ConfigFactory = field()
    """Creates config objects as loaded stash items.."""

    pattern: str = field()
    """The file name portion with ``name`` populating to the key of the data
    value.

    """
    exclude_keys: Sequence[str] = field(default=())
    """Keys to exclude from :meth:`keys`."""

    new_instance: bool = field(default=False)
    """Use :meth:`~zensols.config.importfac.ImportConfigFactory.new_instance` to
    create new instances (new instance every time) if ``True``.  Otherwise, get
    singleton instances.

    """
    def load(self, name: str) -> Any:
        item: Any = None
        if self.exists(name):
            key: str = self.pattern.format(name=name)
            if self.new_instance:
                item = self.config_factory.new_instance(key)
            else:
                item = self.config_factory(key)
        return item

    @persisted('_keys')
    def keys(self) -> Iterable[str]:
        def map_key(key: str) -> str | None:
            p = parse.parse(self.pattern, key)
            if p is not None:
                p = p.named
                if 'name' in p:
                    return p['name']

        keys: Iterable[str] = map(map_key, self.config_factory.config.sections)
        keys = set(filter(lambda s: s is not None, keys))
        keys = keys - set(self.exclude_keys)
        return keys

    def exists(self, name: str) -> bool:
        return name in self.keys()


@dataclass
class MappedLocationTransmuter(LocationTransmuter):
    """A composite-like transmuter that uses other transmuters mapped from file
    names when :obj:`.Location.has_path` is ``True``.

    """
    config_factory: ConfigFactory = field()
    """Creates transmuters from :obj:`object_transmuter_names`."""

    trans_stash: Stash = field()
    """A stash that creates instances of :class:`.LocationTransmuter`."""

    path_transmuters: dict[str, re.Pattern | str] = field()
    """A mapping of :obj:`trans_stash` keys, which are substrings of section
    names, to regular expressions that match a transmuter that can transmute the
    location.

    """
    object_transmuter_names: tuple[str, ...] = field()
    """A list of section names that have transmuters that are used to handle
    objects passed to the program's API.

    """
    def __post_init__(self):
        self.path_transmuters = dict(map(
            lambda t: (t[0], self._process_regex(t[1])),
            self.path_transmuters.items()))

    @property
    @persisted('_object_transmuters')
    def object_transmuters(self) -> tuple[LocationTransmuter]:
        return tuple(map(
            lambda cn: self.config_factory(cn), self.object_transmuter_names))

    def _process_regex(self, val: str | re.Pattern):
        if isinstance(val, str):
            enc: str = val.encode().decode('unicode-escape')
            val = re.compile(enc)
        return val

    def _get_key(self, path: Path) -> str:
        fname: str = str(path)
        name: str
        regex: re.Pattern
        for name, regex in self.path_transmuters.items():
            if regex.match(fname) is not None:
                return name

    def transmute(self, location: Location) -> tuple[Location, ...]:
        new_locs: list[Location] = []
        if location.has_path:
            st_key: str = self._get_key(location.path)
            if st_key is not None:
                lc: LocationTransmuter = self.trans_stash[st_key]
                new_locs.extend(lc.transmute(location))
        else:
            # when objects are passed in, we have to take the hit of importing
            # :mod:`df`
            lc: LocationTransmuter
            for lc in self.object_transmuters:
                new_locs.extend(lc.transmute(location))
        return tuple(new_locs)
