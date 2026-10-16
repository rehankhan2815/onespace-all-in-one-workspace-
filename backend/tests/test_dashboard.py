import uuid

import pytest
from httpx import AsyncClient

from app.models.file import File
from app.models.note import Note
from app.models.resource import Resource
from app.models.task import Task


class TestDashboardAuth:
    @pytest.mark.asyncio
    async def test_dashboard_requires_auth(self, client: AsyncClient, test_workspace):
        response = await client.get(
            f"/api/workspaces/{test_workspace.id}/dashboard/summary"
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_dashboard_invalid_workspace(self, client: AsyncClient, auth_headers):
        response = await client.get(
            f"/api/workspaces/{uuid.uuid4()}/dashboard/summary",
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_dashboard_cross_user_isolation(
        self, client: AsyncClient, auth_headers, another_user_workspace
    ):
        response = await client.get(
            f"/api/workspaces/{another_user_workspace.id}/dashboard/summary",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestDashboardSummary:
    @pytest.mark.asyncio
    async def test_dashboard_counts(
        self, client: AsyncClient, auth_headers, test_workspace, db_session
    ):
        tasks = [
            Task(
                workspace_id=test_workspace.id,
                title="Done Task",
                status="Done",
                priority="Medium",
            ),
            Task(
                workspace_id=test_workspace.id,
                title="Todo Task",
                status="To Do",
                priority="Medium",
            ),
        ]
        notes = [
            Note(workspace_id=test_workspace.id, title=f"Note {i}", body="body")
            for i in range(3)
        ]
        resources = [
            Resource(
                workspace_id=test_workspace.id,
                title=f"Res {i}",
                url="https://example.com",
            )
            for i in range(2)
        ]
        files = [
            File(
                workspace_id=test_workspace.id,
                filename="file.txt",
                size=10,
                storage_path="file.txt",
            )
        ]
        db_session.add_all(tasks + notes + resources + files)
        await db_session.commit()

        response = await client.get(
            f"/api/workspaces/{test_workspace.id}/dashboard/summary",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_tasks"] == 2
        assert data["completed_tasks"] == 1
        assert data["pending_tasks"] == 1
        assert data["total_notes"] == 3
        assert data["total_resources"] == 2
        assert data["total_files"] == 1

    @pytest.mark.asyncio
    async def test_dashboard_empty_workspace(
        self, client: AsyncClient, auth_headers, test_workspace
    ):
        response = await client.get(
            f"/api/workspaces/{test_workspace.id}/dashboard/summary",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_tasks"] == 0
        assert data["completed_tasks"] == 0
        assert data["pending_tasks"] == 0
        assert data["total_notes"] == 0
        assert data["total_resources"] == 0
        assert data["total_files"] == 0

    @pytest.mark.asyncio
    async def test_dashboard_counts_exclude_other_workspaces(
        self,
        client: AsyncClient,
        auth_headers,
        test_workspace,
        another_user_workspace,
        db_session,
    ):
        # Another user's workspace has entities that must NOT appear in our summary.
        other_task = Task(
            workspace_id=another_user_workspace.id,
            title="Other Task",
            status="Done",
            priority="Medium",
        )
        db_session.add(other_task)
        await db_session.commit()

        response = await client.get(
            f"/api/workspaces/{test_workspace.id}/dashboard/summary",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_tasks"] == 0
        assert data["total_notes"] == 0
        assert data["total_resources"] == 0
        assert data["total_files"] == 0
