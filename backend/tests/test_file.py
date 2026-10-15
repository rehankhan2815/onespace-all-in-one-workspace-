from io import BytesIO

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.file import File
from app.models.folder import Folder
from app.models.workspace import Workspace


@pytest_asyncio.fixture
async def test_folder(db_session: AsyncSession, test_workspace: Workspace) -> Folder:
    folder = Folder(
        workspace_id=test_workspace.id,
        name="Test Folder",
    )
    db_session.add(folder)
    await db_session.commit()
    await db_session.refresh(folder)
    return folder


@pytest_asyncio.fixture
async def test_file(db_session: AsyncSession, test_workspace: Workspace) -> File:
    file = File(
        workspace_id=test_workspace.id,
        filename="test.txt",
        size=100,
        storage_path="test.txt",
    )
    db_session.add(file)
    await db_session.commit()
    await db_session.refresh(file)
    return file


@pytest_asyncio.fixture
async def test_file_in_folder(db_session: AsyncSession, test_folder: Folder) -> File:
    file = File(
        workspace_id=test_folder.workspace_id,
        folder_id=test_folder.id,
        filename="folder_file.txt",
        size=200,
        storage_path="folder_file.txt",
    )
    db_session.add(file)
    await db_session.commit()
    await db_session.refresh(file)
    return file


@pytest_asyncio.fixture
async def another_user_file(db_session: AsyncSession, another_user_workspace: Workspace) -> File:
    file = File(
        workspace_id=another_user_workspace.id,
        filename="private.txt",
        size=300,
        storage_path="private.txt",
    )
    db_session.add(file)
    await db_session.commit()
    await db_session.refresh(file)
    return file


class TestFileUpload:
    @pytest.mark.asyncio
    async def test_upload_file_success(
        self, client: AsyncClient, auth_headers, test_workspace: Workspace
    ):
        file_content = b"Hello, World!"
        files = {"file": ("test.txt", BytesIO(file_content), "text/plain")}

        response = await client.post(
            f"/api/workspaces/{test_workspace.id}/files",
            files=files,
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["filename"] == "test.txt"
        assert data["size"] == len(file_content)
        assert data["workspace_id"] == str(test_workspace.id)
        assert data["folder_id"] is None
        assert "id" in data
        assert "upload_date" in data

    @pytest.mark.asyncio
    async def test_upload_file_in_folder(
        self, client: AsyncClient, auth_headers, test_workspace: Workspace, test_folder: Folder
    ):
        file_content = b"In folder"
        files = {"file": ("folder_test.txt", BytesIO(file_content), "text/plain")}

        response = await client.post(
            f"/api/workspaces/{test_workspace.id}/files?folder_id={test_folder.id}",
            files=files,
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["filename"] == "folder_test.txt"
        assert data["folder_id"] == str(test_folder.id)

    @pytest.mark.asyncio
    async def test_upload_file_requires_auth(self, client: AsyncClient, test_workspace: Workspace):
        file_content = b"Test"
        files = {"file": ("test.txt", BytesIO(file_content), "text/plain")}
        response = await client.post(
            f"/api/workspaces/{test_workspace.id}/files",
            files=files,
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_upload_file_invalid_workspace(self, client: AsyncClient, auth_headers):
        import uuid
        file_content = b"Test"
        files = {"file": ("test.txt", BytesIO(file_content), "text/plain")}
        response = await client.post(
            f"/api/workspaces/{uuid.uuid4()}/files",
            files=files,
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_upload_file_cross_user_workspace(
        self, client: AsyncClient, auth_headers, another_user_workspace: Workspace
    ):
        file_content = b"Test"
        files = {"file": ("test.txt", BytesIO(file_content), "text/plain")}
        response = await client.post(
            f"/api/workspaces/{another_user_workspace.id}/files",
            files=files,
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_upload_file_invalid_folder(
        self, client: AsyncClient, auth_headers, test_workspace: Workspace
    ):
        import uuid
        file_content = b"Test"
        files = {"file": ("test.txt", BytesIO(file_content), "text/plain")}
        response = await client.post(
            f"/api/workspaces/{test_workspace.id}/files?folder_id={uuid.uuid4()}",
            files=files,
            headers=auth_headers,
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_upload_file_size_limit(self, client: AsyncClient, auth_headers, test_workspace: Workspace):
        # Create a file larger than the default 50MB limit
        large_content = b"x" * (51 * 1024 * 1024)  # 51 MB
        files = {"file": ("large.txt", BytesIO(large_content), "text/plain")}

        response = await client.post(
            f"/api/workspaces/{test_workspace.id}/files",
            files=files,
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "exceeds maximum" in response.json().get("detail", "").lower()

    @pytest.mark.asyncio
    async def test_upload_file_sanitizes_filename(
        self, client: AsyncClient, auth_headers, test_workspace: Workspace
    ):
        file_content = b"Test"
        files = {"file": ("../../etc/passwd", BytesIO(file_content), "text/plain")}

        response = await client.post(
            f"/api/workspaces/{test_workspace.id}/files",
            files=files,
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        # Filename should be sanitized to just "passwd"
        assert data["filename"] == "passwd"


class TestFileList:
    @pytest.mark.asyncio
    async def test_list_files_empty(self, client: AsyncClient, auth_headers, test_workspace: Workspace):
        response = await client.get(
            f"/api/workspaces/{test_workspace.id}/files",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_list_files_with_data(self, client: AsyncClient, auth_headers, test_file: File):
        response = await client.get(
            f"/api/workspaces/{test_file.workspace_id}/files",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["total"] == 1
        assert data["items"][0]["filename"] == test_file.filename

    @pytest.mark.asyncio
    async def test_list_files_filter_by_folder(
        self, client: AsyncClient, auth_headers, test_file: File, test_file_in_folder: File
    ):
        # List root files (folder_id=None)
        response = await client.get(
            f"/api/workspaces/{test_file.workspace_id}/files",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == str(test_file.id)

        # List files in folder
        response = await client.get(
            f"/api/workspaces/{test_file.workspace_id}/files?folder_id={test_file_in_folder.folder_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == str(test_file_in_folder.id)

    @pytest.mark.asyncio
    async def test_list_files_pagination(
        self, client: AsyncClient, auth_headers, test_workspace: Workspace, db_session: AsyncSession
    ):
        for i in range(5):
            db_session.add(File(
                workspace_id=test_workspace.id,
                filename=f"file_{i}.txt",
                size=100,
                storage_path=f"file_{i}.txt",
            ))
        await db_session.commit()

        response = await client.get(
            f"/api/workspaces/{test_workspace.id}/files?page=1&page_size=2",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert data["total"] == 5


class TestFileGet:
    @pytest.mark.asyncio
    async def test_get_file_success(self, client: AsyncClient, auth_headers, test_file: File):
        response = await client.get(
            f"/api/workspaces/{test_file.workspace_id}/files/{test_file.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_file.id)
        assert data["filename"] == test_file.filename
        assert data["size"] == test_file.size

    @pytest.mark.asyncio
    async def test_get_file_not_found(self, client: AsyncClient, auth_headers, test_workspace: Workspace):
        import uuid
        response = await client.get(
            f"/api/workspaces/{test_workspace.id}/files/{uuid.uuid4()}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_file_cross_user_isolation(
        self, client: AsyncClient, auth_headers, another_user_file: File
    ):
        response = await client.get(
            f"/api/workspaces/{another_user_file.workspace_id}/files/{another_user_file.id}",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestFileDownload:
    @pytest.mark.asyncio
    async def test_download_file_success(
        self, client: AsyncClient, auth_headers, test_workspace: Workspace, db_session: AsyncSession
    ):
        # Create a file with actual storage
        from io import BytesIO

        from app.utils.file_storage import generate_storage_name, save_upload_file

        content = b"Download test content"
        storage_name = generate_storage_name("download_test.txt")
        save_upload_file(BytesIO(content), storage_name)

        file = File(
            workspace_id=test_workspace.id,
            filename="download_test.txt",
            size=len(content),
            storage_path=storage_name,
        )
        db_session.add(file)
        await db_session.commit()
        await db_session.refresh(file)

        response = await client.get(
            f"/api/workspaces/{test_workspace.id}/files/{file.id}/download",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.content == content
        assert response.headers["content-disposition"] == 'attachment; filename="download_test.txt"'

    @pytest.mark.asyncio
    async def test_download_file_not_found(self, client: AsyncClient, auth_headers, test_workspace: Workspace):
        import uuid
        response = await client.get(
            f"/api/workspaces/{test_workspace.id}/files/{uuid.uuid4()}/download",
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_download_file_missing_storage(
        self, client: AsyncClient, auth_headers, test_workspace: Workspace, db_session: AsyncSession
    ):
        # File record exists but storage file is missing
        file = File(
            workspace_id=test_workspace.id,
            filename="missing.txt",
            size=100,
            storage_path="nonexistent.txt",
        )
        db_session.add(file)
        await db_session.commit()
        await db_session.refresh(file)

        response = await client.get(
            f"/api/workspaces/{test_workspace.id}/files/{file.id}/download",
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestFileDelete:
    @pytest.mark.asyncio
    async def test_delete_file(self, client: AsyncClient, auth_headers, test_workspace: Workspace, db_session: AsyncSession):
        # Create a file with actual storage
        from io import BytesIO

        from app.utils.file_storage import generate_storage_name, save_upload_file

        content = b"Delete test content"
        storage_name = generate_storage_name("delete_test.txt")
        save_upload_file(BytesIO(content), storage_name)

        file = File(
            workspace_id=test_workspace.id,
            filename="delete_test.txt",
            size=len(content),
            storage_path=storage_name,
        )
        db_session.add(file)
        await db_session.commit()
        await db_session.refresh(file)

        file_id = file.id
        storage_path = file.storage_path

        response = await client.delete(
            f"/api/workspaces/{test_workspace.id}/files/{file_id}",
            headers=auth_headers,
        )
        assert response.status_code == 204

        # Verify database record is gone
        response = await client.get(
            f"/api/workspaces/{test_workspace.id}/files/{file_id}",
            headers=auth_headers,
        )
        assert response.status_code == 404

        # Verify physical file is deleted
        from app.utils.file_storage import get_storage_path
        assert not get_storage_path(storage_path).exists()

    @pytest.mark.asyncio
    async def test_delete_file_not_found(self, client: AsyncClient, auth_headers, test_workspace: Workspace):
        import uuid
        response = await client.delete(
            f"/api/workspaces/{test_workspace.id}/files/{uuid.uuid4()}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_file_cross_user_isolation(
        self, client: AsyncClient, auth_headers, another_user_file: File
    ):
        response = await client.delete(
            f"/api/workspaces/{another_user_file.workspace_id}/files/{another_user_file.id}",
            headers=auth_headers,
        )
        assert response.status_code == 404
