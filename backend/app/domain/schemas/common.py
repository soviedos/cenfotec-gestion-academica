"""Shared Pydantic base schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, computed_field


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TimestampSchema(BaseSchema):
    created_at: datetime
    updated_at: datetime


class PaginatedResponse(BaseSchema):
    total: int
    page: int
    page_size: int

    @computed_field
    @property
    def total_pages(self) -> int:
        return max(1, -(-self.total // self.page_size))


class PaginatedItems[T](PaginatedResponse):
    items: list[T]


class HealthResponse(BaseSchema):
    status: str
    version: str
    environment: str


class ErrorResponse(BaseSchema):
    detail: str
    code: str | None = None
