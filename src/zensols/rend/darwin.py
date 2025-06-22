"""macOS bindings for displaying.

"""
__author__ = 'Paul Landes'

from typing import Dict, Sequence, Set, Tuple, Union, TYPE_CHECKING
from dataclasses import dataclass, field
from enum import Enum, auto
import logging
import textwrap
import re
from pathlib import Path
from zensols.config import ConfigFactory
from . import (
    RenderFileError, LocationType, Size, Extent, Location, Presentation, Browser
)

logger = logging.getLogger(__name__)


class ApplescriptError(RenderFileError):
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
    update_page: Union[bool, int] = field(default=False)
    """How to update the page in Preview.app after the window displays.  If
    ``True``, then record page before refresh, then go to the page after
    rendered.  This is helpful when the PDF has changed and preview goes back to
    the first page.  If this is a number, then go to that page number in
    Preview.app.

    """
    switch_back_app: str = field(default=None)
    """The application to activate (focus) after the resize is complete."""

    mangle_url: bool = field(default=False)
    """Whether to add ending ``/`` neede by Safari on macOS."""

    def __post_init__(self):
        # try to install the applescript module if possible
        self._assert_applescript()
        # raise error now so BrowserManager can recover
        import applescript

    def _assert_applescript(self):
        from zensols.util import (
            PackageResource, PackageManager, PackageRequirement
        )
        package: str = 'applescript'
        pr = PackageResource(package)
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f'{package} installed: {pr.installed}, ' +
                         f'available: {pr.available}')
        if not pr.installed:
            if logger.isEnabledFor(logging.INFO):
                logger.info(f'attempting to install {package}')
            pm = PackageManager()
            pm.install(PackageRequirement.from_spec(package))

    def _get_error_type(self, res: 'applescript.Result') -> ErrorType:
        err: str = res.err
        for warn, error_type in self.applescript_warns.items():
            if err.find(warn) > -1:
                return ErrorType[error_type]
        return ErrorType.error

    def _exec(self, cmd: str, app: str = None) -> str:
        import applescript
        ret: applescript.Result
        if app is None:
            ret = applescript.run(cmd)
        else:
            ret = applescript.tell.app(app, cmd)
        if ret.code != 0:
            err_type: ErrorType = self._get_error_type(ret)
            cmd_str: str = textwrap.shorten(cmd, 40)
            msg: str = f'Could not invoke <{cmd_str}>: {ret.err} ({ret.code})'
            if err_type == ErrorType.warning:
                logger.warning(msg)
            elif err_type == ErrorType.error:
                raise ApplescriptError(msg)
        elif logger.isEnabledFor(logging.DEBUG):
            logger.debug(f'script output: <{ret.err}>')
        return ret.out

    def get_show_script(self, name: str) -> str:
        """The applescript content used for managing app ``name``."""
        with open(self.script_paths[name]) as f:
            return f.read()

    def _invoke_open_script(self, name: str, arg: str, extent: Extent,
                            func: str = None, add_quotes: bool = True,
                            is_file: bool = False):
        """Invoke applescript.

        :param name: the key of the script in :obj:`script_paths`

        :param arg: the first argument to pass to the applescript (URL or file
                    name)

        :param exent: the bounds to set on the raised window

        """
        show_script: str = self.get_show_script(name)
        qstr: str = '"' if add_quotes else ''
        update_page: str
        page_num: str = 'null'
        if isinstance(self.update_page, bool):
            update_page = str(self.update_page).lower()
            page_num = 'null'
        else:
            update_page = 'true'
            page_num = str(self.update_page)
        func: str = f'show{name.capitalize()}' if func is None else func
        file_form: str
        if is_file:
            # add single quote for files with spaces in the name
            file_form = f"{qstr}'{arg}'{qstr}"
        else:
            file_form = f'{qstr}{arg}{qstr}'
        fn = (f'{func}({file_form}, {extent.x}, {extent.y}, ' +
              f'{extent.width}, {extent.height}, {update_page}, {page_num})')
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

    def _safari_compliant_url(self, url: str) -> str:
        if self.mangle_url and not url.endswith('/'):
            url = url + '/'
        return url

    def _show_file(self, path: Path, extent: Extent):
        self._invoke_open_script('preview', str(path.absolute()),
                                 extent, is_file=True)

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
            if loc.is_file_url or loc.type == LocationType.file:
                path: Path = loc.path
                if path.suffix[1:] in self.web_extensions:
                    loc.coerce_type(LocationType.url)
            return loc

        extent: Extent = presentation.extent
        urls: Tuple[str] = None
        locs: Tuple[Location] = tuple(map(map_loc, presentation.locations))
        if len(locs) > 1:
            loc_set: Set[LocationType] = set(map(lambda lc: lc.type, locs))
            if len(loc_set) != 1 or next(iter(loc_set)) != LocationType.file:
                urls = tuple(map(lambda loc: loc.url, locs))
        if urls is not None:
            self._show_urls(urls, extent)
        else:
            loc: Location
            for loc in presentation.locations:
                if loc.type == LocationType.file:
                    self._show_file(loc.path, extent)
                else:
                    if loc.is_file_url:
                        self._show_file(loc.path, extent)
                    else:
                        self._show_url(loc.url, extent)
