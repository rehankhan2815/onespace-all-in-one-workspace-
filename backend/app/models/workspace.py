import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.activity import Activity
    from app.models.file import File
    from app.models.folder import Folder
    from app.models.note import Note
    from app.models.resource import Resource
    from app.models.task import Task
    from app.models.user import User


class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    owner: Mapped["User"] = relationship("User", back_populates="workspaces", lazy="selectin")
    tasks: Mapped[list["Task"]] = relationship(
        "Task", back_populates="workspace", cascade="all, delete-orphan", lazy="selectin"
    )
    notes: Mapped[list["Note"]] = relationship(
        "Note", back_populates="workspace", cascade="all, delete-orphan", lazy="selectin"
    )
    resources: Mapped[list["Resource"]] = relationship(
        "Resource", back_populates="workspace", cascade="all, delete-orphan", lazy="selectin"
    )
    files: Mapped[list["File"]] = relationship(
        "File", back_populates="workspace", cascade="all, delete-orphan", lazy="selectin"
    )
    folders: Mapped[list["Folder"]] = relationship(
        "Folder", back_populates="workspace", cascade="all, delete-orphan", lazy="selectin"
    )
    activities: Mapped[list["Activity"]] = relationship(
        "Activity", back_populates="workspace", cascade="all, delete-orphan", lazy="selectin"
    )

    __table_args__ = (
        Index("ix_workspaces_owner_archived", "owner_id", "archived"),
        Index("ix_workspaces_owner_updated", "owner_id", "updated_at"),
    )

    def __repr__(self) -> str:
        return f"<Workspace(id={self.id}, name={self.name}, owner_id={self.owner_id})>"
