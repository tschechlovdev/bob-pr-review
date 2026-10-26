import pytest
import os
import tempfile
from app import app
import models


@pytest.fixture
def client(tmp_path):
    """Create a test client with an isolated temporary database."""
    db_file = tmp_path / "test_todos.db"
    models.DB_PATH = str(db_file)
    models.init_db()

    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


# ---------------------------------------------------------------------------
# GET /api/todos
# ---------------------------------------------------------------------------

class TestGetTodos:
    def test_returns_empty_list_initially(self, client):
        resp = client.get("/api/todos")
        assert resp.status_code == 200
        assert resp.get_json() == []

    def test_returns_all_todos_newest_first(self, client):
        client.post("/api/todos", json={"title": "First"})
        client.post("/api/todos", json={"title": "Second"})

        resp = client.get("/api/todos")
        data = resp.get_json()
        assert len(data) == 2
        assert data[0]["title"] == "Second"
        assert data[1]["title"] == "First"


# ---------------------------------------------------------------------------
# POST /api/todos
# ---------------------------------------------------------------------------

class TestCreateTodo:
    def test_creates_todo_and_returns_201(self, client):
        resp = client.post("/api/todos", json={"title": "Buy milk"})
        assert resp.status_code == 201
        body = resp.get_json()
        assert body["title"] == "Buy milk"
        assert body["completed"] is False
        assert "id" in body
        assert "created_at" in body

    def test_strips_whitespace_from_title(self, client):
        resp = client.post("/api/todos", json={"title": "  Trimmed  "})
        assert resp.status_code == 201
        assert resp.get_json()["title"] == "Trimmed"

    def test_rejects_empty_title(self, client):
        resp = client.post("/api/todos", json={"title": ""})
        assert resp.status_code == 400
        assert "error" in resp.get_json()

    def test_rejects_whitespace_only_title(self, client):
        resp = client.post("/api/todos", json={"title": "   "})
        assert resp.status_code == 400

    def test_rejects_missing_title(self, client):
        resp = client.post("/api/todos", json={})
        assert resp.status_code == 400

    def test_rejects_non_json_body(self, client):
        resp = client.post("/api/todos", data="not json",
                           content_type="text/plain")
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# PUT /api/todos/<id>
# ---------------------------------------------------------------------------

class TestUpdateTodo:
    def _create(self, client, title="Original"):
        return client.post("/api/todos", json={"title": title}).get_json()

    def test_updates_title(self, client):
        todo = self._create(client)
        resp = client.put(f"/api/todos/{todo['id']}", json={"title": "Updated"})
        assert resp.status_code == 200
        assert resp.get_json()["title"] == "Updated"

    def test_toggles_completed(self, client):
        todo = self._create(client)
        resp = client.put(f"/api/todos/{todo['id']}", json={"completed": True})
        assert resp.status_code == 200
        assert resp.get_json()["completed"] is True

    def test_updates_title_and_completed_together(self, client):
        todo = self._create(client)
        resp = client.put(f"/api/todos/{todo['id']}",
                          json={"title": "New", "completed": True})
        body = resp.get_json()
        assert body["title"] == "New"
        assert body["completed"] is True

    def test_returns_404_for_nonexistent_id(self, client):
        resp = client.put("/api/todos/999", json={"title": "x"})
        assert resp.status_code == 404
        assert "error" in resp.get_json()

    def test_rejects_empty_title_on_update(self, client):
        todo = self._create(client)
        resp = client.put(f"/api/todos/{todo['id']}", json={"title": "  "})
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# DELETE /api/todos/<id>
# ---------------------------------------------------------------------------

class TestDeleteTodo:
    def test_deletes_todo_and_returns_204(self, client):
        todo = client.post("/api/todos", json={"title": "To delete"}).get_json()
        resp = client.delete(f"/api/todos/{todo['id']}")
        assert resp.status_code == 204
        assert resp.data == b""

    def test_deleted_todo_no_longer_in_list(self, client):
        todo = client.post("/api/todos", json={"title": "Gone"}).get_json()
        client.delete(f"/api/todos/{todo['id']}")
        ids = [t["id"] for t in client.get("/api/todos").get_json()]
        assert todo["id"] not in ids

    def test_returns_404_for_nonexistent_id(self, client):
        resp = client.delete("/api/todos/999")
        assert resp.status_code == 404
        assert "error" in resp.get_json()


# ---------------------------------------------------------------------------
# Generic 404
# ---------------------------------------------------------------------------

class TestNotFound:
    def test_unknown_route_returns_json_404(self, client):
        resp = client.get("/api/nonexistent")
        assert resp.status_code == 404
        assert resp.get_json() == {"error": "Not found"}


# ---------------------------------------------------------------------------
# Kanban Board Status and Migration Tests
# ---------------------------------------------------------------------------

class TestKanbanStatus:
    def test_get_todos_includes_status(self, client):
        client.post("/api/todos", json={"title": "Status test"})
        resp = client.get("/api/todos")
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data) == 1
        assert "status" in data[0]
        assert data[0]["status"] == "todo"

    def test_create_todo_with_default_status(self, client):
        resp = client.post("/api/todos", json={"title": "Default"})
        assert resp.status_code == 201
        body = resp.get_json()
        assert body["status"] == "todo"
        assert body["completed"] is False

    def test_create_todo_with_explicit_status(self, client):
        resp = client.post("/api/todos", json={"title": "Progress", "status": "in_progress"})
        assert resp.status_code == 201
        body = resp.get_json()
        assert body["status"] == "in_progress"
        assert body["completed"] is False

    def test_create_todo_with_done_status(self, client):
        resp = client.post("/api/todos", json={"title": "Done deal", "status": "done"})
        assert resp.status_code == 201
        body = resp.get_json()
        assert body["status"] == "done"
        assert body["completed"] is True

    def test_create_todo_with_completed_true_syncs_status(self, client):
        resp = client.post("/api/todos", json={"title": "Checkbox Complete", "completed": True})
        assert resp.status_code == 201
        body = resp.get_json()
        assert body["status"] == "done"
        assert body["completed"] is True

    def test_create_todo_with_completed_false_syncs_status(self, client):
        resp = client.post("/api/todos", json={"title": "Checkbox Incomplete", "completed": False})
        assert resp.status_code == 201
        body = resp.get_json()
        assert body["status"] == "todo"
        assert body["completed"] is False

    def test_create_todo_with_invalid_status_rejected(self, client):
        resp = client.post("/api/todos", json={"title": "Bad", "status": "not_a_status"})
        assert resp.status_code == 400
        body = resp.get_json()
        assert body["error"] == "Invalid status"

    def test_update_status_to_in_progress(self, client):
        todo = client.post("/api/todos", json={"title": "Task"}).get_json()
        resp = client.put(f"/api/todos/{todo['id']}", json={"status": "in_progress"})
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["status"] == "in_progress"
        assert body["completed"] is False

    def test_update_status_to_done(self, client):
        todo = client.post("/api/todos", json={"title": "Task"}).get_json()
        resp = client.put(f"/api/todos/{todo['id']}", json={"status": "done"})
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["status"] == "done"
        assert body["completed"] is True

    def test_update_status_to_todo(self, client):
        # Create as done
        todo = client.post("/api/todos", json={"title": "Task", "status": "done"}).get_json()
        assert todo["completed"] is True
        
        resp = client.put(f"/api/todos/{todo['id']}", json={"status": "todo"})
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["status"] == "todo"
        assert body["completed"] is False

    def test_update_completed_true_syncs_status(self, client):
        todo = client.post("/api/todos", json={"title": "Task"}).get_json()
        resp = client.put(f"/api/todos/{todo['id']}", json={"completed": True})
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["status"] == "done"
        assert body["completed"] is True

    def test_update_completed_false_syncs_status(self, client):
        todo = client.post("/api/todos", json={"title": "Task", "status": "done"}).get_json()
        resp = client.put(f"/api/todos/{todo['id']}", json={"completed": False})
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["status"] == "todo"
        assert body["completed"] is False

    def test_update_invalid_status_rejected(self, client):
        todo = client.post("/api/todos", json={"title": "Task"}).get_json()
        resp = client.put(f"/api/todos/{todo['id']}", json={"status": "invalid_val"})
        assert resp.status_code == 400
        body = resp.get_json()
        assert body["error"] == "Invalid status"


def test_database_migration(tmp_path):
    import sqlite3
    db_file = tmp_path / "migration_test.db"
    models.DB_PATH = str(db_file)
    
    # Create the old table structure
    conn = sqlite3.connect(models.DB_PATH)
    conn.execute("""
        CREATE TABLE todos (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            title      TEXT    NOT NULL,
            completed  INTEGER NOT NULL DEFAULT 0,
            created_at TEXT    NOT NULL DEFAULT (datetime('now'))
        )
    """)
    conn.execute("INSERT INTO todos (title, completed) VALUES ('Old incomplete', 0)")
    conn.execute("INSERT INTO todos (title, completed) VALUES ('Old completed', 1)")
    conn.commit()
    conn.close()
    
    # Call init_db to run migration
    models.init_db()
    
    # Verify migration results
    conn = sqlite3.connect(models.DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM todos ORDER BY id ASC").fetchall()
    assert len(rows) == 2
    
    assert rows[0]["title"] == "Old incomplete"
    assert rows[0]["status"] == "todo"
    assert rows[0]["completed"] == 0
    
    assert rows[1]["title"] == "Old completed"
    assert rows[1]["status"] == "done"
    assert rows[1]["completed"] == 1
    
    conn.close()
