from pydantic import BaseModel, Field
from typing import Optional


class TodoBase(BaseModel):
    title: str = Field(..., description="Text/title of the todo item", min_length=1, max_length=255)
    completed: bool = Field(False, description="Whether the todo is completed")


class TodoCreate(TodoBase):
    pass


class TodoUpdate(BaseModel):
    title: Optional[str] = Field(None, description="Updated text/title of the todo item", min_length=1, max_length=255)
    completed: Optional[bool] = Field(None, description="Updated completion status")


class TodoOut(TodoBase):
    id: int = Field(..., description="Unique identifier for the todo item")
    created_at: str = Field(..., description="Creation timestamp (UTC)")
    updated_at: str = Field(..., description="Last update timestamp (UTC)")

    class Config:
        from_attributes = True
