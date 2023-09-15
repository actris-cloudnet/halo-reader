import pathlib

from matplotlib.figure import Figure

from . import DEFAULT_ROOT, IMAGE_EXT


class Writer:
    def __init__(self, root: str = DEFAULT_ROOT):
        self.root = pathlib.Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def add_figure(self, name: str, fig: Figure) -> None:
        pth = pathlib.Path(self.root, f"{name}.{IMAGE_EXT}")
        fig.savefig(pth, bbox_inches="tight")

    def add_info(self) -> None:
        raise NotImplementedError
