import asyncio
import uuid

import pytest
from httpx import AsyncClient


def _activity_types(response):
    return [item["type"] for item in response.json()]


class TestActivityAuth:
    @pytest.mark.asyncio
    async def test_list_activity_requires_auth(self, client: AsyncClient, test_workspace):
        response = await client.get(f"/api/workspaces/{test_workspace.id}/activity/")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_activity_invalid_workspace(self, client: AsyncClient, auth_headers):
        response = await client.get(
            f"/api/workspaces/{uuid.uuid4()}/activity/",
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_list_activity_cross_user_isolation(
        self, client: AsyncClient, auth_headers, another_user_workspace
    ):
        response = await client.get(
            f"/api/workspaces/{another_user_workspace.id}/activity/",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestActivityList:
    @pytest.mark.asyncio
    async def test_activity_empty_workspace(
        self, client: AsyncClient, auth_headers, test_workspace
    ):
        # test_workspace is created via db_session directly, so no activity exists yet.
        response = await client.get(
            f"/api/workspaces/{test_workspace.id}/activity/",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_activity_returns_all_events_unpaginated(
        self, client: AsyncClient, auth_headers, test_workspace
    ):
        # Creating 5 tasks logs one "task_created" event each. The endpoint now
        # returns the full array (no pagination envelope), so all 5 are present.
        for i in range(5):
            response = await client.post(
                f"/api/workspaces/{test_workspace.id}/tasks",
                json={"title": f"Task {i}", "status": "To Do"},
                headers=auth_headers,
            )
            assert response.status_code == 201

        response = await client.get(
            f"/api/workspaces/{test_workspace.id}/activity/",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert len(response.json()) == 5


class TestActivityEvents:
    @pytest.mark.asyncio
    async def test_workspace_created_event(self, client: AsyncClient, auth_headers):
        response = await client.post(
            "/api/workspaces",
            json={"name": "Event Workspace"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        ws_id = response.json()["id"]

        response = await client.get(
            f"/api/workspaces/{ws_id}/activity/",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert _activity_types(response) == ["workspace_created"]
        assert data[0]["type"] == "workspace_created"

    @pytest.mark.asyncio
    async def test_task_events(self, client: AsyncClient, auth_headers, test_workspace):
        response = await client.post(
            f"/api/workspaces/{test_workspace.id}/tasks",
            json={"title": "Task A", "status": "To Do", "priority": "Medium"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        task_id = response.json()["id"]

        response = await client.patch(
            f"/api/workspaces/{test_workspace.id}/tasks/{task_id}",
            json={"status": "Done"},
            headers=auth_headers,
        )
        assert response.status_code == 200

        response = await client.delete(
            f"/api/workspaces/{test_workspace.id}/tasks/{task_id}",
            headers=auth_headers,
        )
        assert response.status_code == 204

        response = await client.get(
            f"/api/workspaces/{test_workspace.id}/activity/",
            headers=auth_headers,
        )
        types = _activity_types(response)
        assert "task_created" in types
        assert "task_completed" in types
        assert "task_deleted" in types

    @pytest.mark.asyncio
    async def test_note_events(self, client: AsyncClient, auth_headers, test_workspace):
        response = await client.post(
            f"/api/workspaces/{test_workspace.id}/notes",
            json={"title": "Note A", "body": "body"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        note_id = response.json()["id"]

        response = await client.patch(
            f"/api/workspaces/{test_workspace.id}/notes/{note_id}",
            json={"title": "Note A updated"},
            headers=auth_headers,
        )
        assert response.status_code == 200

        response = await client.delete(
            f"/api/workspaces/{test_workspace.id}/notes/{note_id}",
            headers=auth_headers,
        )
        assert response.status_code == 204

        response = await client.get(
            f"/api/workspaces/{test_workspace.id}/activity/",
            headers=auth_headers,
        )
        types = _activity_types(response)
        assert "note_created" in types
        assert "note_updated" in types
        assert "note_deleted" in types

    @pytest.mark.asyncio
    async def test_resource_events(
        self, client: AsyncClient, auth_headers, test_workspace
    ):
        response = await client.post(
            f"/api/workspaces/{test_workspace.id}/resources",
            json={"title": "Res A", "url": "https://example.com"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        resource_id = response.json()["id"]

        response = await client.patch(
            f"/api/workspaces/{test_workspace.id}/resources/{resource_id}",
            json={"description": "updated"},
            headers=auth_headers,
        )
        assert response.status_code == 200

        response = await client.delete(
            f"/api/workspaces/{test_workspace.id}/resources/{resource_id}",
            headers=auth_headers,
        )
        assert response.status_code == 204

        response = await client.get(
            f"/api/workspaces/{test_workspace.id}/activity/",
            headers=auth_headers,
        )
        types = _activity_types(response)
        assert "resource_added" in types
        assert "resource_updated" in types
        assert "resource_deleted" in types

    @pytest.mark.asyncio
    async def test_folder_events(
        self, client: AsyncClient, auth_headers, test_workspace
    ):
        response = await client.post(
            f"/api/workspaces/{test_workspace.id}/folders",
            json={"name": "Folder A"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        folder_id = response.json()["id"]

        response = await client.patch(
            f"/api/workspaces/{test_workspace.id}/folders/{folder_id}",
            json={"name": "Folder A updated"},
            headers=auth_headers,
        )
        assert response.status_code == 200

        response = await client.delete(
            f"/api/workspaces/{test_workspace.id}/folders/{folder_id}",
            headers=auth_headers,
        )
        assert response.status_code == 204

        response = await client.get(
            f"/api/workspaces/{test_workspace.id}/activity/",
            headers=auth_headers,
        )
        types = _activity_types(response)
        assert "folder_created" in types
        assert "folder_updated" in types
        assert "folder_deleted" in types

    @pytest.mark.asyncio
    async def test_file_events(
        self, client: AsyncClient, auth_headers, test_workspace
    ):
        from io import BytesIO

        response = await client.post(
            f"/api/workspaces/{test_workspace.id}/files",
            files={"file": ("f.txt", BytesIO(b"hi"), "text/plain")},
            headers=auth_headers,
        )
        assert response.status_code == 201
        file_id = response.json()["id"]

        response = await client.delete(
            f"/api/workspaces/{test_workspace.id}/files/{file_id}",
            headers=auth_headers,
        )
        assert response.status_code == 204

        response = await client.get(
            f"/api/workspaces/{test_workspace.id}/activity/",
            headers=auth_headers,
        )
        types = _activity_types(response)
        assert "file_uploaded" in types
        assert "file_deleted" in types

    @pytest.mark.asyncio
    async def test_activity_is_newest_first(
        self, client: AsyncClient, auth_headers, test_workspace
    ):
        await client.post(
            f"/api/workspaces/{test_workspace.id}/tasks",
            json={"title": "First", "status": "To Do"},
            headers=auth_headers,
        )
        await asyncio.sleep(0.02)
        await client.post(
            f"/api/workspaces/{test_workspace.id}/tasks",
            json={"title": "Second", "status": "To Do"},
            headers=auth_headers,
        )

        response = await client.get(
            f"/api/workspaces/{test_workspace.id}/activity/",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        timestamps = [item["timestamp"] for item in data]
        # Newest first: timestamps must be non-increasing.
        for i in range(len(timestamps) - 1):
            assert timestamps[i] >= timestamps[i + 1]
        # The newest event is the second task creation.
        assert data[0]["type"] == "task_created"
        assert "Second" in data[0]["message"]
