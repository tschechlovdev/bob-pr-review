import io

import pytest
from app import app
import collab
import models


@pytest.fixture
def client(tmp_path):
    models.DB_PATH = str(tmp_path / "test_todos.db")
    collab.UPLOAD_DIR = str(tmp_path / "uploads")
    models.init_db()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def make_todo(client, title="Task"):
    return client.post("/api/todos", json={"title": title}).get_json()["id"]


class TestAssignee:
    def test_assign_and_filter(self, client):
        a = make_todo(client, "A")
        b = make_todo(client, "B")
        client.put(f"/api/todos/{a}", json={"assignee": "alice"})
        client.put(f"/api/todos/{b}", json={"assignee": "bob"})

        resp = client.get("/api/todos?assignee=alice")
        assert resp.status_code == 200
        assert [t["title"] for t in resp.get_json()] == ["A"]

    def test_unassign(self, client):
        a = make_todo(client)
        client.put(f"/api/todos/{a}", json={"assignee": "alice"})
        resp = client.put(f"/api/todos/{a}", json={"assignee": ""})
        assert resp.get_json()["assignee"] is None


class TestComments:
    def test_add_and_list(self, client):
        tid = make_todo(client)
        resp = client.post(f"/api/todos/{tid}/comments", json={"body": "Hi", "author": "alice"})
        assert resp.status_code == 201
        listing = client.get(f"/api/todos/{tid}/comments").get_json()
        assert len(listing) == 1
        assert listing[0]["author"] == "alice"

    def test_rejects_empty_body(self, client):
        tid = make_todo(client)
        resp = client.post(f"/api/todos/{tid}/comments", json={"body": "  "})
        assert resp.status_code == 400

    def test_unknown_todo_returns_404(self, client):
        resp = client.post("/api/todos/999/comments", json={"body": "x"})
        assert resp.status_code == 404

    def test_delete_requires_admin_token(self, client):
        tid = make_todo(client)
        cid = client.post(f"/api/todos/{tid}/comments", json={"body": "x"}).get_json()["id"]
        assert client.delete(f"/api/todos/comments/{cid}").status_code == 403
        resp = client.delete(
            f"/api/todos/comments/{cid}", headers={"X-Admin-Token": collab.ADMIN_TOKEN}
        )
        assert resp.status_code == 204


class TestAttachments:
    def test_upload_list_download(self, client):
        tid = make_todo(client)
        resp = client.post(
            f"/api/todos/{tid}/attachments",
            data={"file": (io.BytesIO(b"hello"), "note.txt")},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 201
        assert client.get(f"/api/todos/{tid}/attachments").get_json()[0]["filename"] == "note.txt"
        dl = client.get("/api/todos/attachments/download/note.txt")
        assert dl.status_code == 200
        assert dl.data == b"hello"
        dl.close()

    def test_upload_without_file_returns_400(self, client):
        tid = make_todo(client)
        resp = client.post(f"/api/todos/{tid}/attachments", data={}, content_type="multipart/form-data")
        assert resp.status_code == 400

    def test_download_missing_returns_404(self, client):
        assert client.get("/api/todos/attachments/download/nope.txt").status_code == 404
