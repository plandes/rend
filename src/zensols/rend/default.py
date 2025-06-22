"""Web browser default implementation.

"""
__author__ = 'Paul Landes'

from typing import List, Tuple
from dataclasses import dataclass
import logging
import webbrowser
import screeninfo as si
from screeninfo.common import Monitor
from . import Size, Location, Presentation, Browser

logger = logging.getLogger(__name__)


@dataclass
class WebBrowser(Browser):
    """A class that displays a file or URL in a web browser.

    """
    def _get_screen_size(self) -> Size:
        mons: List[Monitor] = si.get_monitors()
        primes: Tuple[Monitor] = tuple(filter(lambda m: m.is_primary, mons))
        mon: Monitor = primes[0] if len(primes) > 0 else mons[0]
        return Size(mon.width, mon.height)

    def _open_url(self, url: str):
        if logger.isEnabledFor(logging.INFO):
            logger.info(f'opening browser at: {url}')
        webbrowser.open(url, autoraise=False)

    def show(self, presentation: Presentation):
        loc: Location
        for loc in presentation.locations:
            self._open_url(loc.url)
