from pydantic import BaseModel


class DashboardSummaryResponse(BaseModel):
    total_tasks: int
    completed_tasks: int
    pending_tasks: int
    total_notes: int
    total_resources: int
    total_files: int
