import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.folder import Folder
from app.models.workspace import Workspace


@pytest_asyncio.fixture
async def test_folder(db_session: AsyncSession, test_workspace: Workspace) -> Folder:
    folder = Folder(
        workspace_id=test_workspace.id,
        name="Test Folder",
        description="A test folder",
    )
    db_session.add(folder)
    await db_session.commit()
    await db_session.refresh(folder)
    return folder


@pytest_asyncio.fixture
async def another_user_folder(db_session: AsyncSession, another_user_workspace: Workspace) -> Folder:
    folder = Folder(
        workspace_id=another_user_workspace.id,
        name="Another User's Folder",
    )
    db_session.add(folder)
    await db_session.commit()
    await db_session.refresh(folder)
    return folder


@pytest_asyncio.fixture
async def test_subfolder(db_session: AsyncSession, test_folder: Folder) -> Folder:
    subfolder = Folder(
        workspace_id=test_folder.workspace_id,
        parent_id=test_folder.id,
        name="Subfolder",
    )
    db_session.add(subfolder)
    await db_session.commit()
    await db_session.refresh(subfolder)
    return subfolder


class TestFolderCreate:
    @pytest.mark.asyncio
    async def test_create_folder_success(
        self, client: AsyncClient, auth_headers, test_workspace: Workspace
    ):
        response = await client.post(
            f"/api/workspaces/{test_workspace.id}/folders",
            json={"name": "New Folder", "description": "A new folder"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Folder"
        assert data["description"] == "A new folder"
        assert data["workspace_id"] == str(test_workspace.id)
        assert data["parent_id"] is None
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_create_folder_with_parent(
        self, client: AsyncClient, auth_headers, test_workspace: Workspace, test_folder: Folder
    ):
        response = await client.post(
            f"/api/workspaces/{test_workspace.id}/folders",
            json={"name": "Subfolder", "parent_id": str(test_folder.id)},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Subfolder"
        assert data["parent_id"] == str(test_folder.id)

    @pytest.mark.asyncio
    async def test_create_folder_minimal(
        self, client: AsyncClient, auth_headers, test_workspace: Workspace
    ):
        response = await client.post(
            f"/api/workspaces/{test_workspace.id}/folders",
            json={"name": "Minimal Folder"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Minimal Folder"
        assert data["description"] is None
        assert data["parent_id"] is None

    @pytest.mark.asyncio
    async def test_create_folder_requires_auth(self, client: AsyncClient, test_workspace: Workspace):
        response = await client.post(
            f"/api/workspaces/{test_workspace.id}/folders",
            json={"name": "No Auth"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_folder_invalid_workspace(self, client: AsyncClient, auth_headers):
        import uuid
        response = await client.post(
            f"/api/workspaces/{uuid.uuid4()}/folders",
            json={"name": "Folder"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_folder_cross_user_workspace(
        self, client: AsyncClient, auth_headers, another_user_workspace: Workspace
    ):
        response = await client.post(
            f"/api/workspaces/{another_user_workspace.id}/folders",
            json={"name": "Folder"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_create_folder_validation_empty_name(
        self, client: AsyncClient, auth_headers, test_workspace: Workspace
    ):
        response = await client.post(
            f"/api/workspaces/{test_workspace.id}/folders",
            json={"name": ""},
            headers=auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_folder_invalid_parent(
        self, client: AsyncClient, auth_headers, test_workspace: Workspace
    ):
        import uuid
        response = await client.post(
            f"/api/workspaces/{test_workspace.id}/folders",
            json={"name": "Folder", "parent_id": str(uuid.uuid4())},
            headers=auth_headers,
        )
        assert response.status_code == 400


class TestFolderList:
    @pytest.mark.asyncio
    async def test_list_folders_empty(self, client: AsyncClient, auth_headers, test_workspace: Workspace):
        response = await client.get(
            f"/api/workspaces/{test_workspace.id}/folders",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_list_folders_with_data(self, client: AsyncClient, auth_headers, test_folder: Folder):
        response = await client.get(
            f"/api/workspaces/{test_folder.workspace_id}/folders",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["total"] == 1
        assert data["items"][0]["name"] == test_folder.name

    @pytest.mark.asyncio
    async def test_list_folders_filter_by_parent(
        self, client: AsyncClient, auth_headers, test_folder: Folder, test_subfolder: Folder
    ):
        # List root folders (parent_id=None)
        response = await client.get(
            f"/api/workspaces/{test_folder.workspace_id}/folders",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == str(test_folder.id)

        # List subfolders of test_folder
        response = await client.get(
            f"/api/workspaces/{test_folder.workspace_id}/folders?parent_id={test_folder.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == str(test_subfolder.id)


class TestFolderGet:
    @pytest.mark.asyncio
    async def test_get_folder_success(self, client: AsyncClient, auth_headers, test_folder: Folder):
        response = await client.get(
            f"/api/workspaces/{test_folder.workspace_id}/folders/{test_folder.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_folder.id)
        assert data["name"] == test_folder.name
        assert data["description"] == test_folder.description

    @pytest.mark.asyncio
    async def test_get_folder_not_found(self, client: AsyncClient, auth_headers, test_workspace: Workspace):
        import uuid
        response = await client.get(
            f"/api/workspaces/{test_workspace.id}/folders/{uuid.uuid4()}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_folder_cross_user_isolation(
        self, client: AsyncClient, auth_headers, another_user_folder: Folder
    ):
        response = await client.get(
            f"/api/workspaces/{another_user_folder.workspace_id}/folders/{another_user_folder.id}",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestFolderChildren:
    @pytest.mark.asyncio
    async def test_list_child_folders_empty(
        self, client: AsyncClient, auth_headers, test_folder: Folder
    ):
        response = await client.get(
            f"/api/workspaces/{test_folder.workspace_id}/folders/{test_folder.id}/children",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_list_child_folders_with_data(
        self, client: AsyncClient, auth_headers, test_subfolder: Folder
    ):
        response = await client.get(
            f"/api/workspaces/{test_subfolder.workspace_id}/folders/{test_subfolder.parent_id}/children",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["total"] == 1
        assert data["items"][0]["name"] == test_subfolder.name


class TestFolderUpdate:
    @pytest.mark.asyncio
    async def test_update_folder_name(self, client: AsyncClient, auth_headers, test_folder: Folder):
        response = await client.patch(
            f"/api/workspaces/{test_folder.workspace_id}/folders/{test_folder.id}",
            json={"name": "Updated Name"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"

    @pytest.mark.asyncio
    async def test_update_folder_description(self, client: AsyncClient, auth_headers, test_folder: Folder):
        response = await client.patch(
            f"/api/workspaces/{test_folder.workspace_id}/folders/{test_folder.id}",
            json={"description": "Updated description"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Updated description"

    @pytest.mark.asyncio
    async def test_update_folder_parent(
        self, client: AsyncClient, auth_headers, test_folder: Folder, test_subfolder: Folder
    ):
        # Move test_folder under test_subfolder (should fail - descendant)
        response = await client.patch(
            f"/api/workspaces/{test_folder.workspace_id}/folders/{test_folder.id}",
            json={"parent_id": str(test_subfolder.id)},
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "descendant" in response.json().get("detail", "").lower()

    @pytest.mark.asyncio
    async def test_update_folder_move_to_root(
        self, client: AsyncClient, auth_headers, test_subfolder: Folder
    ):
        response = await client.patch(
            f"/api/workspaces/{test_subfolder.workspace_id}/folders/{test_subfolder.id}",
            json={"parent_id": None},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["parent_id"] is None

    @pytest.mark.asyncio
    async def test_update_folder_not_found(self, client: AsyncClient, auth_headers, test_workspace: Workspace):
        import uuid
        response = await client.patch(
            f"/api/workspaces/{test_workspace.id}/folders/{uuid.uuid4()}",
            json={"name": "Updated"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_folder_cross_user_isolation(
        self, client: AsyncClient, auth_headers, another_user_folder: Folder
    ):
        response = await client.patch(
            f"/api/workspaces/{another_user_folder.workspace_id}/folders/{another_user_folder.id}",
            json={"name": "Hacked"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_folder_invalid_parent(
        self, client: AsyncClient, auth_headers, test_workspace: Workspace, test_folder: Folder
    ):
        import uuid
        response = await client.patch(
            f"/api/workspaces/{test_workspace.id}/folders/{test_folder.id}",
            json={"parent_id": str(uuid.uuid4())},
            headers=auth_headers,
        )
        assert response.status_code == 400


class TestFolderDelete:
    @pytest.mark.asyncio
    async def test_delete_folder(self, client: AsyncClient, auth_headers, test_folder: Folder):
        response = await client.delete(
            f"/api/workspaces/{test_folder.workspace_id}/folders/{test_folder.id}",
            headers=auth_headers,
        )
        assert response.status_code == 204

        # Verify it's gone
        response = await client.get(
            f"/api/workspaces/{test_folder.workspace_id}/folders/{test_folder.id}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_folder_cascades_children(
        self, client: AsyncClient, auth_headers, test_folder: Folder, test_subfolder: Folder
    ):
        subfolder_id = test_subfolder.id
        response = await client.delete(
            f"/api/workspaces/{test_folder.workspace_id}/folders/{test_folder.id}",
            headers=auth_headers,
        )
        assert response.status_code == 204

        # Verify child is also gone
        response = await client.get(
            f"/api/workspaces/{test_folder.workspace_id}/folders/{subfolder_id}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_folder_not_found(self, client: AsyncClient, auth_headers, test_workspace: Workspace):
        import uuid
        response = await client.delete(
            f"/api/workspaces/{test_workspace.id}/folders/{uuid.uuid4()}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_folder_cross_user_isolation(
        self, client: AsyncClient, auth_headers, another_user_folder: Folder
    ):
        response = await client.delete(
            f"/api/workspaces/{another_user_folder.workspace_id}/folders/{another_user_folder.id}",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestFolderFileListing:
    @pytest.mark.asyncio
    async def test_list_folder_files_empty(self, client: AsyncClient, auth_headers, test_folder: Folder):
        response = await client.get(
            f"/api/workspaces/{test_folder.workspace_id}/folders/{test_folder.id}/files",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
