import uuid
from datetime import UTC, date, datetime
from typing import TYPE_CHECKING, Literal

from sqlalchemy import Date, DateTime, ForeignKey, Index, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.workspace import Workspace


TaskStatus = Literal["To Do", "In Progress", "Done"]
TaskPriority = Literal["High", "Medium", "Low"]


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        SQLEnum("To Do", "In Progress", "Done", name="task_status", native_enum=False),
        default="To Do",
        nullable=False,
        index=True,
    )
    priority: Mapped[str] = mapped_column(
        SQLEnum("High", "Medium", "Low", name="task_priority", native_enum=False),
        default="Medium",
        nullable=False,
    )
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="tasks", lazy="selectin")

    __table_args__ = (
        Index("ix_tasks_workspace_status", "workspace_id", "status"),
        Index("ix_tasks_workspace_priority", "workspace_id", "priority"),
        Index("ix_tasks_workspace_due_date", "workspace_id", "due_date"),
        Index("ix_tasks_workspace_updated", "workspace_id", "updated_at"),
    )

    def __repr__(self) -> str:
        return f"<Task(id={self.id}, title={self.title}, status={self.status})>"
