"""macOS bindings for file displaying.

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
from zensols.persist import persisted
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
    show_preview_script_path: Path = field()
    """The applescript file path used for managing Preview.app."""

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

    @property
    @persisted('_show_preview_script')
    def show_preview_script(self) -> str:
        """The applescript content used for managing Preview.app."""
        with open(self.show_preview_script_path) as f:
            return f.read()

    def _switch_back(self):
        if self.switch_back_app is not None:
            self._exec(f'tell application "{self.switch_back_app}" to activate')

    def _get_screen_size(self) -> Size:
        bstr: str = self._exec('bounds of window of desktop', 'Finder')
        bounds: Sequence[int] = tuple(map(int, re.split(r'\s*,\s*', bstr)))
        width, height = bounds[2:]
        return Size(width, height)

    def show_file(self, path: Path, extent: Extent = None):
        file_name_str: str = str(path.absolute())
        fn = (f'showPreview("{file_name_str}", {extent.x}, {extent.y}, ' +
              f'{extent.width}, {extent.height})')
        cmd = (self.show_preview_script + '\n' + fn)
        self._exec(cmd)
        self._switch_back()

    def show_url(self, url: str, extent: Extent):
        pass
