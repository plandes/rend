import unittest
from zensols.cli import CliHarness
from zensols.showfile import (
    BrowserManager, Display, Application, ApplicationFactory
)


class TestApplication(unittest.TestCase):
    def setUp(self):
        harn: CliHarness = ApplicationFactory.create_harness()
        self.app: Application = harn.get_instance(
            '-c test-resources/showfile.conf --level=err config')
        if self.app is None:
            raise ValueError('Could not create application')

    def test_somedata(self):
        app: Application = self.app
        self.assertEqual(Application, type(app))
        browser_manager: BrowserManager = app.browser_manager
        self.assertEqual(['laptop'], browser_manager.display_names)
        show_script = browser_manager.browser.get_show_script('preview')
        self.assertTrue(len(show_script) > 100)
        display: Display = browser_manager.displays['laptop']
        self.assertEqual('1024 X 760 (laptop)', str(display))
