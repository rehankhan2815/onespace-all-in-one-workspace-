from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import Activity, ActivityType


async def log_activity(
    db: AsyncSession,
    workspace_id: UUID,
    activity_type: str,
    message: str,
) -> None:
    """Log an activity record.

    This function creates an Activity record but does NOT commit the session.
    The caller is responsible for committing the transaction.
    """
    activity = Activity(
        workspace_id=workspace_id,
        type=activity_type,
        message=message,
    )
    db.add(activity)


async def log_workspace_created(db: AsyncSession, workspace_id: UUID, workspace_name: str) -> None:
    await log_activity(db, workspace_id, ActivityType.WORKSPACE_CREATED, f"Created workspace \"{workspace_name}\"")


async def log_workspace_updated(db: AsyncSession, workspace_id: UUID, workspace_name: str) -> None:
    await log_activity(db, workspace_id, ActivityType.WORKSPACE_UPDATED, f"Updated workspace \"{workspace_name}\"")


async def log_workspace_archived(db: AsyncSession, workspace_id: UUID, workspace_name: str) -> None:
    await log_activity(db, workspace_id, ActivityType.WORKSPACE_ARCHIVED, f"Archived workspace \"{workspace_name}\"")


async def log_task_created(db: AsyncSession, workspace_id: UUID, task_title: str) -> None:
    await log_activity(db, workspace_id, ActivityType.TASK_CREATED, f"Created task \"{task_title}\"")


async def log_task_updated(db: AsyncSession, workspace_id: UUID, task_title: str) -> None:
    await log_activity(db, workspace_id, ActivityType.TASK_UPDATED, f"Updated task \"{task_title}\"")


async def log_task_completed(db: AsyncSession, workspace_id: UUID, task_title: str) -> None:
    await log_activity(db, workspace_id, ActivityType.TASK_COMPLETED, f"Completed task \"{task_title}\"")


async def log_task_deleted(db: AsyncSession, workspace_id: UUID, task_title: str) -> None:
    await log_activity(db, workspace_id, ActivityType.TASK_DELETED, f"Deleted task \"{task_title}\"")


async def log_note_created(db: AsyncSession, workspace_id: UUID, note_title: str) -> None:
    await log_activity(db, workspace_id, ActivityType.NOTE_CREATED, f"Created note \"{note_title}\"")


async def log_note_updated(db: AsyncSession, workspace_id: UUID, note_title: str) -> None:
    await log_activity(db, workspace_id, ActivityType.NOTE_UPDATED, f"Updated note \"{note_title}\"")


async def log_note_deleted(db: AsyncSession, workspace_id: UUID, note_title: str) -> None:
    await log_activity(db, workspace_id, ActivityType.NOTE_DELETED, f"Deleted note \"{note_title}\"")


async def log_resource_added(db: AsyncSession, workspace_id: UUID, resource_title: str) -> None:
    await log_activity(db, workspace_id, ActivityType.RESOURCE_ADDED, f"Added resource \"{resource_title}\"")


async def log_resource_updated(db: AsyncSession, workspace_id: UUID, resource_title: str) -> None:
    await log_activity(db, workspace_id, ActivityType.RESOURCE_UPDATED, f"Updated resource \"{resource_title}\"")


async def log_resource_deleted(db: AsyncSession, workspace_id: UUID, resource_title: str) -> None:
    await log_activity(db, workspace_id, ActivityType.RESOURCE_DELETED, f"Deleted resource \"{resource_title}\"")


async def log_file_uploaded(db: AsyncSession, workspace_id: UUID, filename: str) -> None:
    await log_activity(db, workspace_id, ActivityType.FILE_UPLOADED, f"Uploaded file \"{filename}\"")


async def log_file_deleted(db: AsyncSession, workspace_id: UUID, filename: str) -> None:
    await log_activity(db, workspace_id, ActivityType.FILE_DELETED, f"Deleted file \"{filename}\"")


async def log_folder_created(db: AsyncSession, workspace_id: UUID, folder_name: str) -> None:
    await log_activity(db, workspace_id, ActivityType.FOLDER_CREATED, f"Created folder \"{folder_name}\"")


async def log_folder_updated(db: AsyncSession, workspace_id: UUID, folder_name: str) -> None:
    await log_activity(db, workspace_id, ActivityType.FOLDER_UPDATED, f"Updated folder \"{folder_name}\"")


async def log_folder_deleted(db: AsyncSession, workspace_id: UUID, folder_name: str) -> None:
    await log_activity(db, workspace_id, ActivityType.FOLDER_DELETED, f"Deleted folder \"{folder_name}\"")
