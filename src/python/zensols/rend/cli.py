"""Command line entry point to the application.

"""
__author__ = 'Paul Landes'

from typing import List, Any, Dict, Union
import sys
from zensols.cli import ActionResult, CliHarness
from zensols.cli import ApplicationFactory as CliApplicationFactory
from . import BrowserManager, Application


class ApplicationFactory(CliApplicationFactory):
    def __init__(self, *args, **kwargs):
        kwargs['package_resource'] = 'zensols.rend'
        super().__init__(*args, **kwargs)

    def get_instance(self, args: Union[List[str], str] = None) -> Application:
        if args is None:
            args = 'config'
        return super().get_instance(args)

    @classmethod
    def get_browser_manager(cls, args: Union[List[str], str] = None) -> \
            BrowserManager:
        """Get a new instance of the browser manager."""
        app: Application = cls().get_instance(args)
        return app.browser_manager

    @classmethod
    def render(cls, data: Any):
        """Render ``data`` using :meth:`.BrowserManager.show`."""
        browser_manager = cls.get_browser_manager()
        browser_manager(data)


def main(args: List[str] = sys.argv, **kwargs: Dict[str, Any]) -> ActionResult:
    harness: CliHarness = ApplicationFactory.create_harness(relocate=False)
    harness.invoke(args, **kwargs)
