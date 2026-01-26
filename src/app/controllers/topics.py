from flask import (
    Blueprint,
    current_app,
    request,
    jsonify,
    render_template,
    abort,
    session,
)

from ..repositories.topic_repo_sqlite import SQLiteTopicRepository
from ..repositories.topic_repo_file import FileTopicRepository
from ..repositories.topic_repo import TopicRepoError
from ..services.omikuji import OmikujiService
from ..utils.markdown import MarkdownRenderer

# 認可デコレータをインポート
from .auth import require_roles, require_login

bp = Blueprint("topics", __name__)


def _repo():
    # Prefer a configured SQLite DB if provided; fall back to filesystem repo.
    db_path = current_app.config.get("TOPICS_DB")
    if db_path:
        return SQLiteTopicRepository(db_path=db_path)
    topics_dir = current_app.config.get("TOPICS_DIR")
    return FileTopicRepository(topics_dir)


@bp.route("/")
def index():
    return render_template("index.html")


@bp.route("/omikuji")
@require_roles(["admin"])
def omikuji():
    service = OmikujiService(_repo())
    tid = service.pick_random_topic()
    # If client prefers HTML, render the omikuji page which will call this endpoint to get the result
    if request.accept_mimetypes.accept_html:
        return render_template("omikuji.html")

    if not tid:
        return jsonify({"error": "no topics"}), 404
    return jsonify({"id": tid})


@bp.route("/topics", methods=["GET"])
def list_topics():
    try:
        topics = _repo().list_topics()
        # Serve HTML page when browser requests HTML; otherwise return JSON list
        if request.accept_mimetypes.accept_html:
            # is_admin フラグをテンプレートに渡す
            is_admin = "admin" in (session.get("roles") or [])
            return render_template("list.html", is_admin=is_admin)
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
    is_admin = "admin" in (session.get("roles") or [])
    return render_template(
        "topic.html", title=t.get("title"), content=content, id=id, is_admin=is_admin
    )


@bp.route("/topics", methods=["POST"])
@require_login
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
@require_login
def post_page():
    # Render the posting page
    return render_template("post.html")


@bp.route("/topics/<id>", methods=["DELETE"])
@require_roles(["admin"])
def delete_topic(id):
    try:
        _repo().delete_topic(id)
        return ("", 204)
    except TopicRepoError:
        abort(404)
