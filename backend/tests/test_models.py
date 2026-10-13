import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Activity, File, Note, Resource, Task, User, Workspace


@pytest_asyncio.fixture
async def user(db_session: AsyncSession) -> User:
    user = User(
        name="Test User",
        email="test@example.com",
        password_hash="hashed_password",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def workspace(db_session: AsyncSession, user: User) -> Workspace:
    workspace = Workspace(
        owner_id=user.id,
        name="Test Workspace",
        description="A test workspace",
    )
    db_session.add(workspace)
    await db_session.commit()
    await db_session.refresh(workspace)
    return workspace


class TestUserModel:
    @pytest.mark.asyncio
    async def test_create_user(self, db_session: AsyncSession):
        user = User(
            name="New User",
            email="new@example.com",
            password_hash="hashed",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        assert user.id is not None
        assert user.name == "New User"
        assert user.email == "new@example.com"
        assert user.password_hash == "hashed"
        assert user.created_at is not None

    @pytest.mark.asyncio
    async def test_user_email_unique(self, db_session: AsyncSession, user: User):
        duplicate = User(
            name="Another User",
            email=user.email,
            password_hash="hashed",
        )
        db_session.add(duplicate)
        with pytest.raises(Exception):
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_user_workspaces_relationship(self, db_session: AsyncSession, user: User, workspace: Workspace):
        await db_session.refresh(user, attribute_names=["workspaces"])
        assert len(user.workspaces) == 1
        assert user.workspaces[0].id == workspace.id


class TestWorkspaceModel:
    @pytest.mark.asyncio
    async def test_create_workspace(self, db_session: AsyncSession, user: User):
        workspace = Workspace(
            owner_id=user.id,
            name="My Workspace",
            description="Description",
        )
        db_session.add(workspace)
        await db_session.commit()
        await db_session.refresh(workspace)

        assert workspace.id is not None
        assert workspace.owner_id == user.id
        assert workspace.name == "My Workspace"
        assert workspace.description == "Description"
        assert workspace.archived is False
        assert workspace.created_at is not None
        assert workspace.updated_at is not None

    @pytest.mark.asyncio
    async def test_workspace_archived_default(self, db_session: AsyncSession, user: User):
        workspace = Workspace(owner_id=user.id, name="Test")
        db_session.add(workspace)
        await db_session.commit()
        await db_session.refresh(workspace)
        assert workspace.archived is False

    @pytest.mark.asyncio
    async def test_workspace_cascade_delete(self, db_session: AsyncSession, user: User, workspace: Workspace):
        await db_session.delete(user)
        await db_session.commit()

        result = await db_session.execute(select(Workspace).where(Workspace.id == workspace.id))
        assert result.scalar_one_or_none() is None


class TestTaskModel:
    @pytest.mark.asyncio
    async def test_create_task(self, db_session: AsyncSession, workspace: Workspace):
        task = Task(
            workspace_id=workspace.id,
            title="Test Task",
            description="Task description",
            status="To Do",
            priority="Medium",
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        assert task.id is not None
        assert task.workspace_id == workspace.id
        assert task.title == "Test Task"
        assert task.status == "To Do"
        assert task.priority == "Medium"

    @pytest.mark.asyncio
    async def test_task_defaults(self, db_session: AsyncSession, workspace: Workspace):
        task = Task(workspace_id=workspace.id, title="Minimal Task")
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        assert task.status == "To Do"
        assert task.priority == "Medium"
        assert task.description is None
        assert task.due_date is None

    @pytest.mark.asyncio
    async def test_task_status_enum(self, db_session: AsyncSession, workspace: Workspace):
        for status in ["To Do", "In Progress", "Done"]:
            task = Task(workspace_id=workspace.id, title=f"Task {status}", status=status)
            db_session.add(task)
        await db_session.commit()

        result = await db_session.execute(select(Task).where(Task.workspace_id == workspace.id))
        tasks = result.scalars().all()
        assert len(tasks) == 3
        statuses = {t.status for t in tasks}
        assert statuses == {"To Do", "In Progress", "Done"}

    @pytest.mark.asyncio
    async def test_task_priority_enum(self, db_session: AsyncSession, workspace: Workspace):
        for priority in ["High", "Medium", "Low"]:
            task = Task(workspace_id=workspace.id, title=f"Task {priority}", priority=priority)
            db_session.add(task)
        await db_session.commit()

        result = await db_session.execute(select(Task).where(Task.workspace_id == workspace.id))
        tasks = result.scalars().all()
        priorities = {t.priority for t in tasks}
        assert priorities == {"High", "Medium", "Low"}

    @pytest.mark.asyncio
    async def test_task_cascade_delete(self, db_session: AsyncSession, workspace: Workspace):
        task = Task(workspace_id=workspace.id, title="Test Task")
        db_session.add(task)
        await db_session.commit()
        task_id = task.id

        await db_session.delete(workspace)
        await db_session.commit()

        result = await db_session.execute(select(Task).where(Task.id == task_id))
        assert result.scalar_one_or_none() is None


class TestNoteModel:
    @pytest.mark.asyncio
    async def test_create_note(self, db_session: AsyncSession, workspace: Workspace):
        note = Note(
            workspace_id=workspace.id,
            title="Test Note",
            body="Note body content",
        )
        db_session.add(note)
        await db_session.commit()
        await db_session.refresh(note)

        assert note.id is not None
        assert note.workspace_id == workspace.id
        assert note.title == "Test Note"
        assert note.body == "Note body content"

    @pytest.mark.asyncio
    async def test_note_default_body(self, db_session: AsyncSession, workspace: Workspace):
        note = Note(workspace_id=workspace.id, title="No Body")
        db_session.add(note)
        await db_session.commit()
        await db_session.refresh(note)
        assert note.body == ""

    @pytest.mark.asyncio
    async def test_note_cascade_delete(self, db_session: AsyncSession, workspace: Workspace):
        note = Note(workspace_id=workspace.id, title="Test Note")
        db_session.add(note)
        await db_session.commit()
        note_id = note.id

        await db_session.delete(workspace)
        await db_session.commit()

        result = await db_session.execute(select(Note).where(Note.id == note_id))
        assert result.scalar_one_or_none() is None


class TestResourceModel:
    @pytest.mark.asyncio
    async def test_create_resource(self, db_session: AsyncSession, workspace: Workspace):
        resource = Resource(
            workspace_id=workspace.id,
            title="Test Resource",
            url="https://example.com",
            description="A resource",
        )
        db_session.add(resource)
        await db_session.commit()
        await db_session.refresh(resource)

        assert resource.id is not None
        assert resource.workspace_id == workspace.id
        assert resource.title == "Test Resource"
        assert resource.url == "https://example.com"
        assert resource.description == "A resource"

    @pytest.mark.asyncio
    async def test_resource_cascade_delete(self, db_session: AsyncSession, workspace: Workspace):
        resource = Resource(workspace_id=workspace.id, title="Test", url="https://test.com")
        db_session.add(resource)
        await db_session.commit()
        resource_id = resource.id

        await db_session.delete(workspace)
        await db_session.commit()

        result = await db_session.execute(select(Resource).where(Resource.id == resource_id))
        assert result.scalar_one_or_none() is None


class TestFileModel:
    @pytest.mark.asyncio
    async def test_create_file(self, db_session: AsyncSession, workspace: Workspace):
        file = File(
            workspace_id=workspace.id,
            filename="test.pdf",
            size=1024,
            storage_path="/uploads/test.pdf",
        )
        db_session.add(file)
        await db_session.commit()
        await db_session.refresh(file)

        assert file.id is not None
        assert file.workspace_id == workspace.id
        assert file.filename == "test.pdf"
        assert file.size == 1024
        assert file.storage_path == "/uploads/test.pdf"
        assert file.upload_date is not None

    @pytest.mark.asyncio
    async def test_file_cascade_delete(self, db_session: AsyncSession, workspace: Workspace):
        file = File(workspace_id=workspace.id, filename="test.txt", size=100, storage_path="/test.txt")
        db_session.add(file)
        await db_session.commit()
        file_id = file.id

        await db_session.delete(workspace)
        await db_session.commit()

        result = await db_session.execute(select(File).where(File.id == file_id))
        assert result.scalar_one_or_none() is None


class TestActivityModel:
    @pytest.mark.asyncio
    async def test_create_activity(self, db_session: AsyncSession, workspace: Workspace):
        activity = Activity(
            workspace_id=workspace.id,
            type="task_created",
            message="Created a new task",
        )
        db_session.add(activity)
        await db_session.commit()
        await db_session.refresh(activity)

        assert activity.id is not None
        assert activity.workspace_id == workspace.id
        assert activity.type == "task_created"
        assert activity.message == "Created a new task"
        assert activity.timestamp is not None

    @pytest.mark.asyncio
    async def test_activity_cascade_delete(self, db_session: AsyncSession, workspace: Workspace):
        activity = Activity(workspace_id=workspace.id, type="test", message="Test")
        db_session.add(activity)
        await db_session.commit()
        activity_id = activity.id

        await db_session.delete(workspace)
        await db_session.commit()

        result = await db_session.execute(select(Activity).where(Activity.id == activity_id))
        assert result.scalar_one_or_none() is None


class TestModelRelationships:
    @pytest.mark.asyncio
    async def test_workspace_with_all_relations(self, db_session: AsyncSession, user: User):
        workspace = Workspace(owner_id=user.id, name="Full Workspace")
        db_session.add(workspace)
        await db_session.flush()

        task = Task(workspace_id=workspace.id, title="Task")
        note = Note(workspace_id=workspace.id, title="Note")
        resource = Resource(workspace_id=workspace.id, title="Resource", url="https://example.com")
        file = File(workspace_id=workspace.id, filename="file.txt", size=100, storage_path="/file.txt")
        activity = Activity(workspace_id=workspace.id, type="test", message="Test")

        db_session.add_all([task, note, resource, file, activity])
        await db_session.commit()

        await db_session.refresh(workspace, attribute_names=["tasks", "notes", "resources", "files", "activities"])
        assert len(workspace.tasks) == 1
        assert len(workspace.notes) == 1
        assert len(workspace.resources) == 1
        assert len(workspace.files) == 1
        assert len(workspace.activities) == 1
