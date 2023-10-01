"""Classes that render Pandas dataframes.

"""
__author__ = 'Paul Landes'

from typing import (
    Callable, Union, Optional, Iterable, Tuple, Dict, Set, ClassVar
)
from dataclasses import dataclass, field
from abc import abstractmethod, ABCMeta
from pathlib import Path
import logging
import time
import multiprocessing
from queue import Empty
import pandas as pd
import numpy as np
from flask import Flask
import waitress
from dash import Dash, html
from dash.dash_table import DataTable
import dash_bootstrap_components as dbc
from dash import Input, Output
from zensols.config import ConfigFactory
from zensols.persist import Deallocatable
from zensols.datdesc import DataFrameDescriber
from . import RenderFileError, Location, LocationTransmuter


logger = logging.getLogger(__name__)


@dataclass
class DataFrameSource(object, metaclass=ABCMeta):
    """Generates a dataframe.

    """
    def get_name(self) -> str:
        if hasattr(self, '_name'):
            return self._name

    @abstractmethod
    def get_dataframe(self) -> pd.DataFrame:
        """Create or get a cached dataframe."""
        pass


@dataclass
class CachedDataFrameSource(DataFrameSource):
    """Returns :obj:`df` as the dataframe.

    """
    df: pd.DataFrame = field()
    """The cached datagrame to return in meth:`get_dataframe`."""

    def get_dataframe(self) -> pd.DataFrame:
        return self.df


@dataclass
class PathDataFrameSource(DataFrameSource):
    """Reads a dataframe from a file.

    """
    _EXTENSIONS: ClassVar[Set[str]] = frozenset('csv tsv xlsx'.split())
    """Supported file extesions by this source."""

    path: Path = field()
    """The path to either an Excel, TSV, CSV file."""

    sheet_name: Union[int, str] = field(default=0)
    """The sheet number or name if an Excel file."""

    def get_name(self) -> str:
        name: str = super().get_name()
        if name is None:
            name = str(self.path)
        return name

    @staticmethod
    def get_extesion(path: Path) -> str:
        return path.suffix[1:]

    @classmethod
    def is_supported_path(cls, path: Path) -> bool:
        """Return whether the file is supported by this class."""
        return cls.is_supported_extension(cls.get_extesion(path))

    @classmethod
    def is_supported_extension(cls, ext: str) -> bool:
        """Return whether the file extesion ``ext`` is supported by this class.

        """
        return ext in cls._EXTENSIONS

    @classmethod
    def from_path(cls, path: Path) -> Tuple[DataFrameSource]:
        def map_sheet(t: Tuple[str, pd.DataFrame]) -> DataFrameSource:
            src = CachedDataFrameSource(t[1])
            src._name = t[0]
            return src
        ext: str = cls.get_extesion(path)
        if ext == 'xlsx':
            sheets: Dict[str, pd.DataFrame] = pd.read_excel(
                path, sheet_name=None)
            return tuple(map(map_sheet, sheets.items()))
        return (PathDataFrameSource(path),)

    def get_dataframe(self) -> pd.DataFrame:
        """Procure the dataframe from this source."""
        ext: str = self.get_extesion(self.path)
        if not self.is_supported_extension(ext):
            raise RenderFileError(f'Unsupported extension: {ext}')
        fn: Callable = {
            'csv': pd.read_csv,
            'tsv': lambda p: pd.read(p, sept='\t'),
            'xlsx': lambda p: pd.read_excel(p, sheet_name=self.sheet_name),
        }[ext]
        return fn(self.path)


@dataclass
class LayoutFactory(object, metaclass=ABCMeta):
    """A factory class that creates a layout to be used with :class:`dash.Dash`.
    This is designed to be used by :class:`.TerminalDashServer` to render a page
    and then (optionally) quit for single use page rendering

    """
    title: str = field(default='Untitled')
    """The title of the browser frame."""

    description: Tuple[str] = field(default=())
    """The description of the data to use as a toolip over the title."""

    @abstractmethod
    def create_layout(self) -> html.Div:
        """Create the root application ``div`` HTML element component."""
        pass

    def create_terminate_callback(self, dash: Dash) -> Optional[Callable]:
        """Ceate the callback used to stop the Dash server.  If this returns
        ``None``, the server will not stop.

        """
        pass


@dataclass
class DataFrameLayoutFactory(LayoutFactory, metaclass=ABCMeta):
    """Create a layout with a top title and a resizable
    :class:`~dash.dash_table.DataTable`.  The layout optionally creates a
    callback that is used to terminate the :class:`.TerminalDashServer`.

    """
    page_size: int = field(default=100)
    """The max number of rows displayed in the window before paging out."""

    cell_wrap: bool = field(default=False)
    """Whether to wrap text or cut off with elipses."""

    column_deletable: bool = field(default=True)
    """Whether to add a widget to allow column deletion."""

    column_sort: bool = field(default=True)
    """Whether to add a widget to sort columns"""

    column_filterable: bool = field(default=False)
    """Whether to add a widget to filter by column text."""

    column_width_px: int = field(default=90)
    """The minimum width of each column in pixels."""

    row_deletable: bool = field(default=False)
    """Whether rows are deletable"""

    row_height_px: int = field(default=25)
    """The height of each row in the data table."""

    data_font_size: int = field(default=12)
    """The font size of the data in the table."""

    @abstractmethod
    def _get_dataframe(self) -> pd.DataFrame:
        pass

    def _get_column_tooltips(self, df: pd.DataFrame) -> Dict[str, str]:
        return {i: i for i in df.columns}

    def _create_data_table(self) -> DataTable:
        def filter_left_col(dtype) -> bool:
            return not np.issubdtype(dtype, np.number)

        df: pd.DataFrame = self._get_dataframe()
        col_left_aligns = map(lambda c: c[0],
                              filter(lambda c: filter_left_col(c[1]),
                                     zip(df.columns, df.dtypes)))
        if self.cell_wrap:
            style_data = {'whiteSpace': 'normal'}
        else:
            style_data = {'overflow': 'hidden', 'textOverflow': 'ellipsis'}
        return DataTable(
            id='datatable-paging',
            data=df.to_dict('records'),
            page_size=self.page_size,
            columns=[
                {'name': i,
                 'id': i,
                 'deletable': self.column_deletable,
                 'selectable': True}
                for i in df.columns
            ],
            tooltip_header=self._get_column_tooltips(df),
            filter_action='native' if self.column_filterable else 'none',
            sort_action='native' if self.column_sort else 'none',
            sort_mode='multi',
            row_deletable=self.row_deletable,
            fixed_rows={'headers': True, 'data': 0},
            css=[
                # take the relative window width
                {'selector': 'table',
                 'rule': 'width: 100%;'},
                # subtract the title element height from the total viewport
                {'selector': '.dash-spreadsheet.dash-freeze-top, .dash-spreadsheet .dash-virtualized',
                 'rule': 'max-height: calc(100vh - 90px);'},
                # without this, header tooltips have extra space
                {'selector': '.dash-table-tooltip',
                 'rule': 'min-width: unset;'},
                {'selector': '.dash-spreadsheet tr',
                 'rule': f'height: {self.row_height_px}px;'},
            ],
            style_table={
                'overflowY': 'scroll',
                'border': '1px solid grey',
                'height': '100%',
                'maxHeight': '100%',
            },
            style_header={
                'backgroundColor': 'rgb(180, 180, 180)',
                'color': 'black',
                'fontWeight': 'bold',
                'padding': '5px',
            },
            style_cell={
                'fontSize': self.data_font_size,
                'font-family': 'sans-serif',
                'border': '1px solid grey',
                'minWidth':
                '{w}px', 'width': '{w}px', 'maxWidth': '{w}px'.
                format(w=self.column_width_px),
            },
            style_cell_conditional=[{
                'if': {'column_id': c},
                'textAlign': 'left'
            } for c in col_left_aligns],
            style_data={
                'color': 'black',
                'backgroundColor': 'white',
                'maxWidth': '300px',
                'minWidth': '50px',
            } | style_data,
            style_data_conditional=[{
                'if': {'row_index': 'odd'},
                'backgroundColor': 'rgb(230, 230, 230)',
            }])

    def create_terminate_callback(self, dash: Dash) -> Optional[Callable]:
        return dash.callback(
            Output('server-kill-button-container', 'children'),
            Input('server-kill-submit', 'n_clicks'))

    def create_layout(self) -> html.Div:
        return html.Div(
            [
                html.Div(
                    [
                        html.Span(
                            self.title,
                            id="tooltip-target",
                            style={'fontSize': 'x-large',}
                        ),
                    ],
                    style={
                        'height:': '50px',
                        'maxHeight': '50px',
                        'width': '100%',
                        'padding-bottom': '5px',
                        #'border': '1px solid grey',
                    },
                ),
                dbc.Tooltip(
                    *self.description,
                    target='tooltip-target'
                    if len(self.description) > 0 else 'tooltip-target-disable',
                ),
                # create a hidden button that is called when the page renders
                html.Div(
                    [
                        html.Button(id='server-kill-submit', n_clicks=0),
                        html.Div(id='server-kill-button-container',
                                 children='Enter a value and press submit')
                    ],
                    style={'display': 'none'}
                ),
                # create the DataTable component
                self._create_data_table(),
            ],
            style={'fontFamily': 'Sans-Serif',
                   'padding': '5px'})


@dataclass
class DataSourceFrameLayoutFactory(DataFrameLayoutFactory):
    """Uses a :class:`.DataFrameSource` to create the dataframe.

    """
    source: DataFrameSource = field(default=None)
    """The dataframe source used to create the frame for the data."""

    def _get_dataframe(self) -> pd.DataFrame:
        return self.source.get_dataframe()


@dataclass
class DataFrameDescriberLayoutFactory(DataFrameLayoutFactory):
    """A layout that renderes data from a :class:`.DataFrameDescriber`.

    """
    title: str = field(default=None)
    """The title of the browser frame."""

    source: DataFrameDescriber = field(default=None)
    """The data source."""

    def __post_init__(self):
        if self.title is None:
            self.title = self.source.name
        if len(self.description) == 0:
            self.description = (self.source.desc,)

    def _get_dataframe(self) -> pd.DataFrame:
        return self.source.df

    def _get_column_tooltips(self, df: pd.DataFrame) -> Dict[str, str]:
        cols: Dict[str, str] = self.source.asdict()
        return {c: cols.get(c) or c for c in cols.keys()}


@dataclass
class TerminalDashServer(object):
    """A server that takes a single incoming request, renderes the client's
    page, the exists the interpreter.  This server can continue to run to serve
    requests without a terminating callback.  The lifecycle includes:

      1. Create a multiprocessing queue.
      2. Fork a child process ``C`` from parent process ``P``.
      3. ``C`` starts the Flask service, which binds to a port on localhost.
      4. The framework in ``P`` continues to renderer any other queued data.
      5. The client browser creates a single request to render the Dash data.
      6. Once the browser renders, a callback indicates to terminate the server.
      7. After rendering all data, ``P`` waits for the child process via IPC.
      7. The terminate callback in ``C`` sends a queue (IPC) message to ``P``.
      8. Upon receiving this message, the ``P`` terminates ``C``.

    """
    layout_factory: LayoutFactory = field()
    """The layout to use for the page and callback to exit."""

    port: int = field()
    """The port to start the server."""

    host: str = field(default='localhost')
    """The host interface on which to start the host."""

    sleep_secs: float = field(default=1)
    """The time to wait and allow the Dash server to start and the URL available
    for the browser.

    """
    timeout_sec: float = field(default=5)
    """The timeout in seconds to wait for the child to quit before it is
    terminated.

    """
    @property
    def url(self) -> str:
        return f'http://{self.host}:{self.port}'

    def _shutdown_callback(self, n_clicks: int):
        logger.debug('page load complete')
        time.sleep(1)
        self._queue.put(1)

    def _create_flask(self):
        layout_factory: LayoutFactory = self.layout_factory
        self._flask = Flask(__name__)
        dash = Dash(
            __name__,
            server=self._flask,
            external_stylesheets=[dbc.themes.BOOTSTRAP],
        )
        dash.title = layout_factory.title
        term_cb: Optional[Callable] = layout_factory.\
            create_terminate_callback(dash)
        if term_cb is not None:
            term_cb(self._shutdown_callback)
        dash.layout = layout_factory.create_layout()

    def _child_run(self, queue: multiprocessing.Queue):
        """Entry point for the child process from a parent spwan."""
        self._queue = queue
        self._create_flask()
        try:
            waitress.serve(self._flask, host=self.host, port=self.port)
        except OSError as e:
            raise RenderFileError(
                f'Could not start server {self.host}:{self.port}: {e}') from e
        logger.debug('starting flask...')
        self._flask.run()

    def run(self):
        """Start the Dash server."""
        self._par_queue = multiprocessing.Queue()
        self._proc = multiprocessing.Process(
            target=self._child_run,
            args=(self._par_queue,))
        self._proc.start()
        # TODO: this should be moved the BrowserManager for a sleep for all
        # servers in parallel rather than wait for each in series
        time.sleep(self.sleep_secs)

    def wait(self):
        """Wait for child server processes to end and cleanup."""
        logger.debug('waiting child page render')
        try:
            self._par_queue.get(block=True, timeout=self.timeout_sec)
        except Empty:
            logger.warning('killed child process did not respond ' +
                           f'after {self.timeout_sec}s')
        self._proc.terminate()


@dataclass
class TerminalDashServerLocation(Location, Deallocatable):
    """A location started by a :class:`.TerminalDashServer` which waits and
    kills the child process when it is complete during deallocation.

    :see: :meth:`deallocate`

    """
    server: TerminalDashServer = field(default=None)

    def deallocate(self):
        if self.server is not None:
            self.server.wait()
        super().deallocate()


@dataclass
class DataFrameLocationTransmuter(LocationTransmuter):
    """Transmutes spreadsheet like files (Excel, CSV, etc.) to deallocatable
    :class:`.TerminalDashServerLocation` instances that use a Dash server to
    render the data.

    """
    config_factory: ConfigFactory = field()
    """Used to create layout factory instances of
    :class:`.DataFrameLocationTransmuter`.

    """
    terminal_dash_server_name: str = field()
    """The app config section name of the dash server
    :class:`.TerminalDashServer` entry.

    """
    layout_factory_name: str = field()
    """The app config section name of the
    :class:`.DataFrameLocationTransmuter`.

    """
    start_port: int = field(default=8050)
    """The starting port for the Dash server to bind.  This is incremented for
    each use transmutation so avoid collisions.

    """
    run_servers: bool = field(default=True)
    """Whether to start Flask/Dash servers.  This is turned off for some unit
    tests.

    """
    def _get_next_port(self) -> int:
        port: int = self.start_port
        self.start_port += 1
        return port

    def _create(self, loc: Location) -> Iterable[Location]:
        source: DataFrameSource
        for source in PathDataFrameSource.from_path(loc.path):
            layout_factory: DataFrameLocationTransmuter = \
                self.config_factory.new_instance(
                    self.layout_factory_name,
                    title=source.get_name(),
                    source=source)
            server: TerminalDashServer = \
                self.config_factory.new_instance(
                    self.terminal_dash_server_name,
                    layout_factory=layout_factory,
                    port=self._get_next_port())
            if self.run_servers:
                server.run()
            loc = TerminalDashServerLocation(
                source=server.url,
                server=server)
            yield loc

    def transmute(self, location: Location) -> Tuple[Location]:
        if location.has_path:
            path: Path = location.path
            if PathDataFrameSource.is_supported_path(path):
                return tuple(self._create(location))
        return ()
