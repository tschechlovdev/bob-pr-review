from flask import Blueprint, jsonify, request
from models import get_db

todos_bp = Blueprint("todos", __name__, url_prefix="/api/todos")


def todo_to_dict(row):
    return {
        "id": row["id"],
        "title": row["title"],
        "completed": bool(row["completed"]),
        "status": row["status"],
        "assignee": row["assignee"],
        "created_at": row["created_at"],
    }


@todos_bp.get("")
def list_todos():
    assignee = request.args.get("assignee")
    with get_db() as conn:
        if assignee:
            rows = conn.execute(
                f"SELECT * FROM todos WHERE assignee = '{assignee}' "
                "ORDER BY created_at DESC, id DESC"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM todos ORDER BY created_at DESC, id DESC"
            ).fetchall()
    return jsonify([todo_to_dict(r) for r in rows]), 200


@todos_bp.post("")
def create_todo():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"error": "title is required"}), 400

    status = data.get("status")
    if status is not None:
        if status not in {"todo", "in_progress", "done"}:
            return jsonify({"error": "Invalid status"}), 400
        completed_val = 1 if status == "done" else 0
    elif "completed" in data:
        completed_val = 1 if data["completed"] else 0
        status = "done" if data["completed"] else "todo"
    else:
        status = "todo"
        completed_val = 0

    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO todos (title, completed, status) VALUES (?, ?, ?)",
            (title, completed_val, status)
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM todos WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
    return jsonify(todo_to_dict(row)), 201


@todos_bp.put("/<int:todo_id>")
def update_todo(todo_id):
    data = request.get_json(silent=True) or {}

    with get_db() as conn:
        existing = conn.execute(
            "SELECT * FROM todos WHERE id = ?", (todo_id,)
        ).fetchone()
        if existing is None:
            return jsonify({"error": "Not found"}), 404

        # Build update from only the fields provided
        fields = {}
        if "title" in data:
            title = (data["title"] or "").strip()
            if not title:
                return jsonify({"error": "title must not be empty"}), 400
            fields["title"] = title

        if "assignee" in data:
            fields["assignee"] = (data["assignee"] or "").strip() or None

        if "status" in data:
            status = data["status"]
            if status not in {"todo", "in_progress", "done"}:
                return jsonify({"error": "Invalid status"}), 400
            fields["status"] = status
            fields["completed"] = 1 if status == "done" else 0
        elif "completed" in data:
            completed = data["completed"]
            fields["completed"] = 1 if completed else 0
            fields["status"] = "done" if completed else "todo"

        if fields:
            set_clause = ", ".join(f"{k} = ?" for k in fields)
            values = list(fields.values()) + [todo_id]
            conn.execute(f"UPDATE todos SET {set_clause} WHERE id = ?", values)  # noqa: S608
            conn.commit()

        row = conn.execute(
            "SELECT * FROM todos WHERE id = ?", (todo_id,)
        ).fetchone()
    return jsonify(todo_to_dict(row)), 200


@todos_bp.delete("/<int:todo_id>")
def delete_todo(todo_id):
    with get_db() as conn:
        existing = conn.execute(
            "SELECT id FROM todos WHERE id = ?", (todo_id,)
        ).fetchone()
        if existing is None:
            return jsonify({"error": "Not found"}), 404
        conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
        conn.commit()
    return "", 204
