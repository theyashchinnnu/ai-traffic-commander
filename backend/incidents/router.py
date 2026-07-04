import traceback
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.db import get_db
from auth.utils import get_current_user
from auth.models import User
from incidents.models import Incident
from incidents.schemas import IncidentCreate, IncidentResponse, IncidentListResponse

router = APIRouter(prefix="/api/incidents", tags=["Incidents"])


@router.post("/analyze", response_model=IncidentResponse)
async def analyze_incident(
    data: IncidentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit a traffic incident for AI agent analysis."""
    # Create incident record
    incident = Incident(
        description=data.description,
        location=data.location,
        incident_type=data.incident_type,
        status="processing",
        user_id=current_user.id,
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)

    try:
        # Run CrewAI pipeline
        from agents.crew import TrafficCommanderCrew

        crew = TrafficCommanderCrew()
        results = crew.run(
            incident_description=data.description,
            location=data.location or "Unknown",
            incident_type=data.incident_type or "General",
        )

        # Update incident with results
        incident.status = "completed"
        incident.results = results
        db.commit()
        db.refresh(incident)

    except Exception as e:
        print("[ERROR] Incident analysis failed!")
        import traceback
        traceback.print_exc()
        incident.status = "error"
        incident.results = {"error": str(e), "traceback": traceback.format_exc()}
        db.commit()
        db.refresh(incident)

    return incident


@router.get("/history", response_model=list[IncidentListResponse])
async def get_incident_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all incidents for the current user."""
    incidents = (
        db.query(Incident)
        .filter(Incident.user_id == current_user.id)
        .order_by(Incident.created_at.desc())
        .limit(50)
        .all()
    )
    return incidents


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(
    incident_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific incident by ID."""
    incident = (
        db.query(Incident)
        .filter(Incident.id == incident_id, Incident.user_id == current_user.id)
        .first()
    )
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident
