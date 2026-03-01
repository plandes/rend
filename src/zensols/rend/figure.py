"""Figure rendering and transmuter.

"""
from dataclasses import dataclass, field
import logging
import time
from pathlib import Path
from zensols.util.tempfile import tempfile
from zensols.persist import persisted
from zensols.datdesc.figure import Figure
from zensols.datdesc.render import RenderableFactory, Renderable
from . import RenderFileError, LocationType, Location, LocationTransmuter

logger = logging.getLogger(__name__)


@dataclass
class FigureLocation(Location):
    """A location that points to an image file.  This location deletes the image
    when deallocated to clean up after rendering by the
    :class:`.FigureTransmuter`.

    """
    timeout_secs: float = field(default=0)
    """Wait time before the :obj:`source` file is deleted in
    :meth:`deallocate`.

    """
    def __post_init__(self):
        super().__post_init__()
        self._image_file = self.path
        self.coerce_type(LocationType.url)

    def deallocate(self):
        if self.timeout_secs > 0:
            time.sleep(self.timeout_secs)
        if self._image_file.is_file():
            self._image_file.unlink()
        super().deallocate()


@dataclass
class FigureTransmuter(LocationTransmuter):
    """Transmutes to rendered figure images.

    """
    timeout_secs: float = field()
    """Wait time before the :obj:`source` file is deleted in
    :meth:`deallocate`.

    """
    figure_params: str = field()
    """The image format to use when saving plots."""

    @property
    @persisted('_renderable_factory')
    def renderable_factory(self) -> RenderableFactory:
        """Creates instances of :class:`.Renderable` from file paths."""
        from zensols.datdesc import ApplicationFactory
        return ApplicationFactory.get_renderable_factory()

    def transmute(self, location: Location) -> tuple[Location, ...]:
        locs: list[Location] = []
        if location.has_path:
            fac: RenderableFactory = self.renderable_factory
            rends: tuple[Renderable, ...] = tuple(fac(location.path))
            if len(rends) != 1:
                raise RenderFileError(
                    f'Expecting a single renderable figure: {fac.location}')
            rend: Renderable = rends[0]
            fig: Figure
            for fig in rend:
                fig.__dict__.update(self.figure_params)
                with tempfile(file_fmt=fig.path.name, create=True,
                              remove=False) as path:
                    fig.image_dir = path.parent
                    image_file: Path = fig.save()
                    locs.append(FigureLocation(
                        source=image_file,
                        timeout_secs=self.timeout_secs))
        return tuple(locs)
