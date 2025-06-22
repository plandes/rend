from typing import Union
from zensols.cli import ApplicationFailure
from zensols.rend import BrowserManager, Display, Application
from zensols.rend.darwin import DarwinBrowser
from util import TestApplicationBase


class TestApplication(TestApplicationBase):
    def test_monitor_config(self):
        app: Application = self.app
        browser_manager: BrowserManager = app.browser_manager
        self.assertEqual(['laptop'], browser_manager.display_names)
        display: Display = browser_manager.displays['laptop']
        self.assertEqual('1024 X 760 (laptop)', str(display))

    def test_preview_script(self):
        app: Union[ApplicationFailure, Application] = self.app
        browser_manager: BrowserManager = app.browser_manager
        if isinstance(browser_manager.browser, DarwinBrowser):
            show_script = browser_manager.browser.get_show_script('preview')
            self.assertTrue(len(show_script) > 100)
