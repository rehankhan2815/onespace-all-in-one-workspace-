import pytest
import pytest_asyncio
from httpx import AsyncClient

from app.core.security import create_access_token
from app.models.note import Note
from app.models.workspace import Workspace


@pytest_asyncio.fixture
async def test_note(db_session, test_workspace):
    note = Note(
        workspace_id=test_workspace.id,
        title="Test Note",
        body="This is the note body with multiple\nlines of content.",
    )
    db_session.add(note)
    await db_session.commit()
    await db_session.refresh(note)
    return note


@pytest_asyncio.fixture
async def another_user_note(db_session, another_user_workspace):
    note = Note(
        workspace_id=another_user_workspace.id,
        title="Another User's Note",
        body="Private note",
    )
    db_session.add(note)
    await db_session.commit()
    await db_session.refresh(note)
    return note


class TestNoteCreate:
    @pytest.mark.asyncio
    async def test_create_note_success(self, client: AsyncClient, auth_headers, test_workspace):
        response = await client.post(
            f"/api/workspaces/{test_workspace.id}/notes",
            json={
                "title": "New Note",
                "body": "Note body content",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "New Note"
        assert data["body"] == "Note body content"
        assert data["workspace_id"] == str(test_workspace.id)
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_create_note_minimal(self, client: AsyncClient, auth_headers, test_workspace):
        response = await client.post(
            f"/api/workspaces/{test_workspace.id}/notes",
            json={"title": "Minimal Note"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Minimal Note"
        assert data["body"] == ""

    @pytest.mark.asyncio
    async def test_create_note_multiline_body(self, client: AsyncClient, auth_headers, test_workspace):
        body = "Line 1\nLine 2\nLine 3\n\nParagraph 2"
        response = await client.post(
            f"/api/workspaces/{test_workspace.id}/notes",
            json={"title": "Multiline Note", "body": body},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["body"] == body

    @pytest.mark.asyncio
    async def test_create_note_requires_auth(self, client: AsyncClient, test_workspace):
        response = await client.post(
            f"/api/workspaces/{test_workspace.id}/notes",
            json={"title": "No Auth Note"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_note_invalid_workspace(self, client: AsyncClient, auth_headers):
        import uuid
        response = await client.post(
            f"/api/workspaces/{uuid.uuid4()}/notes",
            json={"title": "Note"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_note_cross_user_workspace(
        self, client: AsyncClient, auth_headers, another_user_workspace
    ):
        response = await client.post(
            f"/api/workspaces/{another_user_workspace.id}/notes",
            json={"title": "Note in other's workspace"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_note_validation_empty_title(self, client: AsyncClient, auth_headers, test_workspace):
        response = await client.post(
            f"/api/workspaces/{test_workspace.id}/notes",
            json={"title": "", "body": "test"},
            headers=auth_headers,
        )
        assert response.status_code == 422


class TestNoteList:
    @pytest.mark.asyncio
    async def test_list_notes_empty(self, client: AsyncClient, auth_headers, test_workspace):
        response = await client.get(
            f"/api/workspaces/{test_workspace.id}/notes",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_list_notes_with_data(self, client: AsyncClient, auth_headers, test_note):
        response = await client.get(
            f"/api/workspaces/{test_note.workspace_id}/notes",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["total"] == 1
        assert data["items"][0]["title"] == test_note.title

    @pytest.mark.asyncio
    async def test_list_notes_pagination(self, client: AsyncClient, auth_headers, test_workspace, db_session):
        for i in range(5):
            db_session.add(Note(workspace_id=test_workspace.id, title=f"Note {i}"))
        await db_session.commit()

        response = await client.get(
            f"/api/workspaces/{test_workspace.id}/notes?page=1&page_size=2",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert data["total"] == 5

    @pytest.mark.asyncio
    async def test_list_notes_ordering(self, client: AsyncClient, auth_headers, test_workspace, db_session):
        import asyncio
        for i in range(3):
            db_session.add(Note(workspace_id=test_workspace.id, title=f"Note {i}"))
            await db_session.commit()
            await asyncio.sleep(0.01)

        response = await client.get(
            f"/api/workspaces/{test_workspace.id}/notes",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        assert data["items"][0]["title"] == "Note 2"


class TestNoteGet:
    @pytest.mark.asyncio
    async def test_get_note_success(self, client: AsyncClient, auth_headers, test_note):
        response = await client.get(
            f"/api/workspaces/{test_note.workspace_id}/notes/{test_note.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_note.id)
        assert data["title"] == test_note.title
        assert data["body"] == test_note.body

    @pytest.mark.asyncio
    async def test_get_note_not_found(self, client: AsyncClient, auth_headers, test_workspace):
        import uuid
        response = await client.get(
            f"/api/workspaces/{test_workspace.id}/notes/{uuid.uuid4()}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_note_cross_user_isolation(
        self, client: AsyncClient, auth_headers, another_user_note
    ):
        response = await client.get(
            f"/api/workspaces/{another_user_note.workspace_id}/notes/{another_user_note.id}",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestNoteUpdate:
    @pytest.mark.asyncio
    async def test_update_note_title(self, client: AsyncClient, auth_headers, test_note):
        response = await client.patch(
            f"/api/workspaces/{test_note.workspace_id}/notes/{test_note.id}",
            json={"title": "Updated Title"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["body"] == test_note.body

    @pytest.mark.asyncio
    async def test_update_note_body(self, client: AsyncClient, auth_headers, test_note):
        response = await client.patch(
            f"/api/workspaces/{test_note.workspace_id}/notes/{test_note.id}",
            json={"body": "Updated body content"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["body"] == "Updated body content"
        assert data["title"] == test_note.title

    @pytest.mark.asyncio
    async def test_update_note_partial(self, client: AsyncClient, auth_headers, test_note):
        original_body = test_note.body
        response = await client.patch(
            f"/api/workspaces/{test_note.workspace_id}/notes/{test_note.id}",
            json={"title": "New Title Only"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "New Title Only"
        assert data["body"] == original_body

    @pytest.mark.asyncio
    async def test_update_note_not_found(self, client: AsyncClient, auth_headers, test_workspace):
        import uuid
        response = await client.patch(
            f"/api/workspaces/{test_workspace.id}/notes/{uuid.uuid4()}",
            json={"title": "Updated"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_note_cross_user_isolation(
        self, client: AsyncClient, auth_headers, another_user_note
    ):
        response = await client.patch(
            f"/api/workspaces/{another_user_note.workspace_id}/notes/{another_user_note.id}",
            json={"title": "Hacked"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_note_validation(self, client: AsyncClient, auth_headers, test_note):
        response = await client.patch(
            f"/api/workspaces/{test_note.workspace_id}/notes/{test_note.id}",
            json={"title": ""},
            headers=auth_headers,
        )
        assert response.status_code == 422


class TestNoteDelete:
    @pytest.mark.asyncio
    async def test_delete_note(self, client: AsyncClient, auth_headers, test_note):
        response = await client.delete(
            f"/api/workspaces/{test_note.workspace_id}/notes/{test_note.id}",
            headers=auth_headers,
        )
        assert response.status_code == 204

        # Verify it's gone
        response = await client.get(
            f"/api/workspaces/{test_note.workspace_id}/notes/{test_note.id}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_note_not_found(self, client: AsyncClient, auth_headers, test_workspace):
        import uuid
        response = await client.delete(
            f"/api/workspaces/{test_workspace.id}/notes/{uuid.uuid4()}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_note_cross_user_isolation(
        self, client: AsyncClient, auth_headers, another_user_note
    ):
        response = await client.delete(
            f"/api/workspaces/{another_user_note.workspace_id}/notes/{another_user_note.id}",
            headers=auth_headers,
        )
        assert response.status_code == 404