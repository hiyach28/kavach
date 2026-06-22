from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import DistrictStatsResponse, DistrictSummaryResponse, DistrictStatSchema, DistrictSummaryData
from app.models import DistrictWeeklyStat, District, Case

from typing import Optional

router = APIRouter()

@router.get("/districts", response_model=DistrictStatsResponse)
def get_districts(fraud_type: Optional[str] = None, db: Session = Depends(get_db)):
    stats = db.query(DistrictWeeklyStat).all()
    res = []
    
    # Optional dynamic calculation if filter is present
    case_counts = {}
    if fraud_type:
        cases = db.query(Case).filter(Case.fraud_type == fraud_type).all()
        for c in cases:
            if c.district:
                case_counts[c.district] = case_counts.get(c.district, 0) + 1

    for stat in stats:
        # If filtering, only show districts that have cases of this type, and adjust priority
        count = case_counts.get(stat.district_name, 0) if fraud_type else stat.complaint_count
        if fraud_type and count == 0:
            continue

        # Join with District table to get state
        dist_obj = db.query(District).filter(District.name == stat.district_name).first()
        state = dist_obj.state if dist_obj else None
            
        res.append(DistrictStatSchema(
            name=stat.district_name,
            state=state,
            priority_score=(stat.priority_score or 0.0) if not fraud_type else min(100.0, count * 15.0),
            complaint_count=count,
            estimated_loss=stat.estimated_loss if not fraud_type else count * 50000,
            active_campaigns=0,
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
