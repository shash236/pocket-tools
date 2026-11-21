from fastapi.testclient import TestClient


def test_notes_crud(client: TestClient) -> None:
    created = client.post("/m/notes/api/notes", json={"title": "Hello", "body": "world"})
    assert created.status_code == 201
    note_id = created.json()["id"]

    assert [n["title"] for n in client.get("/m/notes/api/notes").json()] == ["Hello"]
    assert client.delete(f"/m/notes/api/notes/{note_id}").status_code == 204
    assert client.delete(f"/m/notes/api/notes/{note_id}").status_code == 404


def test_rejects_empty_title(client: TestClient) -> None:
    assert client.post("/m/notes/api/notes", json={"title": ""}).status_code == 422
