import os
from pathlib import Path

from . import create_app


def _get_default_topics_dir():
    # project root is three parents up from this file: src/app/main.py -> app -> src -> project root
    return str(Path(__file__).resolve().parents[2] / "topics")


def run():
    topics_dir = os.environ.get("TOPICS_DIR", _get_default_topics_dir())
    app = create_app({"TOPICS_DIR": topics_dir})
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
        debug=os.environ.get("FLASK_DEBUG") == "1",
    )


if __name__ == "__main__":
    run()
