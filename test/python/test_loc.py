from pathlib import Path
import os
import unittest
from zensols.rend import (
    FileNotFoundError, RenderFileError, LocatorType, Location
)


class TestLocation(unittest.TestCase):
    def test_type(self):
        loc = Location('http://example.com')
        loc.validate()
        self.assertEqual(LocatorType.url, loc.type)
        self.assertFalse(loc.is_file_url)
        with self.assertRaisesRegex(RenderFileError, '^Not a path'):
            self.assertEqual(Path('sample.pdf'), loc.path)

        loc = Location('sample.pdf')
        self.assertEqual(LocatorType.file, loc.type)
        self.assertFalse(loc.is_file_url)
        self.assertEqual(Path('sample.pdf'), loc.path)

        loc = Location('test-res/sample.pdf')
        self.assertEqual(LocatorType.file, loc.type)
        self.assertFalse(loc.is_file_url)

        loc = Location('file:///somedir/file.txt')
        self.assertEqual(LocatorType.url, loc.type)
        self.assertTrue(loc.is_file_url)
        self.assertEqual(Path('/somedir/file.txt'), loc.path)

    def test_validate(self):
        loc = Location('test-resources/sample.pdf')
        loc.validate()

        loc = Location('test-resources/does-not-exist.pdf')
        with self.assertRaises(FileNotFoundError):
            loc.validate()

        loc = Location('file:///somedir/file.txt')
        self.assertEqual(LocatorType.url, loc.type)

    def test_coerce(self):
        loc = Location('test-resources/sample.pdf')
        loc.coerce_type(LocatorType.url)
        self.assertEqual(LocatorType.url, loc.type)
        url = f'file://{os.getcwd()}/test-resources/sample.pdf'
        self.assertEqual(url, loc.source)
        self.assertEqual(url, loc.url)

        loc = Location('file:///somedir/file.txt')
        loc.coerce_type(LocatorType.file)
        self.assertEqual(LocatorType.file, loc.type)
        self.assertEqual(Path('/somedir/file.txt'), loc.source)
        self.assertEqual(Path('/somedir/file.txt'), loc.path)
