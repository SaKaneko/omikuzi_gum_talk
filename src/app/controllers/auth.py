from flask import (
    Blueprint,
    current_app,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    abort,
)
from functools import wraps

bp = Blueprint("auth", __name__)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    # POST
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    if not username or not password:
        return render_template(
            "login.html", error="ユーザー名とパスワードを入力してください"
        )

    repo = current_app.user_repo
    if repo.verify_user(username, password):
        session["username"] = username
        # store roles in session for quick access
        user = repo.get_user(username)
        session["roles"] = user.get("roles", []) if user else []
        return redirect(url_for("topics.index"))

    return render_template("login.html", error="認証に失敗しました")


@bp.route("/logout")
def logout():
    session.pop("username", None)
    session.pop("roles", None)
    return redirect(url_for("topics.index"))


@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    if not username or not password:
        return render_template(
            "register.html", error="ユーザー名とパスワードを入力してください"
        )

    repo = current_app.user_repo
    try:
        repo.create_user(username, password)
    except Exception as e:
        return render_template("register.html", error=f"登録に失敗しました: {e}")

    # auto-login after register
    session["username"] = username
    user = repo.get_user(username)
    session["roles"] = user.get("roles", []) if user else []
    return redirect(url_for("topics.index"))


def require_roles(required_roles):
    def deco(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not session.get("username"):
                return redirect(url_for("auth.login"))
            roles = session.get("roles")
            # ensure roles present in session (fallback to repo lookup)
            if roles is None:
                repo = current_app.user_repo
                user = repo.get_user(session.get("username"))
                roles = user.get("roles", []) if user else []
                session["roles"] = roles
            for r in required_roles:
                if r in roles:
                    return f(*args, **kwargs)
            abort(403)

        return wrapped

    return deco


@bp.route("/admin")
@require_roles(["admin"])
def admin():
    return render_template("admin.html")


__all__ = ["bp"]
