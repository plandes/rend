"""macOS bindings for file displaying.

"""
__author__ = 'Paul Landes'

from typing import Dict
from dataclasses import dataclass, field
from enum import Enum, auto
import logging
import textwrap
import applescript as aps
from applescript._result import Result
from zensols.util import APIError
from . import ScreenManager

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
class MacOSScreenManager(ScreenManager):
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
        return ErrorType.throw

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
