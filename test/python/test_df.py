import warnings
from pathlib import Path
from dash import html
from screeninfo import ScreenInfoError
from zensols.rend import BrowserManager, Application, Presentation, Location
from zensols.rend.df import (
    DataSourceFrameLayoutFactory, TerminalDashServerLocation
)
from util import TestApplicationBase


class TestDataFrame(TestApplicationBase):
    APP_ARGS = ('-c test-resources/rend.conf --level=err config ' +
                '--override=data_frame_location_transmuter.run_servers=False')

    def test_dash_app(self):
        app: Application = self.app
        mng: BrowserManager = app.browser_manager
        path = Path('test-resources/states.csv')
        pres: Presentation = None
        try:
            pres = mng.to_presentation(path)
            self.assertTrue(isinstance(pres, Presentation))
            self.assertEqual(1, len(pres.locators))
            loc: Location = pres.locators[0]
            self.assertEqual(TerminalDashServerLocation, type(loc))
            self.assertEqual('http://localhost:8050', loc.url)
            lf: DataSourceFrameLayoutFactory = loc.server.layout_factory
            self.assertEqual(DataSourceFrameLayoutFactory, type(lf))
            self.assertEqual(str(path), lf.title)
            root: html.Div = lf.create_layout()
            self.assertEqual(html.Div, type(root))
            should = dict(
                cell_wrap=False,
                column_deletable=True,
                column_filterable=False,
                column_sort=True,
                column_width_px=90,
                data_font_size=12,
                description=(),
                page_size=100,
                row_deletable=False,
                row_height_px=25
            )
            lf_dict = lf.__dict__
            attrs = dict(map(lambda k: (k, lf_dict[k]), should.keys()))
            self.assertEqual(should, attrs)
        except ScreenInfoError:
            warnings.warn('Warning: could not get screen info--skipping')
        finally:
            if pres is not None:
                pres.deallocate()
