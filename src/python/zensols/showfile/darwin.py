"""macOS bindings for displaying.

"""
__author__ = 'Paul Landes'

from typing import Dict, Sequence
from dataclasses import dataclass, field
from enum import Enum, auto
import logging
import textwrap
import re
from pathlib import Path
import applescript as aps
from applescript._result import Result
from zensols.util import APIError
from zensols.config import ConfigFactory
from . import Size, Extent, Browser

logger = logging.getLogger(__name__)


class ApplescriptError(APIError):
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
    applescript_warns: Dict[str, str] = field(default_factory=set())
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

    def _invoke_open_script(self, name: str, arg: str, extent: Extent):
        """Invoke applescript.

        :param name: the key of the script in :obj:`script_paths`

        :param arg: the first argument to pass to the applescript (URL or file
                    name)

        :param exent: the bounds to set on the raised window

        """
        show_script: str = self.get_show_script(name)
        func: str = f'show{name.capitalize()}'
        fn = (f'{func}("{arg}", {extent.x}, {extent.y}, ' +
              f'{extent.width}, {extent.height})')
        cmd = (show_script + '\n' + fn)
        if logger.isEnabledFor(logging.DEBUG):
            path: Path = self.script_paths[name]
            logger.debug(f'invoking "{fn}" from {path}')
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

    def show_file(self, path: Path, extent: Extent = None):
        if path.suffix == '.html':
            url: str = self._file_to_url(path)
            self.show_url(url, extent)
        else:
            self._invoke_open_script('preview', str(path.absolute()), extent)

    def show_url(self, url: str, extent: Extent = None):
        # cannonize the URL so the applescript to find it in the list of
        # browsers
        if url[-1] != '/':
            url = url + '/'
        self._invoke_open_script('safari', url, extent)
