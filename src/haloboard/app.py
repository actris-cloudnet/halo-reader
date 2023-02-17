import argparse
import logging
import pathlib

import flask

from . import DEFAULT_ROOT, IMAGE_EXT

logging.basicConfig(level=logging.INFO)


parser = argparse.ArgumentParser("haloboard")
parser.add_argument(
    "--dir", type=pathlib.Path, default=pathlib.Path(DEFAULT_ROOT)
)
args = parser.parse_args()
app = flask.Flask(
    __name__,
    template_folder=str(pathlib.Path(__file__).parent.joinpath("templates")),
)
ROOT = args.dir


def _find_images() -> list:
    img_dir = pathlib.Path(ROOT)
    return sorted(img_dir.glob(f"*.{IMAGE_EXT}"))


@app.route("/")
def index() -> str:
    image_paths = _find_images()
    image_paths = ["/" + str(p) for p in image_paths]
    return flask.render_template("index.html", image_paths=image_paths)


@app.route(f"/{ROOT}/<path:name>")
def serve_files(name: str) -> flask.wrappers.Response:
    return flask.send_from_directory(
        pathlib.Path(ROOT).resolve(), name, as_attachment=True
    )


@app.route("/static/<path:name>")
def serve_static(name: str) -> flask.wrappers.Response:
    return flask.send_from_directory(
        pathlib.Path(app.root_path, "static"), name
    )


def run() -> None:
    app.run(debug=True)


if __name__ == "__main__":
    run()
