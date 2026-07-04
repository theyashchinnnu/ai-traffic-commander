from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime


class IncidentCreate(BaseModel):
    description: str = Field(..., min_length=10, max_length=2000)
    location: Optional[str] = Field(None, max_length=200)
    incident_type: Optional[str] = Field(None, max_length=100)


class IncidentResponse(BaseModel):
    id: str
    description: str
    location: Optional[str] = None
    incident_type: Optional[str] = None
    status: str
    results: Optional[Any] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class IncidentListResponse(BaseModel):
    id: str
    description: str
    status: str
    location: Optional[str] = None
    incident_type: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
