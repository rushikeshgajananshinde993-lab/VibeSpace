"""VibeSpace - main Flask application.

Implements all phases:
  Phase 2  Authentication  (register / login / logout / sessions / roles)
  Phase 3  Dashboard + Rooms
  Phase 4  Monaco Editor (route + API)
  Phase 5  Real-time collaboration (Socket.IO)
  Phase 6  Three chat panels (Socket.IO + DB)
  Phase 7/8/9  Code runner (HTML preview + Python + Java/.NET detection)
  Phase 10/11  Offline AI analyzer + Review page
  Phase 12  Smart templates
  Phase 13  Version history (save / view / restore)
  Phase 14  Admin dashboard
  Phase 15/16  UI + portability (all relative paths, config.py driven)
"""

import os
import secrets
import threading
import time
import uuid

from flask import (
    Flask,
    abort,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_socketio import SocketIO, join_room, leave_room, emit
from werkzeug.security import check_password_hash, generate_password_hash

import ai_engine
import code_runner
import config
import database

app = Flask(
    __name__,
    static_folder=config.STATIC_FOLDER,
    template_folder=config.TEMPLATE_FOLDER,
)

app.config["SECRET_KEY"] = config.secret_key()
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024
app.config["PERMANENT_SESSION_LIFETIME"] = 60 * 60 * 24 * 30  # 30 days, if "remember me"

socketio = SocketIO(app, async_mode="threading", cors_allowed_origins="*")


# ---------------------------------------------------------------------------
# In-memory room state (active code + connected users)
# ---------------------------------------------------------------------------
ROOM_STATE = {}
ROOM_LOCK = threading.Lock()


def room_state(code):
    with ROOM_LOCK:
        if code not in ROOM_STATE:
            room = database.get_room_by_code(code)
            latest = database.get_latest_version(room["id"]) if room else None
            ROOM_STATE[code] = {
                "users": {},
                "code": (latest["code"] if latest else ""),
                "language": (latest["language"] if latest else "python"),
                "v": 0,
            }
        return ROOM_STATE[code]


# ---------------------------------------------------------------------------
# Template helpers
# ---------------------------------------------------------------------------
@app.context_processor
def inject_globals():
    return {
        "app_name": config.APP_NAME,
        "app_tagline": config.APP_TAGLINE,
        "app_version": config.APP_VERSION,
    }


def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return database.get_user_by_id(user_id)


def login_required(fn):
    from functools import wraps

    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login", next=request.path))
        return fn(*args, **kwargs)

    return wrapper


def admin_required(fn):
    from functools import wraps

    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = current_user()
        if not user:
            return redirect(url_for("login", next=request.path))
        if user["role"] != "admin":
            abort(403)
        return fn(*args, **kwargs)

    return wrapper


def make_room_code():
    for _ in range(50):
        code = uuid.uuid4().hex[:6].upper()
        if not database.get_room_by_code(code):
            return code
    return uuid.uuid4().hex[:10].upper()


# ---------------------------------------------------------------------------
# Public routes: home + health
# ---------------------------------------------------------------------------
@app.route("/")
def home():
    return render_template(
        "index.html",
        app_name=config.APP_NAME,
        tagline=config.APP_TAGLINE,
        version=config.APP_VERSION,
    )


@app.route("/health")
def health():
    return jsonify(status="ok", app=config.APP_NAME)


# ---------------------------------------------------------------------------
# Phase 2 - Authentication
# ---------------------------------------------------------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    error = None
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        email = (request.form.get("email") or "").strip()
        password = request.form.get("password") or ""
        confirm = request.form.get("confirm") or ""

        if not username or len(username) < 3 or len(username) > 20:
            error = "Username must be between 3 and 20 characters."
        elif not all(c.isalnum() or c in "_-" for c in username):
            error = "Username can only contain letters, numbers, _ and -."
        elif "@" not in email or "." not in email:
            error = "Please enter a valid email address."
        elif len(password) < 4:
            error = "Password must be at least 4 characters."
        elif password != confirm:
            error = "Passwords do not match."
        elif database.get_user_by_username(username):
            error = "That username is already taken."
        else:
            if database.count_users() == 0:
                role = "admin"  # first registered user becomes the admin
            else:
                role = "user"
            pwd_hash = generate_password_hash(password)
            if database.create_user(username, email, pwd_hash, role):
                user = database.get_user_by_username(username)
                session["user_id"] = user["id"]
                session["username"] = user["username"]
                session["role"] = user["role"]
                return redirect(url_for("dashboard"))
            error = "Something went wrong while creating the account."

    return render_template("register.html", error=error)


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    error = None
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        remember = request.form.get("remember")

        user = database.get_user_by_username(username)
        if not user or not check_password_hash(user["password_hash"], password):
            error = "Invalid username or password."
        else:
            session.permanent = bool(remember)
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            next_url = request.args.get("next")
            return redirect(next_url or url_for("dashboard"))

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


# ---------------------------------------------------------------------------
# Phase 3 - Dashboard + Rooms
# ---------------------------------------------------------------------------
@app.route("/dashboard")
@login_required
def dashboard():
    user = current_user()
    my_rooms = database.get_rooms_for_user(user["id"])
    all_rooms = database.get_all_rooms()
    return render_template(
        "dashboard.html",
        user=user,
        my_rooms=my_rooms,
        all_rooms=all_rooms[:10],
        tool_status=code_runner.tool_status(),
    )


@app.route("/room/create", methods=["POST"])
@login_required
def room_create():
    user = current_user()
    name = (request.form.get("name") or "").strip() or "New Room"
    if len(name) > 60:
        name = name[:60]
    code = make_room_code()
    room = database.create_room(code, name, owner_id=user["id"])
    database.add_room_member(room["id"], user_id=user["id"])
    return redirect(url_for("editor", room_code=room["room_code"]))


@app.route("/join")
@app.route("/join/<room_code>")
@login_required
def join_room_page(room_code=None):
    user = current_user()
    if not room_code:
        room_code = request.args.get("code", "")
    room = database.get_room_by_code(room_code.upper().strip())
    if not room:
        return render_template("dashboard.html", user=user,
                               error="Room not found. Check the code and try again.",
                               my_rooms=database.get_rooms_for_user(user["id"]),
                               all_rooms=database.get_all_rooms()[:10],
                               tool_status=code_runner.tool_status())
    if not database.is_room_member(room["id"], user["id"]):
        database.add_room_member(room["id"], user_id=user["id"])
    return redirect(url_for("editor", room_code=room["room_code"]))


# ---------------------------------------------------------------------------
# Phase 4 - Editor (main collaboration screen)
# ---------------------------------------------------------------------------
@app.route("/room/<room_code>")
@login_required
def editor(room_code):
    user = current_user()
    room = database.get_room_by_code(room_code.upper())
    if not room:
        return "Room not found.", 404
    latest = database.get_latest_version(room["id"])
    versions = database.get_versions(room["id"])[:20]
    members = database.get_room_members(room["id"])
    return render_template(
        "editor.html",
        user=user,
        room=room,
        initial_code=(latest["code"] if latest else ""),
        initial_language=(latest["language"] if latest else "python"),
        versions=versions,
        members=members,
        languages=ai_engine.get_language_list(),
    )


# ---------------------------------------------------------------------------
# Phase 11 - AI Review page
# ---------------------------------------------------------------------------
@app.route("/review/<int:room_id>")
@login_required
def review(room_id):
    user = current_user()
    room = database.get_room_by_id(room_id)
    if not room:
        return "Room not found.", 404
    latest = database.get_latest_version(room["id"])
    report = None
    code_text = ""
    language = "python"
    if latest:
        code_text = latest["code"]
        language = latest["language"]
        report = ai_engine.review_code(code_text, language)
    return render_template(
        "review.html",
        user=user,
        room=room,
        report=report,
        code_text=code_text[:2000],
        language=language,
    )


# ---------------------------------------------------------------------------
# Phase 14 - Admin dashboard
# ---------------------------------------------------------------------------
@app.route("/admin")
@admin_required
def admin():
    users = database.get_users_safe()
    rooms = database.get_all_rooms()
    stats = {
        "users": database.count_users(),
        "rooms": database.count_rooms(),
        "messages": database.count_messages(),
        "versions": database.count_versions(),
    }
    return render_template(
        "admin.html",
        users=users,
        rooms=rooms,
        stats=stats,
        db_path=config.db_path(),
        tool_status=code_runner.tool_status(),
    )


# ---------------------------------------------------------------------------
# JSON / API endpoints
# ---------------------------------------------------------------------------
@app.route("/api/languages")
def api_languages():
    return jsonify(ai_engine.get_language_list())


@app.route("/api/room/<room_code>/members")
@login_required
def api_room_members(room_code):
    room = database.get_room_by_code(room_code.upper())
    if not room:
        return jsonify({"error": "Room not found"}), 404
    members = database.get_room_members(room["id"])
    return jsonify({"members": members})


@app.route("/api/room/<room_code>/versions")
@login_required
def api_versions(room_code):
    room = database.get_room_by_code(room_code.upper())
    if not room:
        return jsonify({"error": "Room not found"}), 404
    return jsonify({"versions": database.get_versions(room["id"])})


@app.route("/api/version/save", methods=["POST"])
@login_required
def api_version_save():
    user = current_user()
    data = request.get_json(silent=True) or {}
    room_code = (data.get("room_code") or "").upper()
    room = database.get_room_by_code(room_code)
    if not room:
        return jsonify({"error": "Room not found"}), 404
    code = data.get("code", "")
    language = data.get("language", "python")
    v = database.save_code_version(room["id"], user["id"], user["username"], code, language)
    return jsonify({"ok": True, "version": v, "versions": database.get_versions(room["id"])[:20]})


@app.route("/api/version/restore", methods=["POST"])
@login_required
def api_version_restore():
    data = request.get_json(silent=True) or {}
    version = database.get_version_by_id(int(data.get("version_id", 0)))
    if not version:
        return jsonify({"error": "Version not found"}), 404
    return jsonify({"ok": True, "code": version["code"], "language": version["language"]})


@app.route("/api/run", methods=["POST"])
def api_run():
    data = request.get_json(silent=True) or {}
    language = data.get("language", "python")
    code = data.get("code", "")
    return jsonify(code_runner.run_code(language, code))


@app.route("/api/template", methods=["POST"])
def api_template():
    data = request.get_json(silent=True) or {}
    language = data.get("language", "python")
    t = ai_engine.TEMPLATES.get(language)
    if not t:
        return jsonify({"error": "Unknown template"}), 404
    return jsonify({"ok": True, "language": language, "code": t["code"]})


@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    data = request.get_json(silent=True) or {}
    language = data.get("language", "python")
    code = data.get("code", "")
    findings = ai_engine.analyze_code(code, language)
    return jsonify({"ok": True, "findings": findings})


@app.route("/api/status")
@login_required
def api_status():
    return jsonify({"status": "ok", "app": config.APP_NAME,
                    "tools": code_runner.tool_status()})


# ---------------------------------------------------------------------------
# Phase 5 + 6 - Real-time collaboration & chat (Socket.IO events)
# ---------------------------------------------------------------------------
@socketio.on("connect")
def handle_connect():
    pass


@socketio.on("disconnect")
def handle_disconnect():
    for code, state in list(ROOM_STATE.items()):
        if request.sid in state["users"]:
            del state["users"][request.sid]
            emit("members_update", {"members": list(state["users"].values())}, room=code)


@socketio.on("room_join")
def handle_room_join(data):
    code = (data.get("code") or "").upper()
    user = data.get("user") or {}
    if not database.get_room_by_code(code):
        emit("room_error", {"msg": "Room not found"})
        return
    join_room(code)
    state = room_state(code)
    state["users"][request.sid] = {
        "sid": request.sid,
        "id": user.get("id"),
        "name": user.get("username") or user.get("name") or "Guest",
        "role": user.get("role", "user"),
    }
    emit("room_joined", {"members": list(state["users"].values()),
                         "code": state["code"],
                         "language": state["language"]})
    emit("members_update", {"members": list(state["users"].values())}, room=code, skip_sid=request.sid)


@socketio.on("room_leave")
def handle_room_leave(data):
    code = (data.get("code") or "").upper()
    leave_room(code)
    if code in ROOM_STATE and request.sid in ROOM_STATE[code]["users"]:
        del ROOM_STATE[code]["users"][request.sid]
        emit("members_update", {"members": list(ROOM_STATE[code]["users"].values())}, room=code)


@socketio.on("code_change")
def handle_code_change(data):
    code = (data.get("code") or "").upper()
    state = room_state(code)
    state["code"] = data.get("content", "")
    state["language"] = data.get("language", state["language"])
    state["v"] += 1
    emit("code_update", {
        "content": state["code"],
        "language": state["language"],
        "v": state["v"],
        "by": data.get("user", {}).get("username", "?")
    }, room=code, skip_sid=request.sid)


@socketio.on("cursor_move")
def handle_cursor(data):
    code = (data.get("code") or "").upper()
    emit("cursor_update", {
        "id": request.sid,
        "name": data.get("name", "?") + "",
        "line": data.get("line"),
        "column": data.get("column")
    }, room=code, skip_sid=request.sid)


@socketio.on("chat_message")
def handle_chat_message(data):
    code = (data.get("code") or "").upper()
    room = database.get_room_by_code(code)
    if not room:
        return
    user = data.get("user", {})
    user_id = user.get("id")
    username = user.get("username") or "Guest"
    msg_type = data.get("type", "general")
    content = data.get("content", "")
    if not content.strip():
        return
    saved = database.add_message(room["id"], user_id, username, msg_type, content)
    emit("chat_new", saved, room=code)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main():
    import argparse

    parser = argparse.ArgumentParser(description="VibeSpace server")
    parser.add_argument("--host", default=os.environ.get("HOST", config.HOST))
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", config.DEFAULT_PORT)))
    args = parser.parse_args()

    database.init_db()

    print("=" * 52)
    print("  %s v%s" % (config.APP_NAME, config.APP_VERSION))
    print("  %s" % config.APP_TAGLINE)
    print("=" * 52)
    print("  Database   : %s" % config.db_path())
    print("  Server     : http://%s:%s" % (args.host, args.port))
    if args.host in ("0.0.0.0", "::"):
        print("  Share this : http://%s:%s/" % (config.lan_ip(), args.port))
        print("              (works on the same network / after port-forwarding)")
    print("  Java       : %s" % code_runner.tool_status()["java"])
    print("  .NET       : %s" % code_runner.tool_status()["dotnet"])
    print("=" * 52)

    socketio.run(app, host=args.host, port=args.port, allow_unsafe_werkzeug=True, debug=False)


if __name__ == "__main__":
    main()