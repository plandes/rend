from pathlib import Path
import unittest
from zensols.showfile import (
    FileNotFoundError, ShowFileError, LocatorType, Location
)


class TestLocation(unittest.TestCase):
    def test_type(self):
        loc = Location('http://example.com')
        loc.validate()
        self.assertEqual(LocatorType.url, loc.type)
        self.assertFalse(loc.is_file_url)
        with self.assertRaisesRegex(ShowFileError, '^Not a path'):
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
