import uuid

import pytest
from httpx import AsyncClient

from app.models.file import File
from app.models.note import Note
from app.models.resource import Resource
from app.models.task import Task


class TestSearchAuth:
    @pytest.mark.asyncio
    async def test_search_requires_auth(self, client: AsyncClient, test_workspace):
        response = await client.get(
            f"/api/workspaces/{test_workspace.id}/search/?q=test"
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_search_invalid_workspace(self, client: AsyncClient, auth_headers):
        response = await client.get(
            f"/api/workspaces/{uuid.uuid4()}/search/?q=test",
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_search_cross_user_isolation(
        self, client: AsyncClient, auth_headers, another_user_workspace
    ):
        response = await client.get(
            f"/api/workspaces/{another_user_workspace.id}/search/?q=test",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestSearch:
    @pytest.mark.asyncio
    async def test_search_case_insensitive_partial(
        self, client: AsyncClient, auth_headers, test_workspace, db_session
    ):
        task = Task(
            workspace_id=test_workspace.id,
            title="Project Alpha Review",
            status="To Do",
            priority="Medium",
        )
        note = Note(
            workspace_id=test_workspace.id,
            title="Alpha Notes",
            body="content about alpha",
        )
        resource = Resource(
            workspace_id=test_workspace.id,
            title="Alpha Resource",
            url="https://example.com",
        )
        file = File(
            workspace_id=test_workspace.id,
            filename="alpha-report.txt",
            size=10,
            storage_path="alpha-report.txt",
        )
        db_session.add_all([task, note, resource, file])
        await db_session.commit()

        # Partial, lowercase match against mixed-case titles.
        response = await client.get(
            f"/api/workspaces/{test_workspace.id}/search/?q=alph",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["tasks"]) == 1
        assert len(data["notes"]) == 1
        assert len(data["resources"]) == 1
        assert len(data["files"]) == 1

        # Uppercase query should still match (case-insensitive).
        response = await client.get(
            f"/api/workspaces/{test_workspace.id}/search/?q=ALPHA",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["tasks"]) == 1
        assert len(data["notes"]) == 1

    @pytest.mark.asyncio
    async def test_search_grouped_shape(
        self, client: AsyncClient, auth_headers, test_workspace, db_session
    ):
        # Only a task exists; searching for its unique title should return a single
        # task and empty arrays for the other groups.
        task = Task(
            workspace_id=test_workspace.id,
            title="UniqueTerm123",
            status="To Do",
            priority="Medium",
        )
        db_session.add_all([task, Note(
            workspace_id=test_workspace.id, title="Other", body="x"
        )])
        await db_session.commit()

        response = await client.get(
            f"/api/workspaces/{test_workspace.id}/search/?q=UniqueTerm123",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert set(data.keys()) == {"tasks", "notes", "resources", "files"}
        assert len(data["tasks"]) == 1
        assert data["notes"] == []
        assert data["resources"] == []
        assert data["files"] == []

    @pytest.mark.asyncio
    async def test_search_blank_query_returns_empty(
        self, client: AsyncClient, auth_headers, test_workspace, db_session
    ):
        db_session.add(Task(
            workspace_id=test_workspace.id, title="Hello", status="To Do", priority="Medium"
        ))
        await db_session.commit()

        # A whitespace-only query passes min_length=1 validation but strips to empty.
        response = await client.get(
            f"/api/workspaces/{test_workspace.id}/search/?q=%20",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["tasks"] == []
        assert data["notes"] == []
        assert data["resources"] == []
        assert data["files"] == []

    @pytest.mark.asyncio
    async def test_search_no_matches_returns_empty(
        self, client: AsyncClient, auth_headers, test_workspace, db_session
    ):
        db_session.add(Task(
            workspace_id=test_workspace.id, title="Hello", status="To Do", priority="Medium"
        ))
        await db_session.commit()

        response = await client.get(
            f"/api/workspaces/{test_workspace.id}/search/?q=zzznomatch",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["tasks"] == []
        assert data["notes"] == []
        assert data["resources"] == []
        assert data["files"] == []

    @pytest.mark.asyncio
    async def test_search_required_param(self, client: AsyncClient, auth_headers, test_workspace):
        response = await client.get(
            f"/api/workspaces/{test_workspace.id}/search/",
            headers=auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_search_invalid_pagination(
        self, client: AsyncClient, auth_headers, test_workspace
    ):
        response = await client.get(
            f"/api/workspaces/{test_workspace.id}/search/?q=test&page=0",
            headers=auth_headers,
        )
        assert response.status_code == 422
