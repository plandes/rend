# Invoke native applications to view files

[![PyPI][pypi-badge]][pypi-link]
[![Python 3.11][python311-badge]][python311-link]
[![Build Status][build-badge]][build-link]

Invoke native applications to view and render data from files.

Features:
- Uses [Dash] to render Excel, CSV and TSV files.
- Render PDF and HTML in the default web browser.

Features on macOS:
- Default web browser used for HTML, [Preview.app] used for PDF files.
- Resize the window and a per display basis.
- Go to a specified page in [Preview.app].
- Multiple file rendering in browser tabs.

The features on macOS are [needed for other operating systems](#contributing).


## Usage

Create a [configuration file] with the dimensions of each of the screens you
work with and where you want [Preview.app] to be displayed.  You can validate
these configurations by having the application echo them back at you:

```bash
$ rend config
```


### Command Line

Invoke the application to show the file and display it:

```bash
$ rend example.pdf
```

See the [configuration file] example.


### From Python

The package is designed to be easy invoke from Python as well (note the
parenthesis needed to make the instance):
```python
from zensols.rend import ApplicationFactory

if (__name__ == '__main__'):
    app = ApplicationFactory().get_instance()
    app('test-resources/sample.pdf')
```

Pandas `DataFrame`s can be rendered using the browser API (note the lack of
parenthesis as it is called as a class method):
```python
from zensols.rend import BrowserManager, ApplicationFactory
import pandas as pd

if (__name__ == '__main__'):
    mng: BrowserManager = ApplicationFactory.get_browser_manager()
    url = 'https://raw.githubusercontent.com/scpike/us-state-county-zip/master/geo-data.csv'
    df = pd.read_csv(url)
    mng.show(df)
```


## Obtaining

The easiest way to install the command line program is via the `pip` installer:
```bash
pip3 install zensols.rend
```

Binaries are also available on [pypi].


## Documentation

See the [full documentation](https://plandes.github.io/rend/index.html).
The [API reference](https://plandes.github.io/rend/api.html) is also
available.


## Contributing

Currently the more advanced features are only available on macOS.  However, the
API is written to easily add other operating systems as plugins.  If you would
like to write one for other operating systems, please contact and/or submit a
pull request.


## Changelog

An extensive changelog is available [here](CHANGELOG.md).


## Community

Please star this repository and let me know how and where you use this API.
Contributions as pull requests, feedback and any input is welcome.


## License

[MIT License](LICENSE.md)

Copyright (c) 2022 - 2025 Paul Landes


<!-- links -->
[pypi]: https://pypi.org/project/zensols.rend/
[pypi-link]: https://pypi.python.org/pypi/zensols.rend
[pypi-badge]: https://img.shields.io/pypi/v/zensols.rend.svg
[python311-badge]: https://img.shields.io/badge/python-3.11-blue.svg
[python311-link]: https://www.python.org/downloads/release/python-3110
[build-badge]: https://github.com/plandes/rend/workflows/CI/badge.svg
[build-link]: https://github.com/plandes/rend/actions

[configuration file]: test-resources/rend.conf
[Dash]: https://plotly.com/dash/
[Preview.app]: https://en.wikipedia.org/wiki/Preview_(macOS)
