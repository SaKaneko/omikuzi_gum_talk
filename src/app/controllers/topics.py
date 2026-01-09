from flask import Blueprint, current_app, request, jsonify, render_template, abort

from ..repositories.topic_repo import TopicRepository, TopicRepoError
from ..services.omikuji import OmikujiService
from ..utils.markdown import MarkdownRenderer

bp = Blueprint("topics", __name__)


def _repo():
    topics_dir = current_app.config.get("TOPICS_DIR")
    return TopicRepository(topics_dir)


@bp.route("/")
def index():
    return render_template("index.html")


@bp.route("/omikuji")
def omikuji():
    service = OmikujiService(_repo())
    tid = service.pick_random_topic()
    # If client prefers HTML, render the omikuji page which will call this endpoint to get the result
    if request.accept_mimetypes.accept_html:
        return render_template("omikuji.html")

    service = OmikujiService(_repo())
    tid = service.pick_random_topic()
    if not tid:
        return jsonify({"error": "no topics"}), 404
    return jsonify({"id": tid})


@bp.route("/topics", methods=["GET"])
def list_topics():
    try:
        topics = _repo().list_topics()
        # Serve HTML page when browser requests HTML; otherwise return JSON list
        if request.accept_mimetypes.accept_html:
            return render_template("list.html")
        try:
            topics = _repo().list_topics()
            return jsonify(topics)
        except Exception:
            return jsonify({"error": "failed to list topics"}), 500
    except TopicRepoError as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/topics/<id>", methods=["GET"])
def get_topic(id):
    try:
        t = _repo().get_topic(id)
    except TopicRepoError:
        abort(404)
    renderer = MarkdownRenderer()
    content = renderer.render(t.get("body", ""))
    # render a template showing the title and rendered content
    return render_template("topic.html", title=t.get("title"), content=content, id=id)


@bp.route("/topics", methods=["POST"])
def create_topic():
    data = request.get_json() if request.is_json else request.form
    title = data.get("title")
    body = data.get("body")
    try:
        new_id = _repo().create_topic(title, body)
        return jsonify({"id": new_id}), 201
    except TopicRepoError as e:
        return jsonify({"error": str(e)}), 400


@bp.route("/topics/preview", methods=["POST"])
def preview_topic():
    data = request.get_json() if request.is_json else request.form
    body = data.get("body", "")
    renderer = MarkdownRenderer()
    content = renderer.render(body)
    # Return HTML fragment
    return content


@bp.route("/post", methods=["GET"])
def post_page():
    # Render the posting page
    return render_template("post.html")


@bp.route("/topics/<id>", methods=["DELETE"])
def delete_topic(id):
    try:
        _repo().delete_topic(id)
        return ("", 204)
    except TopicRepoError:
        abort(404)
