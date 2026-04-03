"""Shared Pydantic base schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TimestampSchema(BaseSchema):
    created_at: datetime
    updated_at: datetime


class PaginatedResponse(BaseSchema):
    total: int
    page: int
    page_size: int


class PaginatedItems[T](PaginatedResponse):
    items: list[T]


class HealthResponse(BaseSchema):
    status: str
    version: str
    environment: str


class ErrorResponse(BaseSchema):
    detail: str
    code: str | None = None
