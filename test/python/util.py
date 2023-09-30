import unittest
from zensols.cli import CliHarness, ApplicationFailure
from zensols.rend import Application, ApplicationFactory


class TestApplicationBase(unittest.TestCase):
    APP_ARGS = '-c test-resources/rend.conf --level=err config'

    def setUp(self):
        harn: CliHarness = ApplicationFactory.create_harness()
        self.app: Application = harn.get_instance(self.APP_ARGS)
        if self.app is None:
            raise ValueError('Could not create application')
        if isinstance(self.app, ApplicationFailure):
            self.app.rethrow()
        self.assertEqual(Application, type(self.app))
