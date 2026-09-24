"""VibeSpace - database layer.

Single-responsibility: talk to SQLite. The Flask server and the AI
engine call the functions defined here. The database file lives at:

    database/vibespace.db   (always inside the project -> portable)
"""

import sqlite3

import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT UNIQUE NOT NULL,
    email         TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role          TEXT NOT NULL DEFAULT 'user',
    created_at    TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS rooms (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    room_code  TEXT UNIQUE NOT NULL,
    name       TEXT NOT NULL,
    owner_id   INTEGER,
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (owner_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS room_members (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id      INTEGER NOT NULL,
    user_id      INTEGER,
    display_name TEXT,
    joined_at    TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (room_id) REFERENCES rooms(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS messages (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id      INTEGER NOT NULL,
    user_id      INTEGER,
    username     TEXT,
    message_type TEXT NOT NULL DEFAULT 'general',
    content      TEXT NOT NULL,
    created_at   TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (room_id) REFERENCES rooms(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS code_versions (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    room_id    INTEGER NOT NULL,
    user_id    INTEGER,
    username   TEXT,
    code       TEXT NOT NULL,
    language   TEXT NOT NULL DEFAULT 'python',
    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (room_id) REFERENCES rooms(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_messages_room ON messages(room_id);
CREATE INDEX IF NOT EXISTS idx_members_room ON room_members(room_id);
CREATE INDEX IF NOT EXISTS idx_versions_room ON code_versions(room_id);
"""


# ---------------------------------------------------------------------------
# Low-level connection helpers
# ---------------------------------------------------------------------------
def connect():
    """Open a connection to the SQLite database and return it."""
    conn = sqlite3.connect(config.db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create the tables if they do not exist yet (safe to run every start)."""
    conn = connect()
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------
def create_user(username, email, password_hash, role="user"):
    conn = connect()
    try:
        conn.execute(
            "INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)",
            (username, email, password_hash, role),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def get_user_by_username(username):
    conn = connect()
    try:
        row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_user_by_id(user_id):
    conn = connect()
    try:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_users_safe():
    """Safe user list for the admin dashboard (no password fields)."""
    conn = connect()
    try:
        rows = conn.execute(
            "SELECT id, username, email, role, created_at FROM users ORDER BY id"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def count_users():
    conn = connect()
    try:
        return conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Rooms
# ---------------------------------------------------------------------------
def create_room(room_code, name, owner_id=None):
    conn = connect()
    try:
        conn.execute(
            "INSERT INTO rooms (room_code, name, owner_id) VALUES (?, ?, ?)",
            (room_code, name, owner_id),
        )
        conn.commit()
        room = conn.execute("SELECT * FROM rooms WHERE room_code = ?", (room_code,)).fetchone()
        return dict(room) if room else None
    finally:
        conn.close()


def get_room_by_code(room_code):
    conn = connect()
    try:
        row = conn.execute("SELECT * FROM rooms WHERE room_code = ?", (room_code,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_room_by_id(room_id):
    conn = connect()
    try:
        row = conn.execute("SELECT * FROM rooms WHERE id = ?", (room_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_rooms_for_user(user_id):
    """Rooms the user owns OR has joined, newest first."""
    conn = connect()
    try:
        rows = conn.execute(
            """
            SELECT DISTINCT r.* FROM rooms r
            LEFT JOIN room_members m ON m.room_id = r.id
            WHERE r.owner_id = ? OR m.user_id = ?
            ORDER BY r.created_at DESC
            """,
            (user_id, user_id),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_all_rooms():
    conn = connect()
    try:
        rows = conn.execute(
            "SELECT r.*, u.username AS owner_name FROM rooms r "
            "LEFT JOIN users u ON u.id = r.owner_id ORDER BY r.created_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def add_room_member(room_id, user_id=None, display_name=None):
    conn = connect()
    try:
        conn.execute(
            "INSERT INTO room_members (room_id, user_id, display_name) VALUES (?, ?, ?)",
            (room_id, user_id, display_name),
        )
        conn.commit()
        return True
    finally:
        conn.close()


def get_room_members(room_id):
    conn = connect()
    try:
        rows = conn.execute(
            "SELECT * FROM room_members WHERE room_id = ? ORDER BY joined_at", (room_id,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def count_rooms():
    conn = connect()
    try:
        return conn.execute("SELECT COUNT(*) AS c FROM rooms").fetchone()["c"]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Messages (chat)
# ---------------------------------------------------------------------------
def add_message(room_id, user_id, username, message_type, content):
    conn = connect()
    try:
        conn.execute(
            "INSERT INTO messages (room_id, user_id, username, message_type, content) "
            "VALUES (?, ?, ?, ?, ?)",
            (room_id, user_id, username, message_type, content),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM messages WHERE id = last_insert_rowid()").fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_messages(room_id, limit=100):
    conn = connect()
    try:
        rows = conn.execute(
            "SELECT * FROM messages WHERE room_id = ? ORDER BY id DESC LIMIT ?",
            (room_id, limit),
        ).fetchall()
        return list(reversed([dict(r) for r in rows]))
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Code versions
# ---------------------------------------------------------------------------
def save_code_version(room_id, user_id, username, code, language):
    conn = connect()
    try:
        conn.execute(
            "INSERT INTO code_versions (room_id, user_id, username, code, language) "
            "VALUES (?, ?, ?, ?, ?)",
            (room_id, user_id, username, code, language),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM code_versions WHERE id = last_insert_rowid()").fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_versions(room_id):
    conn = connect()
    try:
        rows = conn.execute(
            "SELECT * FROM code_versions WHERE room_id = ? ORDER BY id DESC", (room_id,)
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_version_by_id(version_id):
    conn = connect()
    try:
        row = conn.execute("SELECT * FROM code_versions WHERE id = ?", (version_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_latest_version(room_id):
    """The most recent saved code snapshot for a room (or None)."""
    conn = connect()
    try:
        row = conn.execute(
            "SELECT * FROM code_versions WHERE room_id = ? ORDER BY id DESC LIMIT 1",
            (room_id,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def is_room_member(room_id, user_id):
    conn = connect()
    try:
        row = conn.execute(
            "SELECT id FROM room_members WHERE room_id = ? AND user_id = ?",
            (room_id, user_id),
        ).fetchone()
        return row is not None
    finally:
        conn.close()


def count_messages():
    conn = connect()
    try:
        return conn.execute("SELECT COUNT(*) AS c FROM messages").fetchone()["c"]
    finally:
        conn.close()


def count_versions():
    conn = connect()
    try:
        return conn.execute("SELECT COUNT(*) AS c FROM code_versions").fetchone()["c"]
    finally:
        conn.close()