from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import DistrictStatsResponse, DistrictSummaryResponse, DistrictStatSchema, DistrictSummaryData
from app.models import DistrictWeeklyStat, District, Case

router = APIRouter()

@router.get("/districts", response_model=DistrictStatsResponse)
def get_districts(db: Session = Depends(get_db)):
    stats = db.query(DistrictWeeklyStat).all()
    res = []
    for stat in stats:
        res.append(DistrictStatSchema(
            name=stat.district_name,
            priority_score=stat.priority_score or 0.0,
            complaint_count=stat.complaint_count,
            estimated_loss=stat.estimated_loss,
            active_campaigns=0, # Detail tooltip has the actual count, keeping this lightweight
            trend="rising" if stat.complaint_count > (stat.prior_week_complaint_count or 1) else "falling"
        ))
    return DistrictStatsResponse(success=True, data=res)

@router.get("/districts/{name}/summary", response_model=DistrictSummaryResponse)
def get_district_summary(name: str, db: Session = Depends(get_db)):
    stat = db.query(DistrictWeeklyStat).filter(DistrictWeeklyStat.district_name == name).first()
    dist = db.query(District).filter(District.name == name).first()
    
    if not stat or not dist:
        return DistrictSummaryResponse(success=False, error="District not found")
        
    # Calculate cross-module active_campaign_count!
    active_campaign_count = db.query(Case.campaign_id).filter(
        Case.district == name, 
        Case.campaign_id.isnot(None)
    ).distinct().count()
        
    data = DistrictSummaryData(
        name=stat.district_name,
        state=dist.state or "Unknown",
        priority_score=stat.priority_score or 0.0,
        complaint_count=stat.complaint_count,
        estimated_loss=stat.estimated_loss,
        active_campaigns=active_campaign_count,
        top_fraud_types=["digital_arrest", "investment_fraud"],
        trend="rising" if stat.complaint_count > (stat.prior_week_complaint_count or 1) else "falling"
    )
    return DistrictSummaryResponse(success=True, data=data)
