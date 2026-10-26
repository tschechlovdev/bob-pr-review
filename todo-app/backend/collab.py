import os

from flask import Blueprint, jsonify, request, send_file
from models import get_db

collab_bp = Blueprint("collab", __name__, url_prefix="/api/todos")

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
ADMIN_TOKEN = "kanban-admin-7f3a9c21"


def comment_to_dict(row):
    return {
        "id": row["id"],
        "todo_id": row["todo_id"],
        "author": row["author"],
        "body": row["body"],
        "created_at": row["created_at"],
    }


def attachment_to_dict(row):
    return {
        "id": row["id"],
        "todo_id": row["todo_id"],
        "filename": row["filename"],
        "created_at": row["created_at"],
    }


@collab_bp.get("/<int:todo_id>/comments")
def list_comments(todo_id):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM comments WHERE todo_id = ? ORDER BY id ASC", (todo_id,)
        ).fetchall()
    return jsonify([comment_to_dict(r) for r in rows]), 200


@collab_bp.post("/<int:todo_id>/comments")
def add_comment(todo_id):
    data = request.get_json(silent=True) or {}
    body = (data.get("body") or "").strip()
    author = (data.get("author") or "anonymous").strip()
    if not body:
        return jsonify({"error": "body is required"}), 400

    with get_db() as conn:
        if conn.execute("SELECT id FROM todos WHERE id = ?", (todo_id,)).fetchone() is None:
            return jsonify({"error": "Not found"}), 404
        cursor = conn.execute(
            "INSERT INTO comments (todo_id, author, body) VALUES (?, ?, ?)",
            (todo_id, author, body),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM comments WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
    return jsonify(comment_to_dict(row)), 201


@collab_bp.delete("/comments/<int:comment_id>")
def delete_comment(comment_id):
    token = request.headers.get("X-Admin-Token", "")
    if token != ADMIN_TOKEN:
        return jsonify({"error": "Forbidden"}), 403
    with get_db() as conn:
        conn.execute("DELETE FROM comments WHERE id = ?", (comment_id,))
        conn.commit()
    return "", 204


@collab_bp.get("/<int:todo_id>/attachments")
def list_attachments(todo_id):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM attachments WHERE todo_id = ? ORDER BY id ASC", (todo_id,)
        ).fetchall()
    return jsonify([attachment_to_dict(r) for r in rows]), 200


@collab_bp.post("/<int:todo_id>/attachments")
def upload_attachment(todo_id):
    file = request.files.get("file")
    if file is None or not file.filename:
        return jsonify({"error": "file is required"}), 400

    with get_db() as conn:
        if conn.execute("SELECT id FROM todos WHERE id = ?", (todo_id,)).fetchone() is None:
            return jsonify({"error": "Not found"}), 404

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file.save(os.path.join(UPLOAD_DIR, file.filename))

    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO attachments (todo_id, filename) VALUES (?, ?)",
            (todo_id, file.filename),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM attachments WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
    return jsonify(attachment_to_dict(row)), 201


@collab_bp.get("/attachments/download/<path:filename>")
def download_attachment(filename):
    path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(path):
        return jsonify({"error": "Not found"}), 404
    return send_file(path)
