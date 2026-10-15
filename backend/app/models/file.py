import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.folder import Folder
    from app.models.workspace import Workspace


class File(Base):
    __tablename__ = "files"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    folder_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("folders.id", ondelete="SET NULL"), nullable=True, index=True
    )
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    storage_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    upload_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    workspace: Mapped["Workspace"] = relationship("Workspace", back_populates="files", lazy="selectin")
    folder: Mapped["Folder | None"] = relationship("Folder", back_populates="files", lazy="selectin")

    __table_args__ = (
        Index("ix_files_workspace_upload_date", "workspace_id", "upload_date"),
        Index("ix_files_workspace_filename", "workspace_id", "filename"),
        Index("ix_files_workspace_folder", "workspace_id", "folder_id"),
    )

    def __repr__(self) -> str:
        return f"<File(id={self.id}, filename={self.filename})>"
