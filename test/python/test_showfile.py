import unittest
from zensols.cli import CliHarness
from zensols.showfile import (
    ScreenManager, Display,
    Application, ApplicationFactory
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
        smng: ScreenManager = app.smng
        self.assertEqual(['laptop'], smng.display_names)
        self.assertTrue(len(smng.show_preview_script) > 100)
        display: Display = smng.displays['laptop']
        self.assertEqual('1024 X 760 (laptop)', str(display))
