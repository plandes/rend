"""macOS bindings for displaying.

"""
__author__ = 'Paul Landes'

from typing import Dict, Sequence, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto
import logging
import textwrap
import re
from pathlib import Path
import applescript as aps
from applescript._result import Result
from zensols.config import ConfigFactory
from . import (
    ShowFileError, LocatorType, Size, Extent, Location, Presentation, Browser
)

logger = logging.getLogger(__name__)


class ApplescriptError(ShowFileError):
    """Raised for macOS errors.

    """
    pass


class ErrorType(Enum):
    """Types of errors raised by :class:`.ApplescriptError`.

    """
    ignore = auto()
    warning = auto()
    error = auto()


@dataclass
class DarwinBrowser(Browser):
    config_factory: ConfigFactory = field()
    """The configuration factory used to create a default :class:`.Browser`
    instance for URL viewing.

    """
    script_paths: Dict[str, Path] = field()
    """The applescript file paths used for managing show apps (``Preview.app``
    and ``Safari.app``).

    """
    web_extensions: Set[str] = field()
    """Extensions that indicate to use Safari.app rather than Preview.app."""

    applescript_warns: Dict[str, str] = field()
    """A set of string warning messages to log instead raise as an
    :class:`.ApplicationError`.

    """
    switch_back_app: str = field(default=None)
    """The application to activate (focus) after the resize is complete."""

    def _get_error_type(self, res: Result) -> ErrorType:
        err: str = res.err
        for warn, error_type in self.applescript_warns.items():
            if err.find(warn) > -1:
                return ErrorType[error_type]
        return ErrorType.error

    def _exec(self, cmd: str, app: str = None) -> str:
        ret: aps.Result
        if app is None:
            ret = aps.run(cmd)
        else:
            ret = aps.tell.app(app, cmd)
        if ret.code != 0:
            err_type: ErrorType = self._get_error_type(ret)
            cmd_str: str = textwrap.shorten(cmd, 40)
            msg: str = f'Could not invoke <{cmd_str}>: {ret.err} ({ret.code})'
            if err_type == ErrorType.warning:
                logger.warning(msg)
            elif err_type == ErrorType.error:
                raise ApplescriptError(msg)
        return ret.out

    def get_show_script(self, name: str) -> str:
        """The applescript content used for managing app ``name``."""
        with open(self.script_paths[name]) as f:
            return f.read()

    def _invoke_open_script(self, name: str, arg: str, extent: Extent,
                            func: str = None, add_quotes: bool = True):
        """Invoke applescript.

        :param name: the key of the script in :obj:`script_paths`

        :param arg: the first argument to pass to the applescript (URL or file
                    name)

        :param exent: the bounds to set on the raised window

        """
        show_script: str = self.get_show_script(name)
        qstr: str = '"' if add_quotes else ''
        func = f'show{name.capitalize()}' if func is None else func
        fn = (f'{func}({qstr}{arg}{qstr}, {extent.x}, {extent.y}, ' +
              f'{extent.width}, {extent.height})')
        cmd = (show_script + '\n' + fn)
        if logger.isEnabledFor(logging.DEBUG):
            path: Path = self.script_paths[name]
            logger.debug(f'invoking "{fn}" from {path}')
        if 0:
            print(cmd)
            return
        self._exec(cmd)
        self._switch_back()

    def _switch_back(self):
        """Optionally active an application after running the show-script, which
        is usually the previous running application.

        """
        if self.switch_back_app is not None:
            self._exec(f'tell application "{self.switch_back_app}" to activate')

    def _get_screen_size(self) -> Size:
        bstr: str = self._exec('bounds of window of desktop', 'Finder')
        bounds: Sequence[int] = tuple(map(int, re.split(r'\s*,\s*', bstr)))
        width, height = bounds[2:]
        return Size(width, height)

    def _safari_compliant_url(self, url: str) -> str:
        if not url.endswith('/'):
            url = url + '/'
        return url

    def _show_file(self, path: Path, extent: Extent):
        self._invoke_open_script('preview', str(path.absolute()), extent)

    def _show_url(self, url: str, extent: Extent):
        url = self._safari_compliant_url(url)
        self._invoke_open_script('safari', url, extent)

    def _show_urls(self, urls: Tuple[str], extent: Extent):
        def map_url(url: str) -> str:
            url = self._safari_compliant_url(url)
            return f'"{url}"'

        url_str: str = ','.join(map(map_url, urls))
        url_str = "{" + url_str + "}"
        self._invoke_open_script(
            name='safari-multi',
            arg=url_str,
            func='showSafariMulti',
            extent=extent,
            add_quotes=False)

    def show(self, presentation: Presentation):
        def map_loc(loc: Location) -> Location:
            if loc.is_file_url:
                path: Path = loc.path
                if path.suffix[1:] in self.web_extensions:
                    loc.coerce_type(LocatorType.url)
            return loc

        extent: Extent = presentation.extent
        urls: Tuple[str] = None
        locs: Tuple[Location] = tuple(map(map_loc, presentation.locators))
        if len(locs) > 1:
            loc_set: Set[LocatorType] = set(map(lambda lc: lc.type, locs))
            if len(loc_set) != 1 or next(iter(loc_set)) != LocatorType.file:
                urls = tuple(map(lambda loc: loc.url, locs))
        if urls is not None:
            self._show_urls(urls, extent)
        else:
            loc: Location
            for loc in presentation.locators:
                if loc.type == LocatorType.file:
                    self._show_file(loc.path, extent)
                else:
                    if loc.is_file_url:
                        self._show_file(loc.path, extent)
                    else:
                        self._show_url(loc.url, extent)
