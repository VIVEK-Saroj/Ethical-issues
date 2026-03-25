from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.dashboard import AlertOut, AlertSummary
from app.services.alerting import get_all_alerts, get_alert_summary

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("/", response_model=list[AlertOut])
def list_alerts(
    store_id: str = Query("store-1"),
    risk_level: str = Query("", max_length=20),
    category: str = Query("", max_length=100),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    alerts = get_all_alerts(db, store_id)
    if risk_level:
        alerts = [a for a in alerts if a.risk_level == risk_level]
    if category:
        alerts = [a for a in alerts if a.category == category]
    return alerts


@router.get("/summary", response_model=AlertSummary)
def alert_summary(
    store_id: str = Query("store-1"),
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    return get_alert_summary(db, store_id)
