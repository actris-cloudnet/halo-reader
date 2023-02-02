import logging
import pathlib

import flask

from . import DEFAULT_ROOT, IMAGE_EXT

logging.basicConfig(level=logging.INFO)

app = flask.Flask(
    __name__,
    template_folder=pathlib.Path(__file__).parent.joinpath("templates"),
)
ROOT = DEFAULT_ROOT


def _find_images():
    img_dir = pathlib.Path(ROOT)
    return sorted(img_dir.glob(f"*.{IMAGE_EXT}"))


@app.route("/")
def index():
    image_paths = _find_images()
    image_paths = ["/" + str(p) for p in image_paths]
    return flask.render_template("index.html", image_paths=image_paths)


@app.route(f"/{ROOT}/<path:name>")
def serve_files(name):
    return flask.send_from_directory(
        pathlib.Path(DEFAULT_ROOT).resolve(), name, as_attachment=True
    )


@app.route("/static/favicon.ico")
def favicon():
    return flask.send_from_directory(
        pathlib.Path(app.root_path, "static"),
        "favicon.ico",
        mimetype="image/svg+xml",
    )


def run():
    app.run(debug=True)


if __name__ == "__main__":
    run()
