import warnings
from screeninfo import ScreenInfoError
from zensols.rend import Browser, BrowserManager, Application
from util import TestApplicationBase


class TestBrowser(TestApplicationBase):
    def test_dash_app(self):
        app: Application = self.app
        mng: BrowserManager = app.browser_manager
        browser: Browser = mng.browser
        self.assertTrue(isinstance(browser, Browser))
        try:
            self.assertTrue(browser.screen_size is not None)
        except ScreenInfoError:
            warnings.warn('Warning: could not get screen info--skipping')
