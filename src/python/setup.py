from pathlib import Path
from zensols.pybuild import SetupUtil

su = SetupUtil(
    setup_path=Path(__file__).parent.absolute(),
    name="zensols.showfile",
    package_names=['zensols', 'resources'],
    # package_data={'': ['*.html', '*.js', '*.css', '*.map', '*.svg']},
    package_data={'': ['*.conf', '*.json', '*.yml', '*.scpt']},
    description='Invoke macOS applications to view files',
    user='plandes',
    project='showfile',
    keywords=['tooling'],
    # has_entry_points=False,
).setup()
